"""
LangGraph Agent Graph Definition

Core agent implementation using LangGraph with Claude via Azure.
"""

import os
import logging
from typing import Dict, Annotated, TypedDict

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

from .prompts import SYSTEM_PROMPT, TEMPLATE_BUILDER_PROMPT, ANALYTICS_PROMPT, INJECTION_PROMPT
from .tools import get_all_tools, get_tools_by_mode, ENTITY_ALIASES

# Load environment before imports that need it
load_dotenv()

log = logging.getLogger(__name__)

# ============== Configuration ==============

AZURE_ENDPOINT = os.environ.get("AZURE_ENDPOINT", "").rstrip("/")
AZURE_KEY = os.environ.get("AZURE_KEY", "")
MODEL_DEPLOYMENT = os.environ.get("AZURE_DEPLOYMENT", "claude-sonnet-4-5")

# Max messages to keep in context (prevent token overflow)
MAX_MESSAGES = 30
SUMMARY_TRIGGER_MESSAGES = int(os.getenv("RG_SUMMARY_TRIGGER_MESSAGES", "24"))
SUMMARY_KEEP_MESSAGES = int(os.getenv("RG_SUMMARY_KEEP_MESSAGES", "12"))


# ============== Agent State ==============

class AgentState(TypedDict):
    """State for the agent graph."""
    messages: Annotated[list, add_messages]
    mode: str
    summary: str


# ============== LLM Setup ==============

def create_llm():
    """Create Claude LLM configured for Azure."""
    base_url = f"{AZURE_ENDPOINT}/anthropic"
    
    return ChatAnthropic(
        model=MODEL_DEPLOYMENT,
        api_key=AZURE_KEY,
        base_url=base_url,
        max_tokens=8192,
    )


def _create_summary_llm():
    """Create a smaller LLM instance for summarization."""
    base_url = f"{AZURE_ENDPOINT}/anthropic"
    return ChatAnthropic(
        model=MODEL_DEPLOYMENT,
        api_key=AZURE_KEY,
        base_url=base_url,
        max_tokens=1024,
    )


# ============== Graph Definition ==============

def _classify_intent(text: str) -> str:
    text_lower = (text or "").lower()
    injection_keywords = [
        "inject", "injection", "token", "tokens", "placeholder", "placeholders",
        "docx", "word doc", "word document", "uploaded template", "upload template",
    ]
    template_keywords = [
        "template", "portable view", "pv",
    ]
    report_keywords = [
        "report", "summary", "list", "show me", "count",
    ]

    if any(k in text_lower for k in injection_keywords):
        return "injection"
    if any(k in text_lower for k in template_keywords):
        return "template"
    if any(k in text_lower for k in report_keywords):
        return "analytics"
    return "general"


def _summarize_messages(messages: list, existing_summary: str = "") -> str:
    summary_llm = _create_summary_llm()
    transcript_lines = []
    for msg in messages:
        if isinstance(msg, HumanMessage):
            transcript_lines.append(f"User: {msg.content}")
        elif isinstance(msg, AIMessage):
            transcript_lines.append(f"Assistant: {msg.content}")

    transcript = "\n".join(transcript_lines)
    system_prompt = (
        "Summarize the conversation for future context. "
        "Be concise and factual. Include:\n"
        "- user goals\n"
        "- files/modules mentioned\n"
        "- decisions/constraints\n"
        "- open questions\n"
        "- current task/status\n"
        "Use bullet points. Keep under 12 bullets."
    )
    user_payload = ""
    if existing_summary:
        user_payload += f"Existing summary:\n{existing_summary}\n\n"
    user_payload += f"Transcript:\n{transcript}"

    response = summary_llm.invoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_payload),
        ]
    )
    return response.content.strip()


def create_agent():
    """Create the LangGraph agent."""
    
    # Get all tools for execution
    all_tools = get_all_tools()
    
    # Create LLM (bind tools per mode inside agent_node)
    llm = create_llm()
    
    # Agent node - calls LLM
    def agent_node(state: AgentState):
        messages = state["messages"]
        mode = state.get("mode", "general")
        summary = state.get("summary", "")

        if mode == "injection":
            system_prompt = INJECTION_PROMPT
        elif mode == "template":
            system_prompt = TEMPLATE_BUILDER_PROMPT
        elif mode == "analytics":
            system_prompt = ANALYTICS_PROMPT
        else:
            system_prompt = SYSTEM_PROMPT
        if summary:
            system_prompt = f"{system_prompt}\n\nConversation summary:\n{summary}"
        
        # Ensure system message is first
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=system_prompt)] + messages
        elif messages[0].content != system_prompt:
            messages = [SystemMessage(content=system_prompt)] + messages[1:]
        
        # Truncate message history if too long (keep system + recent messages)
        if len(messages) > MAX_MESSAGES:
            system_msg = messages[0] if isinstance(messages[0], SystemMessage) else None
            recent_messages = messages[-(MAX_MESSAGES - 1):] if system_msg else messages[-MAX_MESSAGES:]
            if system_msg:
                messages = [system_msg] + recent_messages
            else:
                messages = recent_messages
            log.info(f"Truncated message history to {len(messages)} messages")
        
        llm_with_tools = llm.bind_tools(get_tools_by_mode(mode))
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}
    
    # Tool node - executes tools
    tool_node = ToolNode(all_tools)
    
    # Router - decide next step
    def should_continue(state: AgentState):
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return END
    
    def route_node(state: AgentState):
        messages = state["messages"]
        last_user_text = ""
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                last_user_text = msg.content
                break
        return {"mode": _classify_intent(last_user_text)}

    def summarize_node(state: AgentState):
        messages = state["messages"]
        if len(messages) < SUMMARY_TRIGGER_MESSAGES:
            return {}
        existing_summary = state.get("summary", "")
        try:
            new_summary = _summarize_messages(messages, existing_summary=existing_summary)
        except Exception as exc:
            log.warning(f"Summary generation failed: {exc}")
            return {}
        trimmed_messages = messages[-SUMMARY_KEEP_MESSAGES:]
        return {"summary": new_summary, "messages": trimmed_messages}

    # Build graph
    graph = StateGraph(AgentState)
    graph.add_node("router", route_node)
    graph.add_node("summarize", summarize_node)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)
    
    graph.add_edge(START, "router")
    graph.add_edge("router", "summarize")
    graph.add_edge("summarize", "agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")
    
    # Compile with memory
    memory = MemorySaver()
    return graph.compile(checkpointer=memory)


# ============== Main Interface ==============

_agent = None


def get_agent():
    """Get or create the agent singleton."""
    global _agent
    if _agent is None:
        log.info(f"Creating LangGraph agent with model: {MODEL_DEPLOYMENT}")
        _agent = create_agent()
    return _agent


def reset_session(session_id: str = "default") -> bool:
    """
    Reset a corrupted session to allow fresh conversation.
    Call this if a session gets into a bad state with pending tool calls.
    
    Returns True if session was reset.
    """
    global _agent
    _agent = None
    log.info(f"Session {session_id} reset - agent will be recreated")
    return True


async def chat(message: str, session_id: str = "default") -> str:
    """
    Send a message to the agent and get a response.
    
    Args:
        message: User message
        session_id: Session ID for conversation memory
    
    Returns:
        Agent response text
    """
    agent = get_agent()
    
    config = {"configurable": {"thread_id": session_id}}
    
    try:
        result = await agent.ainvoke(
            {"messages": [HumanMessage(content=message)]},
            config=config
        )
        
        # Get the last AI message
        for msg in reversed(result["messages"]):
            if isinstance(msg, AIMessage):
                return msg.content
        
        return "No response generated."
    except Exception as e:
        error_str = str(e)
        # Check for the specific tool_use/tool_result mismatch error
        if "tool_use ids were found without tool_result" in error_str:
            log.warning(f"Session {session_id} corrupted (pending tool calls), resetting...")
            reset_session(session_id)
            # Retry with fresh agent
            agent = get_agent()
            result = await agent.ainvoke(
                {"messages": [HumanMessage(content=message)]},
                config=config
            )
            for msg in reversed(result["messages"]):
                if isinstance(msg, AIMessage):
                    return msg.content
            return "No response generated."
        else:
            raise


def chat_sync(message: str, session_id: str = "default") -> str:
    """Synchronous version of chat."""
    agent = get_agent()
    
    config = {"configurable": {"thread_id": session_id}}
    
    try:
        result = agent.invoke(
            {"messages": [HumanMessage(content=message)]},
            config=config
        )
        
        for msg in reversed(result["messages"]):
            if isinstance(msg, AIMessage):
                return msg.content
        
        return "No response generated."
    except Exception as e:
        error_str = str(e)
        if "tool_use ids were found without tool_result" in error_str:
            log.warning(f"Session {session_id} corrupted, resetting...")
            reset_session(session_id)
            agent = get_agent()
            result = agent.invoke(
                {"messages": [HumanMessage(content=message)]},
                config=config
            )
            for msg in reversed(result["messages"]):
                if isinstance(msg, AIMessage):
                    return msg.content
            return "No response generated."
        else:
            raise


# ============== Test ==============

if __name__ == "__main__":
    print("Testing LangGraph agent...")
    response = chat_sync("Hello! What model are you?")
    print(f"\nResponse:\n{response}")
