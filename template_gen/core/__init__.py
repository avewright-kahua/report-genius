"""
Core module for intelligent template generation.

This module provides:
- DesignSystem: Document design principles and archetypes
- TemplateDesignAgent: SOTA agent for template creation via natural language
- CreativeComposer: Programmatic template composition with design intelligence
"""

from .design_system import (
    DesignSystem,
    DesignGuidelines,
    TemplateArchetype,
    InformationDensity,
    VisualTone,
    ARCHETYPE_GUIDELINES,
)

from .smart_agent import (
    TemplateDesignAgent,
    ConversationState,
    AgentTools,
    create_agent,
    quick_create_template,
)

from .creative_composer import (
    CreativeComposer,
    SectionPurpose,
    ComposedSection,
    compose_template,
    auto_compose_template,
)

__all__ = [
    # Design System
    "DesignSystem",
    "DesignGuidelines", 
    "TemplateArchetype",
    "InformationDensity",
    "VisualTone",
    "ARCHETYPE_GUIDELINES",
    # Agent
    "TemplateDesignAgent",
    "ConversationState",
    "AgentTools",
    "create_agent",
    "quick_create_template",
    # Composer
    "CreativeComposer",
    "SectionPurpose",
    "ComposedSection",
    "compose_template",
    "auto_compose_template",
]
