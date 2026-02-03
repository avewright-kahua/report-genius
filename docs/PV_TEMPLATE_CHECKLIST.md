# PV Template System Checklist

## Problem Summary

The agent generated a **specification document** instead of an actual portable view template. Key failures:
1. Used `generate_report` (analytics) instead of `build_custom_template` (PV)
2. Output was a design guide with placeholders shown as text in tables
3. Custom styling requests (Comic Sans, blue, large) were documented but not applied
4. No actual DOCX template with embedded Kahua placeholders was produced

---

## Checklist: Agent & Tool Sufficiency

### 1. Tool Selection Logic ✅ FIXED

| Check | Status | Issue |
|-------|--------|-------|
| Agent correctly identifies "create template" requests | ✅ | System prompt updated with ABSOLUTE RULES |
| Agent distinguishes template vs. report requests | ✅ | Added explicit criteria in prompt |
| System prompt is unambiguous | ✅ | Added "NEVER DO THIS" examples |
| Tool names are self-explanatory | ✅ | `build_custom_template` vs `generate_report` |

**Implemented:**
- [x] Added ABSOLUTE RULES section in system prompt
- [x] Added explicit WRONG vs RIGHT behavior examples
- [x] Added Kahua syntax quick reference inline

---

### 2. HeaderConfig Styling Options ✅ IMPLEMENTED

Current `HeaderConfig` supports:
```python
title_template: str             # ✅ Template string
subtitle_template: str          # ✅ Template string  
show_logo: bool                 # ✅ Logo toggle
logo_position: str              # ✅ left/right
fields: List[FieldDef]          # ✅ Additional fields
static_title: Optional[str]     # ✅ NEW: Static document title
title_font: Optional[str]       # ✅ NEW: Font family
title_size: Optional[int]       # ✅ NEW: Font size in points
title_color: Optional[str]      # ✅ NEW: Hex color
title_bold: bool = True         # ✅ NEW: Bold toggle
title_alignment: Alignment      # ✅ NEW: left/center/right
```

**Implemented:**
- [x] Extended `HeaderConfig` with custom title styling options
- [x] Added `static_title` field for user-defined document titles
- [x] Updated renderer to apply custom fonts/colors/sizes

---

### 3. DOCX Renderer Support ✅ IMPLEMENTED

Current renderer (`docx_renderer_sota.py`) has:
- ✅ `DesignTokens` with default fonts/colors
- ✅ Custom font override from HeaderConfig
- ✅ Custom size override from HeaderConfig
- ✅ Custom color override from HeaderConfig
- ✅ Arbitrary font support (Comic Sans, Arial Black, etc.)
- ✅ Per-template color customization

**Implemented:**
- [x] Renderer reads style from HeaderConfig
- [x] _render_header_simple applies custom styling
- [x] _render_header_with_logo applies custom styling
- [x] Tested with Comic Sans, blue, 28pt

---

### 4. Tool Parameter Completeness ✅ IMPLEMENTED

`build_custom_template` parameters:
```python
entity_type: str         # ✅ 
name: str                # ✅
sections_json: str       # ✅
include_logo: bool       # ✅
layout: str              # ✅
static_title: str        # ✅ NEW: Document title
title_style_json: str    # ✅ NEW: {"font": "Comic Sans MS", "size": 28, "color": "#0000FF"}
```

**Implemented:**
- [x] Added `static_title` parameter
- [x] Added `title_style_json` parameter
- [x] Updated tool docstring with styling examples

---

### 5. Kahua Placeholder Format ✅ CORRECT

The system correctly generates:
- `[Attribute(RFI.Number)]` for text fields
- `[Currency(Source=Attribute,Path=Amount,Format="C2")]` for currency
- `[Date(Source=Attribute,Path=DueDate,Format="d")]` for dates
- `[StartTable...]...[EndTable]` for collections
- `[IF(...)][ENDIF]` for conditionals

**No action needed.**

---

### 6. Static Title vs. Placeholder Title ✅ IMPLEMENTED

User requested: "Title that says 'Beaus RFI Template'"

This is a **static title** (literal text), not a placeholder. System now supports:
- `{Number}` → `[Attribute(RFI.Number)]` (dynamic)
- `static_title: "Beaus RFI Template"` → literal text output
- Mixed templates: "RFI: {Number}" → "RFI: [Attribute(Number)]"

**Implemented:**
- [x] Added `static_title` in HeaderConfig
- [x] Renderer outputs literal text when static_title is set
- [x] Mixed template support works correctly

---

### 7. End-to-End Workflow ✅ COMPLETE

Expected flow:
1. User: "Create RFI template with blue Comic Sans title"
2. Agent: Calls `build_custom_template` with static_title and title_style_json
3. System: Creates template JSON with custom styling
4. Agent: Calls `render_smart_template`
5. System: Generates DOCX with custom styling applied
6. Agent: Returns download link

All steps now functional.

---

## New Features Added

### 8. Bullet/Numbered Lists ✅ IMPLEMENTED

New `ListConfig` in schema:
```python
class ListConfig(BaseModel):
    list_type: Literal["bullet", "number"] = "bullet"
    items: List[str] = []          # Static items or {field} templates
    source: Optional[str] = None   # Path to collection for dynamic lists
    item_field: Optional[str] = None  # Field from collection
    indent_level: int = 0          # Nesting level
```

New `SectionType.LIST` with `_render_list` method in renderer.

---

### 9. Page Headers & Footers ✅ IMPLEMENTED

New `PageHeaderFooterConfig` in schema:
```python
class PageHeaderFooterConfig(BaseModel):
    left_text: Optional[str] = None
    center_text: Optional[str] = None
    right_text: Optional[str] = None
    include_page_number: bool = False
    page_number_format: str = "Page {page} of {total}"
    font_size: int = 9
    show_on_first_page: bool = True
```

LayoutConfig now supports:
```python
page_header: Optional[PageHeaderFooterConfig] = None
page_footer: Optional[PageHeaderFooterConfig] = None
```

Renderer implements:
- `_setup_page_header()` - 3-column table for left/center/right alignment
- `_setup_page_footer()` - 3-column table with page number support
- `_add_page_number_field()` - XML field codes for PAGE/NUMPAGES

---

## Required Schema Changes (COMPLETED)

### HeaderConfig Extension
```python
class HeaderConfig(BaseModel):
    # Existing
    title_template: str = "{Number}"
    subtitle_template: Optional[str] = None
    fields: List[FieldDef] = Field(default_factory=list)
    show_logo: bool = False
    logo_position: str = "left"
    
    # NEW: Static title option
    static_title: Optional[str] = None  # If set, use this instead of title_template
    
    # NEW: Title styling
    title_font: Optional[str] = None      # Font family override
    title_size: Optional[int] = None      # Point size override
    title_color: Optional[str] = None     # Hex color override
    title_bold: bool = True
    title_alignment: Alignment = Alignment.LEFT
```

### StyleConfig Extension
```python
class StyleConfig(BaseModel):
    # Existing colors/fonts...
    
    # NEW: Allow complete override
    custom_fonts: Dict[str, str] = {}  # {"title": "Comic Sans MS", "body": "Arial"}
    custom_colors: Dict[str, str] = {}  # {"primary": "#0000FF"}
    custom_sizes: Dict[str, int] = {}   # {"title": 28, "body": 11}
```

---

## Required Tool Changes

### build_custom_template Enhancement
```python
@tool
def build_custom_template(
    entity_type: str,
    name: str,
    sections_json: str,
    include_logo: bool = True,
    layout: str = "single_column",
    # NEW PARAMETERS:
    static_title: str = None,           # Document title (not placeholder)
    title_style_json: str = None,       # {"font": "Comic Sans MS", "size": 24, "color": "#0000FF"}
) -> dict:
```

---

## Required Renderer Changes

### SOTADocxRenderer._render_header_simple
```python
def _render_header_simple(self, config: HeaderConfig) -> None:
    # Handle static vs. dynamic title
    if config.static_title:
        title_text = config.static_title
    else:
        title_text = self._expand_template(config.title_template)
    
    p = self.doc.add_paragraph()
    run = p.add_run(title_text)
    
    # Apply custom styling if provided, else use defaults
    run.font.name = config.title_font or self.tokens.FONT_HEADING
    run.font.size = Pt(config.title_size or self.tokens.SIZE_TITLE)
    run.font.bold = config.title_bold
    
    if config.title_color:
        run.font.color.rgb = RGBColor(*hex_to_rgb(config.title_color))
    else:
        run.font.color.rgb = RGBColor(*hex_to_rgb(self.tokens.COLOR_PRIMARY))
```

---

### 10. Hyperlinks ✅ IMPLEMENTED

New `HyperlinkDef` in schema:
```python
class HyperlinkDef(BaseModel):
    text: str                          # Display text
    url: str                           # URL (can include Kahua placeholder like {WebUrl})
    tooltip: Optional[str] = None      # Optional hover tooltip
```

TextConfig now supports:
```python
hyperlinks: List[HyperlinkDef] = []  # Inline hyperlinks
```

Renderer implements:
- `_add_hyperlink()` - Creates hyperlink using XML and relationships
- `_add_hyperlink_paragraph()` - Adds a paragraph with hyperlink
- Hyperlink style automatically added to document

---

## Priority Implementation Order (ALL COMPLETED)

1. ~~**HIGH: Fix tool selection**~~ ✅ Agent uses correct tool
2. ~~**HIGH: Add static_title support**~~ ✅ Users have custom document titles
3. ~~**MEDIUM: Add title styling**~~ ✅ Font, size, color customization
4. ~~**MEDIUM: Wire styling through renderer**~~ ✅ Style configs applied
5. ~~**LOW: Full StyleConfig overrides**~~ ✅ Complete theming system

---

## Test Cases

After implementation, verify these work:

```
User: "Create an RFI template"
→ Uses build_custom_template, renders DOCX with placeholders ✅

User: "Make the title 'Beaus RFI Template' in Comic Sans, blue, size 28"
→ Applies static_title, custom font/color/size ✅

User: "Show me all overdue RFIs"
→ Uses query_entities + generate_report (NOT template tools) ✅

User: "Add the Due Date field"
→ Uses modify_existing_template ✅

User: "Remove the logo"
→ Uses modify_existing_template with toggle_logo ✅
```

---

## Feature Summary

| Feature | Status | Schema | Renderer | Tool |
|---------|--------|--------|----------|------|
| Custom title styling | ✅ | HeaderConfig | _render_header_* | build_custom_template |
| Static titles | ✅ | HeaderConfig.static_title | _render_header_* | static_title param |
| Page headers | ✅ | PageHeaderFooterConfig | _setup_page_header | page_header_json |
| Page footers | ✅ | PageHeaderFooterConfig | _setup_page_footer | page_footer_json |
| Page numbers | ✅ | PageHeaderFooterConfig | _add_page_number_field | include_page_number |
| Bullet lists | ✅ | ListConfig | _render_list | sections_json |
| Numbered lists | ✅ | ListConfig | _render_list | sections_json |
| Hyperlinks | ✅ | HyperlinkDef | _add_hyperlink | TextConfig.hyperlinks |
