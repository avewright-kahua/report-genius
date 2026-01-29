"""
Word Template Examples
Demonstrates usage of the Word template system.
"""

from pathlib import Path
from word_template_builder import WordDocumentBuilder, DocumentTheme, PageMargins, Alignment, FieldFormat
from word_template_defs import (
    WordTemplateDef, ThemeDef, TemplateRegistry, get_registry,
    create_field, create_column, create_title_section, create_header_section,
    create_field_grid_section, create_table_section, create_text_section,
    FieldDef, ColumnDef, FieldFormat as DefFieldFormat, Alignment as DefAlignment,
    get_contract_template, get_rfi_template
)
from word_template_renderer import render_template, render_template_to_bytes, quick_render


# Sample contract data
SAMPLE_CONTRACT = {
    "Number": "CON-2026-0042",
    "Description": "HVAC System Replacement - Building A",
    "WorkflowStatus": "Approved",
    "Type": "Subcontract",
    "CurrencyCode": "USD",
    "ContractorCompany": {
        "ShortLabel": "ACME Mechanical Inc.",
        "LongLabel": "ACME Mechanical Incorporated"
    },
    "OriginalContractValue": 150000.00,
    "ContractApprovedTotalValue": 168500.00,
    "ContractPendingTotalValue": 5000.00,
    "BalanceToFinishAmount": 42125.00,
    "ScopeOfWork": "Complete replacement of existing HVAC system including removal of old equipment, installation of new units, ductwork modifications, and commissioning.",
    "StartDate": "2026-01-15",
    "EndDate": "2026-06-30",
    "ChangeOrders": [
        {
            "Number": "CO-001",
            "Description": "Additional ductwork for server room",
            "ApprovedAmount": 12500.00,
            "Status": "Approved"
        },
        {
            "Number": "CO-002", 
            "Description": "Upgraded thermostats to smart controls",
            "ApprovedAmount": 6000.00,
            "Status": "Approved"
        },
        {
            "Number": "CO-003",
            "Description": "Extended warranty coverage",
            "ApprovedAmount": 0,
            "Status": "Pending"
        }
    ]
}

SAMPLE_RFI = {
    "Number": "RFI-2026-0015",
    "Subject": "Clarification on Ceiling Height Requirements",
    "Status": "Open",
    "Priority": "High",
    "DateSubmitted": "2026-01-20",
    "DateRequired": "2026-01-27",
    "Question": "Drawing A-201 shows ceiling height as 9'-0\" but specification section 09210 references 8'-6\" AFF. Please clarify the correct ceiling height for the main corridor.",
    "Response": None,
    "SubmittedBy": {"Name": "John Smith"},
    "AssignedTo": {"Name": "Jane Architect"},
    "RespondedBy": None,
    "DateResponded": None
}


def example_1_builder_api():
    """
    Example 1: Using WordDocumentBuilder directly for full control.
    Best for one-off documents or highly custom layouts.
    """
    print("Example 1: Direct builder API")
    
    # Create builder with custom theme
    theme = DocumentTheme(
        primary_color="#003366",
        secondary_color="#0066cc",
        accent_color="#00aa55",
        heading_font="Arial",
        body_font="Arial",
        title_size=22,
        body_size=10
    )
    
    builder = WordDocumentBuilder(theme=theme)
    
    # Build document
    builder.add_title(
        f"{SAMPLE_CONTRACT['Number']} - {SAMPLE_CONTRACT['Description']}",
        subtitle=f"Contractor: {SAMPLE_CONTRACT['ContractorCompany']['ShortLabel']}"
    )
    
    builder.add_field_grid([
        {"label": "Status", "value": SAMPLE_CONTRACT["WorkflowStatus"]},
        {"label": "Type", "value": SAMPLE_CONTRACT["Type"]},
        {"label": "Start Date", "value": SAMPLE_CONTRACT["StartDate"], "format": FieldFormat.DATE},
        {"label": "End Date", "value": SAMPLE_CONTRACT["EndDate"], "format": FieldFormat.DATE},
    ], columns=2)
    
    builder.add_section_header("Financial Summary")
    builder.add_field_grid([
        {"label": "Original Value", "value": SAMPLE_CONTRACT["OriginalContractValue"], "format": FieldFormat.CURRENCY},
        {"label": "Approved Total", "value": SAMPLE_CONTRACT["ContractApprovedTotalValue"], "format": FieldFormat.CURRENCY},
        {"label": "Pending", "value": SAMPLE_CONTRACT["ContractPendingTotalValue"], "format": FieldFormat.CURRENCY},
        {"label": "Balance to Finish", "value": SAMPLE_CONTRACT["BalanceToFinishAmount"], "format": FieldFormat.CURRENCY},
    ], columns=2, striped=True)
    
    builder.add_section_header("Scope of Work")
    builder.add_text(SAMPLE_CONTRACT["ScopeOfWork"])
    
    builder.add_section_header("Change Orders")
    builder.add_data_table(
        columns=[
            {"key": "Number", "label": "CO #", "align": Alignment.LEFT},
            {"key": "Description", "label": "Description"},
            {"key": "ApprovedAmount", "label": "Amount", "format": FieldFormat.CURRENCY, "align": Alignment.RIGHT},
            {"key": "Status", "label": "Status", "align": Alignment.CENTER},
        ],
        rows=SAMPLE_CONTRACT["ChangeOrders"],
        totals={"ApprovedAmount": sum(co["ApprovedAmount"] for co in SAMPLE_CONTRACT["ChangeOrders"])}
    )
    
    builder.add_header_footer(
        footer_text="ACME Construction Management",
        show_page_numbers=True
    )
    
    # Save
    output_path = builder.save(Path("reports") / "example1_builder_api.docx")
    print(f"  Created: {output_path}")
    return output_path


def example_2_builtin_template():
    """
    Example 2: Using a built-in template.
    Quick and easy for standard document types.
    """
    print("Example 2: Built-in template")
    
    template = get_contract_template()
    path, _ = render_template(template, SAMPLE_CONTRACT, filename="example2_builtin_contract.docx")
    print(f"  Created: {path}")
    
    # Also try RFI
    rfi_template = get_rfi_template()
    path2, _ = render_template(rfi_template, SAMPLE_RFI, filename="example2_builtin_rfi.docx")
    print(f"  Created: {path2}")
    
    return path, path2


def example_3_custom_template():
    """
    Example 3: Creating and saving a custom reusable template.
    Best for templates that will be reused multiple times.
    """
    print("Example 3: Custom reusable template")
    
    # Define a custom template
    template = WordTemplateDef(
        name="Contract Executive Summary",
        description="Compact one-page executive summary for contracts",
        entity_def="kahua_Contract.Contract",
        category="executive",
        tags=["contract", "executive", "summary"],
        
        sections=[
            create_title_section("{Number}", subtitle="{Description}", order=0),
            
            create_field_grid_section([
                create_field("ContractorCompany.ShortLabel", "Contractor"),
                create_field("WorkflowStatus", "Status"),
                create_field("OriginalContractValue", "Original Value", DefFieldFormat.CURRENCY),
                create_field("ContractApprovedTotalValue", "Current Value", DefFieldFormat.CURRENCY),
            ], columns=2, order=1),
            
            create_header_section("Key Dates", order=2),
            create_field_grid_section([
                create_field("StartDate", "Start", DefFieldFormat.DATE),
                create_field("EndDate", "End", DefFieldFormat.DATE),
            ], columns=2, order=3),
        ],
        
        theme=ThemeDef(
            primary_color="#1e3a5f",
            secondary_color="#2563eb",
            body_size=10,
            margin_top=0.5,
            margin_bottom=0.5,
            margin_left=0.75,
            margin_right=0.75,
        ),
        
        footer_text="Executive Summary - Confidential",
        show_page_numbers=True,
    )
    
    # Save template for reuse
    registry = get_registry()
    template_id = registry.save(template)
    print(f"  Saved template: {template_id}")
    
    # Render with data
    path, _ = render_template(template, SAMPLE_CONTRACT, filename="example3_custom_template.docx")
    print(f"  Created: {path}")
    
    # Load and render again (demonstrating reusability)
    loaded_template = registry.load(template_id)
    path2, _ = render_template(loaded_template, SAMPLE_CONTRACT, filename="example3_custom_reloaded.docx")
    print(f"  Created (reloaded): {path2}")
    
    return path


def example_4_quick_render():
    """
    Example 4: Quick render without defining a template.
    Fastest way to get a document from data.
    """
    print("Example 4: Quick render")
    
    path, _ = quick_render(
        title="Contract Quick Summary",
        data=SAMPLE_CONTRACT,
        fields=["Number", "Description", "WorkflowStatus", "ContractorCompany.ShortLabel", 
                "OriginalContractValue", "ContractApprovedTotalValue"],
        table_source="ChangeOrders",
        table_columns=["Number", "Description", "ApprovedAmount", "Status"],
        filename="example4_quick_render.docx"
    )
    print(f"  Created: {path}")
    return path


def example_5_programmatic_template():
    """
    Example 5: Building template programmatically with conditions.
    Shows conditional sections and advanced features.
    """
    print("Example 5: Programmatic template with conditions")
    
    from word_template_defs import Condition, Section, SectionKind, DataTableSection
    
    template = WordTemplateDef(
        name="Contract Detail Report",
        description="Detailed contract report with conditional sections",
        entity_def="kahua_Contract.Contract",
        
        sections=[
            create_title_section("{Number} - {Description}", order=0),
            
            create_header_section("Contract Information", order=1),
            create_field_grid_section([
                create_field("ContractorCompany.ShortLabel", "Contractor"),
                create_field("WorkflowStatus", "Status"),
                create_field("Type", "Type"),
                create_field("CurrencyCode", "Currency"),
            ], columns=2, order=2),
            
            create_header_section("Financial Summary", order=3),
            create_field_grid_section([
                create_field("OriginalContractValue", "Original Contract Value", DefFieldFormat.CURRENCY),
                create_field("ContractApprovedTotalValue", "Approved Total", DefFieldFormat.CURRENCY),
                create_field("ContractPendingTotalValue", "Pending Changes", DefFieldFormat.CURRENCY),
                create_field("BalanceToFinishAmount", "Balance to Finish", DefFieldFormat.CURRENCY),
            ], columns=2, order=4),
            
            # Conditional scope section - only shows if ScopeOfWork exists
            create_header_section(
                "Scope of Work", 
                order=5,
                condition=Condition("ScopeOfWork", "not_empty")
            ),
            create_text_section(
                "{ScopeOfWork}", 
                order=6,
                condition=Condition("ScopeOfWork", "not_empty")
            ),
            
            # Conditional change orders table
            create_header_section(
                "Change Orders",
                order=7,
                condition=Condition("ChangeOrders", "not_empty")
            ),
            create_table_section(
                source="ChangeOrders",
                columns=[
                    create_column("Number", "CO Number"),
                    create_column("Description", "Description"),
                    create_column("ApprovedAmount", "Amount", DefFieldFormat.CURRENCY, DefAlignment.RIGHT),
                    create_column("Status", "Status", DefFieldFormat.TEXT, DefAlignment.CENTER),
                ],
                order=8,
                condition=Condition("ChangeOrders", "not_empty"),
                totals=["ApprovedAmount"]
            ),
        ],
        
        theme=ThemeDef(
            primary_color="#0f172a",
            secondary_color="#0369a1",
        ),
        
        show_page_numbers=True,
    )
    
    path, _ = render_template(template, SAMPLE_CONTRACT, filename="example5_conditional.docx")
    print(f"  Created: {path}")
    
    # Test with data missing scope - shows conditional hiding
    no_scope_data = {**SAMPLE_CONTRACT, "ScopeOfWork": None, "ChangeOrders": []}
    path2, _ = render_template(template, no_scope_data, filename="example5_no_scope.docx")
    print(f"  Created (no scope/COs): {path2}")
    
    return path


def example_6_list_templates():
    """
    Example 6: Listing and querying templates.
    """
    print("Example 6: Template registry operations")
    
    registry = get_registry()
    
    # List all templates
    all_templates = registry.list_all()
    print(f"  Total templates: {len(all_templates)}")
    
    # List by category
    cost_templates = registry.list_all(category="cost")
    print(f"  Cost templates: {len(cost_templates)}")
    
    # Search
    search_results = registry.list_all(search="contract")
    print(f"  Templates matching 'contract': {len(search_results)}")
    
    for t in all_templates[:5]:
        print(f"    - {t['id']}: {t['name']}")


def run_all_examples():
    """Run all examples."""
    print("=" * 60)
    print("Word Template System Examples")
    print("=" * 60)
    print()
    
    # Ensure output directory exists
    Path("reports").mkdir(exist_ok=True)
    
    example_1_builder_api()
    print()
    
    example_2_builtin_template()
    print()
    
    example_3_custom_template()
    print()
    
    example_4_quick_render()
    print()
    
    example_5_programmatic_template()
    print()
    
    example_6_list_templates()
    print()
    
    print("=" * 60)
    print("All examples completed!")
    print("Check the 'reports' directory for generated documents.")
    print("=" * 60)


if __name__ == "__main__":
    run_all_examples()
