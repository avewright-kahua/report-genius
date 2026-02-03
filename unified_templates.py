"""
Unified Template System - Bridges report-genius and template_gen

This module provides a unified API for template generation that combines:
1. The existing pv_template_schema (report-genius style)
2. The template_gen SOTA agent architecture
3. Kahua-compatible DOCX rendering with proper placeholder syntax

The key insight: both systems generate templates that render to DOCX with
Kahua placeholders. We unify the schema and provide adapters between them.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

# Add template_gen to path
TEMPLATE_GEN_PATH = Path(__file__).parent / "template_gen"
if str(TEMPLATE_GEN_PATH) not in sys.path:
    sys.path.insert(0, str(TEMPLATE_GEN_PATH))

# Import from existing report-genius infrastructure
from pv_template_schema import (
    PortableTemplate as RGPortableTemplate,
    Section as RGSection,
    SectionType as RGSectionType,
    FieldMapping,
    FieldFormat,
    HeaderSection,
    DetailSection,
    TableSection,
    TextSection,
    ColumnDef,
    Alignment,
    PageLayout,
    StyleConfig,
)

# Import from canonical report_genius SOTA system
from report_genius.templates import (
    PortableViewTemplate as TGPortableTemplate,
    Section as TGSection,
    SectionType as TGSectionType,
    FieldDef,
    FieldFormat as TGFieldFormat,
    HeaderConfig,
    DetailConfig,
    TextConfig,
    TableConfig,
    TableColumn,
    LayoutConfig,
    StyleConfig as TGStyleConfig,
    Condition,
    ConditionOperator,
)

# Import design system from template_gen (to be migrated later)
from template_gen.core import (
    DesignSystem,
    TemplateArchetype,
    CreativeComposer,
    InformationDensity,
    VisualTone,
)

from template_gen.core.smart_agent import AgentTools, ConversationState
from template_gen.schema_introspector import get_available_schemas, EntitySchema
from report_genius.rendering import DocxRenderer


# ============================================================================
# Schema Adapters - Convert between report-genius and template_gen formats
# ============================================================================

def rg_format_to_tg_format(rg_fmt: FieldFormat) -> TGFieldFormat:
    """Convert report-genius FieldFormat to template_gen FieldFormat."""
    mapping = {
        FieldFormat.TEXT: TGFieldFormat.TEXT,
        FieldFormat.NUMBER: TGFieldFormat.NUMBER,
        FieldFormat.CURRENCY: TGFieldFormat.CURRENCY,
        FieldFormat.DATE: TGFieldFormat.DATE,
        FieldFormat.DATETIME: TGFieldFormat.DATETIME,
        FieldFormat.PERCENT: TGFieldFormat.PERCENT,
        FieldFormat.BOOLEAN: TGFieldFormat.BOOLEAN,
    }
    return mapping.get(rg_fmt, TGFieldFormat.TEXT)


def tg_format_to_rg_format(tg_fmt: TGFieldFormat) -> FieldFormat:
    """Convert template_gen FieldFormat to report-genius FieldFormat."""
    mapping = {
        TGFieldFormat.TEXT: FieldFormat.TEXT,
        TGFieldFormat.NUMBER: FieldFormat.NUMBER,
        TGFieldFormat.CURRENCY: FieldFormat.CURRENCY,
        TGFieldFormat.DATE: FieldFormat.DATE,
        TGFieldFormat.DATETIME: FieldFormat.DATETIME,
        TGFieldFormat.PERCENT: FieldFormat.PERCENT,
        TGFieldFormat.BOOLEAN: FieldFormat.BOOLEAN,
    }
    return mapping.get(tg_fmt, FieldFormat.TEXT)


def rg_section_to_tg_section(rg_section: RGSection) -> TGSection:
    """Convert a report-genius section to template_gen section."""
    section_type_map = {
        RGSectionType.HEADER: TGSectionType.HEADER,
        RGSectionType.DETAIL: TGSectionType.DETAIL,
        RGSectionType.TABLE: TGSectionType.TABLE,
        RGSectionType.TEXT: TGSectionType.TEXT,
        RGSectionType.PAGE_BREAK: TGSectionType.DIVIDER,
    }
    
    tg_type = section_type_map.get(rg_section.type, TGSectionType.DETAIL)
    
    # Build appropriate config
    if rg_section.type == RGSectionType.HEADER and rg_section.header_config:
        cfg = rg_section.header_config
        header_config = HeaderConfig(
            title_template=f"{{{cfg.fields[0].path}}}" if cfg.fields else "{Number}",
            subtitle_template=f"{{{cfg.fields[1].path}}}" if len(cfg.fields) > 1 else None,
            fields=[
                FieldDef(path=f.path, label=f.label, format=rg_format_to_tg_format(f.format))
                for f in cfg.fields[2:] if cfg.fields
            ] if cfg.fields and len(cfg.fields) > 2 else [],
        )
        return TGSection(
            type=TGSectionType.HEADER,
            title=rg_section.title,
            order=rg_section.order,
            header_config=header_config,
        )
    
    elif rg_section.type == RGSectionType.DETAIL and rg_section.detail_config:
        cfg = rg_section.detail_config
        detail_config = DetailConfig(
            fields=[
                FieldDef(path=f.path, label=f.label, format=rg_format_to_tg_format(f.format))
                for f in cfg.fields
            ],
            columns=cfg.columns,
        )
        return TGSection(
            type=TGSectionType.DETAIL,
            title=rg_section.title,
            order=rg_section.order,
            detail_config=detail_config,
        )
    
    elif rg_section.type == RGSectionType.TABLE and rg_section.table_config:
        cfg = rg_section.table_config
        table_config = TableConfig(
            source=cfg.source,
            columns=[
                TableColumn(
                    field=FieldDef(
                        path=col.field.path,
                        label=col.field.label,
                        format=rg_format_to_tg_format(col.field.format),
                    ),
                    width=int(col.width * 100) if col.width else None,
                )
                for col in cfg.columns
            ],
            show_header=cfg.show_header,
        )
        return TGSection(
            type=TGSectionType.TABLE,
            title=rg_section.title,
            order=rg_section.order,
            table_config=table_config,
        )
    
    elif rg_section.type == RGSectionType.TEXT and rg_section.text_config:
        cfg = rg_section.text_config
        text_config = TextConfig(
            content=cfg.content,
        )
        return TGSection(
            type=TGSectionType.TEXT,
            title=rg_section.title,
            order=rg_section.order,
            text_config=text_config,
        )
    
    # Default: empty detail section
    return TGSection(
        type=tg_type,
        title=rg_section.title,
        order=rg_section.order,
    )


def tg_section_to_rg_section(tg_section: TGSection) -> RGSection:
    """Convert a template_gen section to report-genius section."""
    from pv_template_schema import (
        HeaderSection as RGHeaderSection,
        DetailSection as RGDetailSection,
        TableSection as RGTableSection,
        TextSection as RGTextSection,
    )
    
    section_type_map = {
        TGSectionType.HEADER: RGSectionType.HEADER,
        TGSectionType.DETAIL: RGSectionType.DETAIL,
        TGSectionType.TABLE: RGSectionType.TABLE,
        TGSectionType.TEXT: RGSectionType.TEXT,
        TGSectionType.DIVIDER: RGSectionType.PAGE_BREAK,
        TGSectionType.SPACER: RGSectionType.PAGE_BREAK,
    }
    
    rg_type = section_type_map.get(tg_section.type, RGSectionType.DETAIL)
    
    section = RGSection(
        type=rg_type,
        title=tg_section.title,
        order=tg_section.order,
    )
    
    if tg_section.type == TGSectionType.HEADER and tg_section.header_config:
        cfg = tg_section.header_config
        fields = []
        # Parse title template to get primary field
        if cfg.title_template:
            import re
            matches = re.findall(r'\{(\w+(?:\.\w+)*)\}', cfg.title_template)
            for m in matches:
                fields.append(FieldMapping(path=m, label=None, format=FieldFormat.TEXT))
        fields.extend([
            FieldMapping(path=f.path, label=f.label, format=tg_format_to_rg_format(f.format))
            for f in cfg.fields
        ])
        section.header_config = RGHeaderSection(
            fields=fields,
            title_template=cfg.title_template,
        )
    
    elif tg_section.type == TGSectionType.DETAIL and tg_section.detail_config:
        cfg = tg_section.detail_config
        section.detail_config = RGDetailSection(
            fields=[
                FieldMapping(path=f.path, label=f.label, format=tg_format_to_rg_format(f.format))
                for f in cfg.fields
            ],
            columns=cfg.columns,
        )
    
    elif tg_section.type == TGSectionType.TABLE and tg_section.table_config:
        cfg = tg_section.table_config
        section.table_config = RGTableSection(
            source=cfg.source,
            columns=[
                ColumnDef(
                    field=FieldMapping(
                        path=col.field.path,
                        label=col.field.label,
                        format=tg_format_to_rg_format(col.field.format),
                    ),
                    width=col.width / 100.0 if col.width else None,
                )
                for col in cfg.columns
            ],
            show_header=cfg.show_header,
        )
    
    elif tg_section.type == TGSectionType.TEXT and tg_section.text_config:
        cfg = tg_section.text_config
        section.text_config = RGTextSection(
            content=cfg.content,
        )
    
    return section


def rg_to_tg_template(rg_template: RGPortableTemplate) -> TGPortableTemplate:
    """Convert a full report-genius template to template_gen format."""
    sections = [rg_section_to_tg_section(s) for s in rg_template.sections]
    
    # Ensure sections have valid order
    for i, s in enumerate(sections):
        s.order = i
    
    return TGPortableTemplate(
        id=rg_template.id or f"pv-converted-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        name=rg_template.name,
        description=rg_template.description,
        entity_def=rg_template.target_entity_def,
        sections=sections,
    )


def tg_to_rg_template(tg_template: TGPortableTemplate) -> RGPortableTemplate:
    """Convert a template_gen template to report-genius format."""
    sections = [tg_section_to_rg_section(s) for s in tg_template.get_sections_ordered()]
    
    return RGPortableTemplate(
        id=tg_template.id,
        name=tg_template.name,
        description=tg_template.description,
        target_entity_def=tg_template.entity_def or "",
        sections=sections,
    )


# ============================================================================
# Unified Template API
# ============================================================================

class UnifiedTemplateSystem:
    """
    Unified template system that bridges report-genius and template_gen.
    
    Provides a single API for:
    - Creating templates with SOTA agent intelligence
    - Converting between schema formats
    - Rendering to Kahua-compatible DOCX
    - Managing template storage
    """
    
    def __init__(self):
        self.design_system = DesignSystem()
        self.composer = CreativeComposer()
        self._tg_schemas = None
        
    @property
    def tg_schemas(self) -> Dict[str, EntitySchema]:
        """Lazy-load template_gen schemas."""
        if self._tg_schemas is None:
            self._tg_schemas = get_available_schemas()
        return self._tg_schemas
    
    def get_archetypes(self) -> List[Dict[str, str]]:
        """Get available template archetypes."""
        return [
            {"id": a.value, "name": a.value.replace("_", " ").title()}
            for a in TemplateArchetype
        ]
    
    def infer_archetype(
        self,
        entity_type: str,
        user_intent: Optional[str] = None,
    ) -> TemplateArchetype:
        """Infer the best archetype for an entity type and intent."""
        return self.design_system.infer_archetype(entity_type, user_intent)
    
    def compose_smart(
        self,
        entity_type: str,
        archetype: Optional[Union[str, TemplateArchetype]] = None,
        user_intent: Optional[str] = None,
        name: Optional[str] = None,
    ) -> TGPortableTemplate:
        """
        Create a template using the SOTA composer.
        
        Args:
            entity_type: Entity type name (e.g., "Invoice", "RFI", "ExpenseContract")
            archetype: Template archetype or None to auto-infer
            user_intent: Natural language description of what user wants
            name: Template name
            
        Returns:
            TGPortableTemplate ready for rendering
        """
        # Resolve entity type
        entity_key = None
        entity_lower = entity_type.lower()
        for key in self.tg_schemas:
            if key.lower() == entity_lower:
                entity_key = key
                break
        
        if not entity_key:
            raise ValueError(f"Unknown entity type: {entity_type}. Available: {list(self.tg_schemas.keys())}")
        
        schema = self.tg_schemas[entity_key]
        
        # Determine archetype
        if archetype is None:
            archetype = self.infer_archetype(schema.name, user_intent)
        elif isinstance(archetype, str):
            archetype = TemplateArchetype(archetype)
        
        # Compose
        template = self.composer.compose(schema, archetype)
        
        # Override name if provided
        if name:
            template.name = name
        
        return template
    
    def create_agent_session(self) -> "UnifiedAgentSession":
        """Create a new agent session for conversational template creation."""
        return UnifiedAgentSession(self)
    
    def render_to_docx(
        self,
        template: Union[TGPortableTemplate, RGPortableTemplate],
        output_path: Optional[Path] = None,
        use_sota: bool = True,
    ) -> Optional[bytes]:
        """
        Render a template to DOCX with Kahua placeholder syntax.
        
        Args:
            template: Template in either format
            output_path: Path to save file, or None to return bytes
            use_sota: Use the SOTA renderer for professional output
            
        Returns:
            DOCX bytes if no output_path, None otherwise
        """
        # Convert to template_gen format if needed
        if isinstance(template, RGPortableTemplate):
            template = rg_to_tg_template(template)
        
        # Use SOTA renderer for better quality
        if use_sota:
            try:
                from report_genius.rendering import DocxRenderer as SOTADocxRenderer
                renderer = SOTADocxRenderer(template)
            except ImportError:
                # Fallback to standard renderer
                renderer = DocxRenderer(template)
        else:
            renderer = DocxRenderer(template)
        
        if output_path:
            renderer.render_to_file(output_path)
            return None
        
        return renderer.render_to_bytes()
    
    def convert_rg_to_tg(self, rg_template: RGPortableTemplate) -> TGPortableTemplate:
        """Convert report-genius template to template_gen format."""
        return rg_to_tg_template(rg_template)
    
    def convert_tg_to_rg(self, tg_template: TGPortableTemplate) -> RGPortableTemplate:
        """Convert template_gen template to report-genius format."""
        return tg_to_rg_template(tg_template)


class UnifiedAgentSession:
    """
    Agent session for conversational template creation.
    
    Wraps the SOTA smart agent with unified API.
    """
    
    def __init__(self, system: UnifiedTemplateSystem):
        self.system = system
        self.tools = AgentTools(system.tg_schemas, system.design_system)
        self.state = ConversationState()
    
    def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an agent tool and return the result."""
        result, self.state = self.tools.execute(tool_name, args, self.state)
        return result
    
    @property
    def current_template(self) -> Optional[TGPortableTemplate]:
        """Get the current template if one exists."""
        if self.state.current_template:
            return TGPortableTemplate(**self.state.current_template)
        return None
    
    @property
    def available_tools(self) -> List[Dict[str, Any]]:
        """Get available tool definitions."""
        return self.tools.get_tool_definitions()


# ============================================================================
# Singleton instance
# ============================================================================

_unified_system: Optional[UnifiedTemplateSystem] = None

def get_unified_system() -> UnifiedTemplateSystem:
    """Get the unified template system singleton."""
    global _unified_system
    if _unified_system is None:
        _unified_system = UnifiedTemplateSystem()
    return _unified_system
