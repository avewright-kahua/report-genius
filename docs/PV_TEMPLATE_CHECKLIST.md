# PV Template System Checklist

## Problem Summary

The agent generated a **specification document** instead of an actual portable view template. Key failures:
1. Used `generate_report` (analytics) instead of `build_custom_template` (PV)
2. Output was a design guide with placeholders shown as text in tables
3. Custom styling requests (Comic Sans, blue, large) were documented but not applied
4. No actual DOCX template with embedded Kahua placeholders was produced

---

## Checklist: Agent & Tool Sufficiency

### 1. Tool Selection Logic ❌ NEEDS WORK

| Check | Status | Issue |
|-------|--------|-------|
| Agent correctly identifies "create template" requests | ❌ | Used wrong tool despite clear system prompt |
| Agent distinguishes template vs. report requests | ❌ | Failed this time |
| System prompt is unambiguous | ⚠️ | Prompt is clear, but agent still picked wrong tool |
| Tool names are self-explanatory | ✅ | `build_custom_template` vs `generate_report` |

**Action Items:**
- [ ] Add stronger guardrails in system prompt
- [ ] Consider adding a "request classifier" tool that first categorizes intent
- [ ] Add examples of WRONG behavior with explicit "DO NOT DO THIS"

---

### 2. HeaderConfig Styling Options ❌ MISSING

Current `HeaderConfig` supports:
```python
title_template: str           # ✅ Template string
subtitle_template: str        # ✅ Template string  
show_logo: bool              # ✅ Logo toggle
logo_position: str           # ✅ left/right
fields: List[FieldDef]       # ✅ Additional fields
```

**Missing for custom styling:**
```python
# NEEDED - Not currently in schema
title_font: str              # ❌ Font family (e.g., "Comic Sans MS")
title_size: int              # ❌ Font size in points
title_color: str             # ❌ Hex color (e.g., "#0000FF")
title_bold: bool             # ❌ Bold toggle
title_alignment: str         # ❌ left/center/right
static_title: str            # ❌ Static text (not a placeholder)
```

**Action Items:**
- [ ] Extend `HeaderConfig` with custom title styling options
- [ ] Add `static_title` field for user-defined document titles
- [ ] Update renderer to apply custom fonts/colors/sizes

---

### 3. DOCX Renderer Support ⚠️ PARTIAL

Current renderer (`docx_renderer_sota.py`) has:
- ✅ `DesignTokens` with default fonts/colors
- ✅ Hardcoded `FONT_HEADING = "Calibri Light"`
- ✅ Hardcoded `SIZE_TITLE = 24`
- ✅ Hardcoded `COLOR_PRIMARY = "#1a365d"`
- ❌ No override mechanism for custom fonts per template
- ❌ No Comic Sans or arbitrary font support
- ❌ No per-template color customization

**Action Items:**
- [ ] Make renderer read style from `template.style` config
- [ ] Allow style overrides at section/field level
- [ ] Test with non-standard fonts (Comic Sans, Arial Black, etc.)

---

### 4. Tool Parameter Completeness ❌ MISSING STYLE PARAMS

`build_custom_template` parameters:
```python
entity_type: str         # ✅ 
name: str                # ✅
sections_json: str       # ✅
include_logo: bool       # ✅
layout: str              # ✅
# MISSING:
style_json: str          # ❌ Custom styling (fonts, colors, sizes)
header_style: dict       # ❌ Title-specific styling
```

**Action Items:**
- [ ] Add `style_json` or `header_style` parameter to `build_custom_template`
- [ ] Add `static_title` parameter for document name/branding
- [ ] Update tool docstring with styling examples

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

### 6. Static Title vs. Placeholder Title ❌ NOT SUPPORTED

User requested: "Title that says 'Beaus RFI Template'"

This is a **static title** (literal text), not a placeholder. Current system only supports:
- `{Number}` → `[Attribute(RFI.Number)]` (dynamic)

**Missing:**
- Static text that doesn't come from entity data
- Mix of static + dynamic: "RFI: {Number}"

**Action Items:**
- [ ] Support `static_title` in HeaderConfig
- [ ] Renderer should output literal text, not convert to placeholder
- [ ] Allow mixed templates: "RFI: {Number}" → "RFI: [Attribute(Number)]"

---

### 7. End-to-End Workflow ⚠️ INCOMPLETE

Expected flow:
1. User: "Create RFI template with blue Comic Sans title"
2. Agent: Calls `build_custom_template` with style params
3. System: Creates template JSON with custom styling
4. Agent: Calls `render_smart_template`
5. System: Generates DOCX with custom styling applied
6. Agent: Returns download link

Current gaps:
- Step 2: No style params accepted
- Step 3: No styling in schema
- Step 5: Renderer ignores custom styling

---

## Required Schema Changes

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

## Priority Implementation Order

1. **HIGH: Fix tool selection** - Agent must use correct tool
2. **HIGH: Add static_title support** - Users need custom document titles
3. **MEDIUM: Add title styling** - Font, size, color customization
4. **MEDIUM: Wire styling through renderer** - Apply style configs
5. **LOW: Full StyleConfig overrides** - Complete theming system

---

## Test Cases

After implementation, verify these work:

```
User: "Create an RFI template"
→ Uses build_custom_template, renders DOCX with placeholders

User: "Make the title 'Beaus RFI Template' in Comic Sans, blue, size 28"
→ Applies static_title, custom font/color/size

User: "Show me all overdue RFIs"
→ Uses query_entities + generate_report (NOT template tools)

User: "Add the Due Date field"
→ Uses modify_existing_template

User: "Remove the logo"
→ Uses modify_existing_template with toggle_logo
```
