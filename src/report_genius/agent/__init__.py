"""
Agent module - LangGraph-based template creation agent.

This module provides the AI agent for creating and managing portable view templates.
It wraps the LangGraph-based implementation with a clean API.

Usage:
    from report_genius.agent import get_agent, chat_sync, reset_session

    # Get or create agent
    agent = get_agent()
    
    # Chat with agent
    response = chat_sync("Create an RFI template for Summit project")
    
    # Reset session
    reset_session("session-123")
"""

# Try internal module first (new structure), fall back to root-level (legacy)
try:
    # New modular structure
    from .graph import (
        create_agent,
        get_agent,
        create_llm,
        reset_session,
        chat_sync,
        chat,
    )
    from .tools import ENTITY_ALIASES, resolve_entity_def, get_all_tools
    from .prompts import SYSTEM_PROMPT
    
    AGENT_AVAILABLE = True
    
except ImportError:
    # Fall back to legacy root-level module
    try:
        from langgraph_agent import (
            create_agent,
            get_agent,
            create_llm,
            reset_session,
            chat_sync,
            ENTITY_ALIASES,
            resolve_entity_def,
        )
        
        AGENT_AVAILABLE = True
        get_all_tools = None
        SYSTEM_PROMPT = None
        chat = None
        
    except ImportError as e:
        import warnings
        warnings.warn(f"LangGraph agent not available: {e}")
        
        AGENT_AVAILABLE = False
        create_agent = None
        get_agent = None
        create_llm = None
        reset_session = None
        chat_sync = None
        chat = None
        ENTITY_ALIASES = {}
        resolve_entity_def = None
        get_all_tools = None
        SYSTEM_PROMPT = None


__all__ = [
    # Availability flag
    "AGENT_AVAILABLE",
    
    # Agent creation
    "create_agent",
    "get_agent", 
    "create_llm",
    
    # Session management
    "reset_session",
    
    # Chat interface
    "chat_sync",
    "chat",
    
    # Tools
    "get_all_tools",
    "SYSTEM_PROMPT",
    
    # Configuration
    "ENTITY_ALIASES",
    "resolve_entity_def",
]
