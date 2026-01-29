"""
Anthropic Model Adapter for OpenAI Agents SDK

This adapter allows using Azure-hosted Claude models with the openai-agents SDK
by implementing the Model interface and translating between formats.
"""

import os
import json
import logging
import uuid
from typing import Any, List, Optional, AsyncIterator
from dataclasses import dataclass

from anthropic import AsyncAnthropic
from agents import Model, ModelResponse, Usage
from agents.items import TResponseInputItem

# Import OpenAI response types for proper format
from openai.types.responses import (
    ResponseOutputMessage,
    ResponseOutputText,
    ResponseFunctionToolCall,
)

log = logging.getLogger("anthropic_adapter")


class AnthropicChatCompletionsModel(Model):
    """
    Adapter to use Anthropic Claude models (including Azure-hosted) 
    with the OpenAI Agents SDK.
    """
    
    def __init__(
        self,
        model: str,
        anthropic_client: AsyncAnthropic,
    ):
        self._model = model
        self._client = anthropic_client
    
    def _convert_tools_to_anthropic(self, tools: List[Any]) -> List[dict]:
        """Convert OpenAI-format tools to Anthropic format."""
        anthropic_tools = []
        for tool in tools:
            if hasattr(tool, 'name') and hasattr(tool, 'params_json_schema'):
                anthropic_tools.append({
                    "name": tool.name,
                    "description": getattr(tool, 'description', tool.name),
                    "input_schema": tool.params_json_schema,
                })
            elif isinstance(tool, dict):
                # Already dict format
                if tool.get("type") == "function":
                    func = tool.get("function", {})
                    anthropic_tools.append({
                        "name": func.get("name"),
                        "description": func.get("description", ""),
                        "input_schema": func.get("parameters", {}),
                    })
        return anthropic_tools
    
    def _convert_messages_to_anthropic(self, input_items: List[TResponseInputItem]) -> tuple[str, List[dict]]:
        """
        Convert OpenAI-format messages to Anthropic format.
        Returns (system_prompt, messages).
        """
        system_prompt = ""
        messages = []
        
        for item in input_items:
            if isinstance(item, dict):
                role = item.get("role", "user")
                content = item.get("content", "")
                
                if role == "system":
                    # Anthropic uses separate system parameter
                    system_prompt += content + "\n"
                elif role == "assistant":
                    # Check for tool calls
                    tool_calls = item.get("tool_calls", [])
                    if tool_calls:
                        # Convert tool calls to Anthropic format
                        content_blocks = []
                        if content:
                            content_blocks.append({"type": "text", "text": content})
                        for tc in tool_calls:
                            content_blocks.append({
                                "type": "tool_use",
                                "id": tc.get("id"),
                                "name": tc.get("function", {}).get("name"),
                                "input": json.loads(tc.get("function", {}).get("arguments", "{}")),
                            })
                        messages.append({"role": "assistant", "content": content_blocks})
                    else:
                        messages.append({"role": "assistant", "content": content})
                elif role == "tool":
                    # Tool result
                    messages.append({
                        "role": "user",
                        "content": [{
                            "type": "tool_result",
                            "tool_use_id": item.get("tool_call_id"),
                            "content": content,
                        }]
                    })
                else:
                    # User message
                    messages.append({"role": "user", "content": content})
            else:
                # Handle non-dict items (like message objects)
                role = getattr(item, 'role', 'user')
                content = getattr(item, 'content', str(item))
                if role == "system":
                    system_prompt += content + "\n"
                else:
                    messages.append({"role": role, "content": content})
        
        # Merge consecutive same-role messages (Anthropic requirement)
        merged = []
        for msg in messages:
            if merged and merged[-1]["role"] == msg["role"]:
                # Merge content
                prev_content = merged[-1]["content"]
                new_content = msg["content"]
                if isinstance(prev_content, str) and isinstance(new_content, str):
                    merged[-1]["content"] = prev_content + "\n" + new_content
                elif isinstance(prev_content, list) and isinstance(new_content, list):
                    merged[-1]["content"].extend(new_content)
                else:
                    # Convert to list format
                    if isinstance(prev_content, str):
                        prev_content = [{"type": "text", "text": prev_content}]
                    if isinstance(new_content, str):
                        new_content = [{"type": "text", "text": new_content}]
                    merged[-1]["content"] = prev_content + new_content
            else:
                merged.append(msg)
        
        return system_prompt.strip(), merged
    
    def _convert_response_to_openai(self, response) -> ModelResponse:
        """Convert Anthropic response to OpenAI Agents SDK format."""
        output_items = []
        
        # Extract text and tool calls from response
        text_parts = []
        tool_calls = []
        
        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                # Create a proper function tool call
                tool_call = ResponseFunctionToolCall(
                    id=block.id,
                    type="function_call",
                    call_id=block.id,
                    name=block.name,
                    arguments=json.dumps(block.input),
                    status="completed",
                )
                tool_calls.append(tool_call)
        
        # If we have text, create a message
        if text_parts:
            text_content = "".join(text_parts)
            content_items = [
                ResponseOutputText(
                    type="output_text",
                    text=text_content,
                    annotations=[],
                )
            ]
            msg = ResponseOutputMessage(
                id=f"msg_{uuid.uuid4().hex[:16]}",
                type="message",
                role="assistant",
                content=content_items,
                status="completed",
            )
            output_items.append(msg)
        
        # Add tool calls as separate items
        output_items.extend(tool_calls)
        
        # Build usage
        usage = Usage(
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            total_tokens=response.usage.input_tokens + response.usage.output_tokens,
        )
        
        return ModelResponse(
            output=output_items,
            usage=usage,
            response_id=response.id,
        )
    
    async def get_response(
        self,
        system_instructions: Optional[str],
        input: List[TResponseInputItem],
        model_settings: Any,
        tools: List[Any],
        output_schema: Optional[Any],
        handoffs: List[Any],
        tracing: Any,
        *,
        previous_response_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        prompt: Optional[Any] = None,
    ) -> ModelResponse:
        """Get a response from the Anthropic model."""
        
        # Convert tools
        anthropic_tools = self._convert_tools_to_anthropic(tools)
        
        # Convert messages
        system_from_messages, messages = self._convert_messages_to_anthropic(input)
        
        # Combine system prompts
        full_system = ""
        if system_instructions:
            full_system = system_instructions
        if system_from_messages:
            full_system = f"{full_system}\n\n{system_from_messages}".strip()
        
        # Ensure messages alternate correctly
        if not messages:
            messages = [{"role": "user", "content": "Hello"}]
        
        # Build request kwargs
        kwargs = {
            "model": self._model,
            "max_tokens": getattr(model_settings, 'max_tokens', None) or 8192,
            "messages": messages,
        }
        
        if full_system:
            kwargs["system"] = full_system
        
        if anthropic_tools:
            kwargs["tools"] = anthropic_tools
        
        # Temperature
        if hasattr(model_settings, 'temperature') and model_settings.temperature is not None:
            kwargs["temperature"] = model_settings.temperature
        
        log.debug(f"Anthropic request: model={self._model}, messages={len(messages)}, tools={len(anthropic_tools)}")
        
        try:
            response = await self._client.messages.create(**kwargs)
            return self._convert_response_to_openai(response)
        except Exception as e:
            log.error(f"Anthropic API error: {e}")
            raise
    
    async def stream_response(
        self,
        system_instructions: Optional[str],
        input: List[TResponseInputItem],
        model_settings: Any,
        tools: List[Any],
        output_schema: Optional[Any],
        handoffs: List[Any],
        tracing: Any,
        *,
        previous_response_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        prompt: Optional[Any] = None,
    ) -> AsyncIterator[Any]:
        """Stream a response from the Anthropic model."""
        # For now, fall back to non-streaming
        response = await self.get_response(
            system_instructions, input, model_settings, tools,
            output_schema, handoffs, tracing,
            previous_response_id=previous_response_id,
            conversation_id=conversation_id,
            prompt=prompt,
        )
        yield response


def create_azure_anthropic_client(
    api_key: Optional[str] = None,
    endpoint: Optional[str] = None,
) -> AsyncAnthropic:
    """
    Create an Anthropic client configured for Azure.
    
    Args:
        api_key: Azure API key (defaults to AZURE_KEY env var)
        endpoint: Azure endpoint URL (defaults to AZURE_ENDPOINT env var)
    
    Returns:
        AsyncAnthropic client configured for Azure
    """
    api_key = api_key or os.environ.get("AZURE_KEY")
    endpoint = endpoint or os.environ.get("AZURE_ENDPOINT")
    
    if not api_key:
        raise ValueError("API key required - set AZURE_KEY env var or pass api_key")
    if not endpoint:
        raise ValueError("Endpoint required - set AZURE_ENDPOINT env var or pass endpoint")
    
    # Azure Anthropic endpoint should end with /anthropic
    # The client will append /v1/messages
    base_url = endpoint.rstrip("/")
    if not base_url.endswith("/anthropic"):
        base_url = f"{base_url}/anthropic"
    
    return AsyncAnthropic(
        api_key=api_key,
        base_url=base_url,
    )
