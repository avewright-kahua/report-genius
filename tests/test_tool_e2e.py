"""
End-to-end test for build_custom_template with new features.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_build_custom_template_with_all_features():
    """Test the build_custom_template tool with all new features."""
    from report_genius.templates import (
        PortableViewTemplate, Section, SectionType,
        HeaderConfig, DetailConfig, ListConfig,
        FieldDef, FieldFormat as TGFieldFormat,
        LayoutConfig, PageHeaderFooterConfig, Alignment,
    )
    from report_genius.rendering import DocxRenderer as SOTADocxRenderer
    
    # Build a comprehensive template with all new features
    template = PortableViewTemplate(
        name="Full Featured RFI Template",
        entity_def="RFI",
        layout=LayoutConfig(
            columns=1,
            page_header=PageHeaderFooterConfig(
                left_text="Kahua Inc.",
                center_text="Request for Information",
                font_size=10,
            ),
            page_footer=PageHeaderFooterConfig(
                include_page_number=True,
                page_number_format="Page {page} of {total}",
                font_size=9,
            ),
        ),
        sections=[
            # Header with custom styling
            Section(
                type=SectionType.HEADER,
                order=0,
                header_config=HeaderConfig(
                    static_title="Beau's RFI Template",
                    title_font="Comic Sans MS",
                    title_size=28,
                    title_color="#0000FF",
                    title_bold=True,
                    title_alignment=Alignment.CENTER,
                    subtitle_template="RFI #{Number} - {Subject}",
                ),
            ),
            # Detail section
            Section(
                type=SectionType.DETAIL,
                title="RFI Information",
                order=1,
                detail_config=DetailConfig(
                    fields=[
                        FieldDef(path="Number", label="RFI Number"),
                        FieldDef(path="Subject", label="Subject"),
                        FieldDef(path="Status", label="Status"),
                        FieldDef(path="Priority", label="Priority"),
                    ],
                    columns=2,
                ),
            ),
            # Bullet list
            Section(
                type=SectionType.LIST,
                title="Action Items",
                order=2,
                list_config=ListConfig(
                    list_type="bullet",
                    items=[
                        "Review attached documents",
                        "Provide technical clarification",
                        "Submit response by {DueDate}",
                    ],
                ),
            ),
            # Numbered list
            Section(
                type=SectionType.LIST,
                title="Approval Steps",
                order=3,
                list_config=ListConfig(
                    list_type="number",
                    items=[
                        "Project manager review",
                        "Engineering review",
                        "Client approval",
                        "Response submitted",
                    ],
                ),
            ),
        ],
    )
    
    print("Template created with:")
    print(f"  - Name: {template.name}")
    print(f"  - Entity: {template.entity_def}")
    print(f"  - Page Header: {template.layout.page_header is not None}")
    print(f"  - Page Footer: {template.layout.page_footer is not None}")
    print(f"  - Sections: {len(template.sections)}")
    for s in template.sections:
        print(f"    - {s.type.value}: {s.title or '(no title)'}")
    
    # Render the template
    print("\nRendering template...")
    renderer = SOTADocxRenderer(template)
    doc_bytes = renderer.render_to_bytes()
    
    # Save to disk
    output_path = Path(__file__).parent.parent / "reports" / "test_full_features_e2e.docx"
    output_path.parent.mkdir(exist_ok=True)
    output_path.write_bytes(doc_bytes)
    
    print(f"\n✅ Template rendered successfully!")
    print(f"   Output: {output_path}")
    print(f"   Size: {len(doc_bytes):,} bytes")


if __name__ == "__main__":
    test_build_custom_template_with_all_features()
