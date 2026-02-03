"""
Expense Change Order entity model for Kahua Portable View templates.

Represents change orders against expense contracts with line items,
cost tracking, and approval workflow.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import AnyUrl, Field

from report_genius.models.common import (
    KahuaBaseModel,
    Comment,
    ContactFull,
    CostCodeIndex,
    CostItemIndex,
    DistributionEntry,
    Location,
    NotificationEntry,
    OutwardReference,
    WorkBreakdownItem,
)

JSONDict = Dict[str, Any]


# -----------------------------------------------------------------------------
# Change Order Item
# -----------------------------------------------------------------------------


class ChangeOrderItem(KahuaBaseModel):
    """Line item within a change order."""

    # Currency & Exchange
    currency_code: Optional[str] = None
    currency_rate_id: Optional[int] = None
    currency_rate_to_domain: Optional[Decimal] = None
    currency_rate_to_document: Optional[Decimal] = None
    currency_rate_type_id: Optional[int] = None

    # Accounting
    accounting_completed_on: Optional[date] = None
    accounting_started_on: Optional[date] = None

    # Classification
    change_reason: Optional[str] = None
    work_breakdown_item: Optional[WorkBreakdownItem] = None
    cost_item_index: Optional[CostItemIndex] = None
    cost_code_index_01: Optional[CostCodeIndex] = Field(default=None, alias="CostCodeIndex_01")
    cost_code_index_02: Optional[CostCodeIndex] = Field(default=None, alias="CostCodeIndex_02")
    cost_code_index_03: Optional[CostCodeIndex] = Field(default=None, alias="CostCodeIndex_03")
    domain_cost_code_index_01: Optional[CostCodeIndex] = Field(
        default=None, alias="DomainCostCodeIndex_01"
    )

    # Current Cost Values
    cost_current_quantity: Optional[Decimal] = None
    cost_current_total_value: Optional[Decimal] = None
    cost_current_tax_rate: Optional[Decimal] = None
    cost_current_unit_of_measurement: Optional[str] = None
    cost_current_unit_value: Optional[Decimal] = None

    # Projected Values
    contract_change_order_projected_quantity: Optional[Decimal] = None
    contract_change_order_projected_total_value: Optional[Decimal] = None
    contract_change_order_projected_unit_of_measurement: Optional[str] = None
    contract_change_order_projected_unit_value: Optional[Decimal] = None
    contract_change_order_projected_tax_rate: Optional[Decimal] = None

    # Pending Values
    contract_change_order_pending_quantity: Optional[Decimal] = None
    contract_change_order_pending_total_value: Optional[Decimal] = None
    contract_change_order_pending_unit_of_measurement: Optional[str] = None
    contract_change_order_pending_unit_value: Optional[Decimal] = None
    contract_change_order_pending_tax_rate: Optional[Decimal] = None

    # Approved Values
    contract_change_order_approved_quantity: Optional[Decimal] = None
    contract_change_order_approved_total_value: Optional[Decimal] = None
    contract_change_order_approved_unit_of_measurement: Optional[str] = None
    contract_change_order_approved_unit_value: Optional[Decimal] = None
    contract_change_order_approved_tax_rate: Optional[Decimal] = None

    # Descriptive
    description: Optional[str] = None
    notes: Optional[str] = None
    scope_of_work: Optional[str] = None
    number: Optional[str] = None
    status: Optional[str] = None

    # Schedule
    schedule_end: Optional[date] = None
    schedule_start: Optional[date] = None
    committed_date: Optional[date] = None

    # Comments & References
    comments: Optional[List[Comment]] = None
    outward_references: Optional[List[OutwardReference]] = None
    external_links: Optional[List[JSONDict]] = None

    # Funding Linkage
    client_contract_change_order: Optional[JSONDict] = None
    client_contract_change_order_item: Optional[JSONDict] = None


# -----------------------------------------------------------------------------
# Expense Change Order Model
# -----------------------------------------------------------------------------


class ExpenseChangeOrderModel(KahuaBaseModel):
    """
    Expense Change Order entity for contract modifications.

    Tracks changes to expense contracts including cost adjustments,
    time extensions, and scope modifications with full approval workflow.
    """

    # Entity Definition (for template generator)
    entity_def: str = Field(default="kahua.expensechangeorder", exclude=True)

    # Identification
    number: Optional[str] = None
    description: Optional[str] = None
    type_: Optional[str] = Field(default=None, alias="Type")
    status: Optional[str] = None
    task_status: Optional[str] = None

    # Related Contract
    contract: Optional[JSONDict] = None
    contract_extension: Optional[Decimal] = None

    # Currency
    currency_code: Optional[str] = None
    currency_rate_id: Optional[int] = None
    currency_rate_to_domain: Optional[Decimal] = None
    currency_rate_to_document: Optional[Decimal] = None
    currency_rate_type_id: Optional[int] = None
    cost_unit_entry_type: Optional[str] = None
    tax_entry_type: Optional[str] = None

    # Key Dates
    date: Optional[date] = None
    date_executed: Optional[date] = None
    date_approved: Optional[date] = None
    internally_approved_date: Optional[date] = None
    board_agenda_date: Optional[date] = None
    revised_completion_date: Optional[date] = None

    # Location
    location: Optional[Location] = None

    # Scope
    scope_of_work: Optional[str] = None
    bid_package_no: Optional[str] = None
    issue_item: Optional[JSONDict] = None

    # Line Items
    items: Optional[List[ChangeOrderItem]] = None

    # Totals - Current
    cost_current_quantity: Optional[Decimal] = None
    cost_current_total_value: Optional[Decimal] = None
    cost_current_unit_of_measurement: Optional[str] = None
    cost_current_unit_value: Optional[Decimal] = None

    # Totals - By Status
    contract_change_order_projected_total_value: Optional[Decimal] = None
    contract_change_order_pending_total_value: Optional[Decimal] = None
    contract_change_order_approved_total_value: Optional[Decimal] = None

    # Totals - Aggregate
    cost_items_total_total_value: Optional[Decimal] = None
    cost_items_tax_total_total_value: Optional[Decimal] = None
    cost_items_non_tax_total_total_value: Optional[Decimal] = None

    # Contract Summary Values
    original_contract_amount: Optional[Decimal] = None
    approved_changes_amount: Optional[Decimal] = None
    pending_changes_amount: Optional[Decimal] = None
    current_contract_amount: Optional[Decimal] = None
    current_contract_plus_pending_changes_amount: Optional[Decimal] = None
    contract_gross_total_amount: Optional[Decimal] = None
    previously_approved_changes_amount: Optional[Decimal] = None
    previous_contract_amount: Optional[Decimal] = None
    new_contract_amount: Optional[Decimal] = None
    previously_executed_changes_amount: Optional[Decimal] = None
    previously_executed_contract_amount: Optional[Decimal] = None
    executed_changes_amount: Optional[Decimal] = None
    executed_changes_contract_amount: Optional[Decimal] = None
    new_executed_contract_amount: Optional[Decimal] = None

    # Contacts
    bond_director: Optional[ContactFull] = None
    custom_contact1: Optional[ContactFull] = None
    custom_contact2: Optional[ContactFull] = None
    custom_contact3: Optional[ContactFull] = None
    custom_contact4: Optional[ContactFull] = None
    custom_contact5: Optional[ContactFull] = None

    # Custom Fields - Text
    custom_text1: Optional[str] = None
    custom_text2: Optional[str] = None
    custom_text3: Optional[str] = None
    custom_text4: Optional[str] = None
    custom_text5: Optional[str] = None

    # Custom Fields - Dates
    custom_date1: Optional[date] = None
    custom_date2: Optional[date] = None
    custom_date3: Optional[date] = None
    custom_date4: Optional[date] = None
    custom_date5: Optional[date] = None

    # Custom Fields - Unlimited Text
    custom_unlimited_text1: Optional[str] = None
    custom_unlimited_text2: Optional[str] = None
    custom_unlimited_text3: Optional[str] = None
    custom_unlimited_text4: Optional[str] = None
    custom_unlimited_text5: Optional[str] = None

    # Custom Fields - Lookups
    custom_lookup1: Optional[str] = None
    custom_lookup2: Optional[str] = None
    custom_lookup3: Optional[str] = None
    custom_lookup4: Optional[str] = None
    custom_lookup5: Optional[str] = None

    # Notes & Comments
    notes: Optional[str] = None
    comments: Optional[List[Comment]] = None

    # References
    outward_references: Optional[List[OutwardReference]] = None

    # Distribution
    distribution: Optional[List[DistributionEntry]] = None
    notification: Optional[List[NotificationEntry]] = None


# -----------------------------------------------------------------------------
# Forward Reference Resolution
# -----------------------------------------------------------------------------


def _rebuild_models() -> None:
    """Rebuild models to resolve forward references."""
    models = [
        ChangeOrderItem,
        ExpenseChangeOrderModel,
    ]
    for model in models:
        if hasattr(model, "model_rebuild"):
            model.model_rebuild()


_rebuild_models()
