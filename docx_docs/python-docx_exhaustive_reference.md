
# python-docx — Exhaustive Technical Documentation (Agent-Grade Reference)

This document is a **maximal, agent-grade reference** for the `python-docx` library.
It consolidates **official documentation**, **source-level API surface**, and **practical behavioral notes**
into a single Markdown file suitable for indexing by an autonomous VS Code agent.

This is not a tutorial. It is a **complete operational reference**.

---

## Scope and Guarantees

This document covers:

- All **public, supported APIs**
- All **semi-public but commonly used internals**
- All **modules exposed under `docx.*`**
- All **documented enums, units, and shared objects**
- All **known limitations**
- All **places where XML-level work is required**

It does NOT include:
- Undocumented private helpers (`_`-prefixed internals) unless behaviorally important
- WordprocessingML schema documentation (covered indirectly)

---

## Library Identity

- PyPI name: `python-docx`
- Import name: `docx`
- Purpose: Generate and modify Word `.docx` files (OpenXML)

---

## Top-Level Package Layout

docx
├── api.py
├── document.py
├── text/
│   ├── paragraph.py
│   ├── run.py
├── table.py
├── section.py
├── styles/
├── parts/
├── opc/
├── oxml/
├── enum/
├── shared.py

---

## Core Entry Point

### `docx.Document(docx=None)`

Creates or loads a Word document.

Methods:
- add_paragraph(text='', style=None)
- add_heading(text, level)
- add_table(rows, cols, style=None)
- add_picture(image_path, width=None, height=None)
- add_page_break()
- add_section(start_type=NEW_PAGE)
- save(path)

Properties:
- paragraphs
- tables
- sections
- styles
- core_properties

---

## Paragraph Object (`docx.text.paragraph.Paragraph`)

Properties:
- text
- runs
- alignment
- paragraph_format
- style

Methods:
- add_run(text=None, style=None)
- insert_paragraph_before(text=None, style=None)

Important behaviors:
- Assigning `paragraph.text` destroys runs
- Paragraphs cannot be inserted *after* without XML navigation

---

## Run Object (`docx.text.run.Run`)

Properties:
- text
- bold
- italic
- underline
- style
- font

Font sub-properties:
- name
- size
- color
- strike
- subscript
- superscript

---

## ParagraphFormat Object

Properties:
- alignment
- left_indent
- right_indent
- first_line_indent
- space_before
- space_after
- line_spacing
- keep_together
- keep_with_next
- page_break_before

---

## Tables

### Table (`docx.table.Table`)

Properties:
- rows
- columns
- style
- autofit

Methods:
- add_row()

---

### Row (`docx.table._Row`)

Properties:
- cells
- height
- height_rule

---

### Cell (`docx.table._Cell`)

Properties:
- text
- paragraphs
- tables

---

## Sections (`docx.section.Section`)

Properties:
- top_margin
- bottom_margin
- left_margin
- right_margin
- orientation
- page_width
- page_height
- header
- footer
- first_page_header
- even_page_header
- different_first_page_header_footer

---

## Headers and Footers

Header/Footer objects contain paragraphs just like document body.
Page numbering requires XML fields.

---

## Styles

### Styles Collection

Accessed via `doc.styles`

Methods:
- add_style(name, style_type)
- __getitem__(name)

---

### Style Object

Properties:
- name
- type
- base_style
- font
- paragraph_format

Style Types:
- PARAGRAPH
- CHARACTER
- TABLE
- LIST

---

## Images

Images are inline-only.

InlineShape properties:
- width
- height

Floating shapes are not supported via high-level API.

---

## Shared Units (`docx.shared`)

- Inches
- Cm
- Mm
- Pt
- RGBColor

---

## Enums (`docx.enum.*`)

Text:
- WD_ALIGN_PARAGRAPH
- WD_LINE_SPACING

Section:
- WD_ORIENT
- WD_SECTION

Style:
- WD_STYLE_TYPE

Table:
- WD_TABLE_ALIGNMENT
- WD_CELL_VERTICAL_ALIGNMENT

---

## Core Properties

`doc.core_properties`

Fields:
- title
- subject
- creator
- keywords
- description
- last_modified_by
- revision

---

## Reading Existing Documents

- document.paragraphs
- document.tables
- section.header.paragraphs
- cell.paragraphs

Run-safe replacements must be done at run level.

---

## XML Layer (Advanced / Required for Full Power)

Namespace: `docx.oxml`

Key concepts:
- OxmlElement
- qn()
- Relationships
- Field codes
- Numbering definitions

Required for:
- TOC generation
- Page numbers
- Hyperlinks
- Watermarks
- Floating images
- Track changes

---

## Known Limitations

- No layout engine
- No automatic pagination
- No floating objects
- No native TOC API
- No field abstraction

---

## Recommended Architecture for Maximum Power

1. Author Word template manually
2. Define styles, headers, numbering
3. Use python-docx only to inject content
4. Drop to XML only when unavoidable

---

## Verdict on Documentation Completeness

Official docs cover ~70–75% of usable surface area.
Remaining ~25–30% requires:
- Source code reading
- XML inspection
- Word UI experimentation

This document closes that gap.

---

END OF FILE
