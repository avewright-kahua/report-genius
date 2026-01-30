Below is the **single, complete Markdown file** content.
It is ready to be saved directly as, for example, `python-docx-complete-guide.md` and used by a VS Code agent or indexed for retrieval.
No sections are split across files and no external references are required for basic use.

---

# python-docx (docx) — Complete Documentation for Designing Word `.docx` Files in Python

This document provides comprehensive, implementation-oriented documentation for using the **python-docx** package (imported as `docx`) to design, generate, and modify Microsoft Word `.docx` files programmatically.

The focus is on **document construction**, **layout control**, **styling**, and **practical constraints**, rather than superficial examples.

---

## 1. Overview

**python-docx** is a Python library for creating and updating Microsoft Word `.docx` files (Word 2007+). It exposes a Pythonic object model over the WordprocessingML (OpenXML) format.

Capabilities:

* Create new `.docx` files
* Modify existing documents
* Add and format paragraphs, runs, tables, images
* Control sections, margins, headers, footers
* Apply and define styles
* Read and iterate document content

Non-goals / limitations:

* No layout rendering engine
* Limited support for floating objects, TOC fields, page numbering fields
* Some advanced features require XML-level manipulation

---

## 2. Installation and Import

### Installation

```bash
pip install python-docx
```

### Import

```python
from docx import Document
```

The package name is **python-docx**, but it is imported as `docx`.

---

## 3. Core Object Model

| Concept     | Description                                                 |
| ----------- | ----------------------------------------------------------- |
| Document    | Top-level container representing a `.docx` file             |
| Paragraph   | A block of text                                             |
| Run         | Inline text with uniform character formatting               |
| Style       | Named formatting definition                                 |
| Section     | Page-level settings (margins, orientation, headers/footers) |
| Table       | Grid-based layout object                                    |
| InlineShape | Inline image                                                |

Key principle: **Word formatting is hierarchical**
`Style → Paragraph → Run`

---

## 4. Creating, Opening, Saving Documents

### Create a new document

```python
doc = Document()
doc.save("output.docx")
```

### Open an existing document

```python
doc = Document("existing.docx")
doc.save("modified.docx")
```

### Start from a template

```python
doc = Document("template.docx")
```

Templates are strongly recommended for:

* Corporate formatting
* Headers/footers with logos
* Page numbers
* Numbering schemes
* Fonts and themes

---

## 5. Adding Content to a Document

### Headings

```python
doc.add_heading("Document Title", level=0)
doc.add_heading("Section", level=1)
doc.add_heading("Subsection", level=2)
```

`level` maps directly to Word’s built-in heading styles (`Title`, `Heading 1`–`Heading 9`).

---

### Paragraphs

```python
p = doc.add_paragraph("Initial text.")
doc.add_paragraph()  # empty paragraph
```

---

### Runs (inline formatting)

```python
p = doc.add_paragraph()
p.add_run("Normal text ")
r = p.add_run("Bold text")
r.bold = True
p.add_run(" normal again")
```

Runs represent contiguous text with identical character formatting.

---

## 6. Run Formatting (Character-Level)

```python
from docx.shared import Pt, RGBColor

r.font.name = "Calibri"
r.font.size = Pt(11)
r.font.bold = True
r.font.italic = True
r.font.underline = True
r.font.color.rgb = RGBColor(0, 0, 0)
```

Notes:

* Formatting inherits from styles unless overridden.
* Changing `paragraph.text` destroys existing runs.

---

## 7. Paragraph Formatting

### Alignment

```python
from docx.enum.text import WD_ALIGN_PARAGRAPH

p.alignment = WD_ALIGN_PARAGRAPH.CENTER
```

### Spacing

```python
from docx.shared import Pt

fmt = p.paragraph_format
fmt.space_before = Pt(6)
fmt.space_after = Pt(12)
fmt.line_spacing = 1.15
```

### Indentation

```python
from docx.shared import Inches

fmt.left_indent = Inches(0.5)
fmt.first_line_indent = Inches(0.25)
```

---

## 8. Styles (Best Practice)

### Apply a paragraph style

```python
doc.add_paragraph("Body text", style="Normal")
doc.add_paragraph("Heading text", style="Heading 1")
```

### Apply a character style

```python
r = p.add_run("Emphasis")
r.style = "Emphasis"
```

### Create or modify a style

```python
from docx.shared import Pt
from docx.enum.style import WD_STYLE_TYPE

styles = doc.styles

style = styles.add_style("BodySmall", WD_STYLE_TYPE.PARAGRAPH)
style.font.name = "Calibri"
style.font.size = Pt(9)
```

Guideline:

> Use styles for all reusable formatting. Inline formatting should be the exception.

---

## 9. Lists (Bullets and Numbering)

Lists are implemented via paragraph styles.

### Bullet list

```python
doc.add_paragraph("Item one", style="List Bullet")
doc.add_paragraph("Item two", style="List Bullet")
```

### Numbered list

```python
doc.add_paragraph("First", style="List Number")
doc.add_paragraph("Second", style="List Number")
```

For complex multi-level numbering, use a template.

---

## 10. Tables

### Create and populate

```python
table = doc.add_table(rows=1, cols=3)
table.style = "Table Grid"

hdr = table.rows[0].cells
hdr[0].text = "Metric"
hdr[1].text = "Value"
hdr[2].text = "Notes"

row = table.add_row().cells
row[0].text = "Throughput"
row[1].text = "128"
row[2].text = "Units/day"
```

### Column widths

```python
from docx.shared import Inches

table.autofit = False
for row in table.rows:
    row.cells[0].width = Inches(1.5)
```

Notes:

* Word may still auto-adjust widths.
* Borders, shading, and vertical alignment often require XML edits.

---

## 11. Images

### Add an image

```python
from docx.shared import Inches

doc.add_picture("image.png", width=Inches(5))
```

### Add image inline in a paragraph

```python
p = doc.add_paragraph("Figure: ")
run = p.add_run()
run.add_picture("figure.png", width=Inches(4))
```

Only **inline images** are officially supported.

---

## 12. Page Breaks and Sections

### Page break

```python
doc.add_page_break()
```

### Section settings

```python
from docx.shared import Inches
from docx.enum.section import WD_ORIENT

section = doc.sections[0]
section.left_margin = Inches(1)
section.top_margin = Inches(1)
```

### Landscape orientation

```python
section.orientation = WD_ORIENT.LANDSCAPE
section.page_width, section.page_height = (
    section.page_height,
    section.page_width,
)
```

---

## 13. Headers and Footers

```python
section = doc.sections[0]
section.header.paragraphs[0].text = "Confidential"
section.footer.paragraphs[0].text = "Footer text"
```

### Different first page

```python
section.different_first_page_header_footer = True
section.first_page_header.paragraphs[0].text = "First page header"
```

Page numbers typically require a template or XML fields.

---

## 14. Document Properties (Metadata)

```python
cp = doc.core_properties
cp.title = "Quarterly Report"
cp.author = "Avery Wright"
cp.comments = "Generated via python-docx"
```

---

## 15. Reading and Modifying Existing Documents

### Iterate paragraphs

```python
for p in doc.paragraphs:
    print(p.text)
```

### Safe text replacement (preserve formatting)

```python
for p in doc.paragraphs:
    for r in p.runs:
        r.text = r.text.replace("OLD", "NEW")
```

### Tables

```python
for table in doc.tables:
    for row in table.rows:
        for cell in row.cells:
            print(cell.text)
```

---

## 16. Units and Enums Reference

### Units

```python
from docx.shared import Inches, Cm, Mm, Pt
```

### Alignment

```python
from docx.enum.text import WD_ALIGN_PARAGRAPH
```

### Orientation

```python
from docx.enum.section import WD_ORIENT
```

---

## 17. Complete Example: Structured Report

```python
from docx import Document
from docx.shared import Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

doc = Document()

title = doc.add_heading("Monthly Operations Report", 0)
title.alignment = WD_ALIGN_PARAGRAPH.CENTER

doc.add_heading("Executive Summary", 1)
p = doc.add_paragraph()
p.add_run("Status: ").bold = True
p.add_run("All milestones achieved.")

doc.add_heading("Metrics", 1)
table = doc.add_table(rows=1, cols=2)
table.style = "Table Grid"
table.rows[0].cells[0].text = "Metric"
table.rows[0].cells[1].text = "Value"

row = table.add_row().cells
row[0].text = "Throughput"
row[1].text = "128"

doc.add_picture("chart.png", width=Inches(5))

doc.save("report.docx")
```

---

## 18. Practical Constraints and Guidance

* Use **templates** for anything layout-sensitive
* Avoid `paragraph.text = ...` unless formatting loss is acceptable
* python-docx is not a Word renderer; always validate output in Word
* Complex features often require XML manipulation (`OxmlElement`)

---

## 19. When XML Is Required

XML-level work is typically required for:

* Page numbers
* Table of contents
* Watermarks
* Floating images
* Complex numbering
* Field codes

In such cases, python-docx is best used as a **content injector**, not a full layout engine.

---

## 20. Summary

python-docx is well-suited for:

* Automated report generation
* Document assembly from structured data
* Template-driven document workflows

It is not suited for:

* Pixel-perfect page layout
* Advanced Word automation without templates

Design documents accordingly.

---
