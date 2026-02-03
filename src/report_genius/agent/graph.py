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

from .prompts import SYSTEM_PROMPT
from .tools import get_all_tools, ENTITY_ALIASES

# Load environment before imports that need it
load_dotenv()

log = logging.getLogger(__name__)

# ============== Configuration ==============

AZURE_ENDPOINT = os.environ.get("AZURE_ENDPOINT", "").rstrip("/")
AZURE_KEY = os.environ.get("AZURE_KEY", "")
MODEL_DEPLOYMENT = os.environ.get("AZURE_DEPLOYMENT", "claude-sonnet-4-5")

# Max messages to keep in context (prevent token overflow)
MAX_MESSAGES = 30


# ============== Agent State ==============

class AgentState(TypedDict):
    """State for the agent graph."""
    messages: Annotated[list, add_messages]


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


# ============== Graph Definition ==============

def create_agent():
    """Create the LangGraph agent."""
    
    # Get all tools
    all_tools = get_all_tools()
    
    # Create LLM with tools bound
    llm = create_llm()
    llm_with_tools = llm.bind_tools(all_tools)
    
    # Agent node - calls LLM
    def agent_node(state: AgentState):
        messages = state["messages"]
        
        # Ensure system message is first
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
        
        # Truncate message history if too long (keep system + recent messages)
        if len(messages) > MAX_MESSAGES:
            system_msg = messages[0] if isinstance(messages[0], SystemMessage) else None
            recent_messages = messages[-(MAX_MESSAGES - 1):] if system_msg else messages[-MAX_MESSAGES:]
            if system_msg:
                messages = [system_msg] + recent_messages
            else:
                messages = recent_messages
            log.info(f"Truncated message history to {len(messages)} messages")
        
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
    
    # Build graph
    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)
    
    graph.add_edge(START, "agent")
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
