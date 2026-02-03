"""
Invoice entity model for Kahua Portable View templates.

Represents invoices/payment applications with line items, retainage,
and approval workflow for construction payment processing.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import Field

from report_genius.models.common import (
    Comment,
    ContactFull,
    CostCodeIndex,
    CostItemIndex,
    DistributionEntry,
    KahuaBaseModel,
    NotificationEntry,
    OutwardReference,
    WorkBreakdownItem,
)

JSONDict = Dict[str, Any]


class InvoiceItem(KahuaBaseModel):
    """Line item within an invoice."""

    # Identification
    number: Optional[str] = None
    description: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None

    # Classification
    work_breakdown_item: Optional[WorkBreakdownItem] = None
    cost_item_index: Optional[CostItemIndex] = None
    cost_code_index_01: Optional[CostCodeIndex] = Field(default=None, alias="CostCodeIndex_01")
    cost_code_index_02: Optional[CostCodeIndex] = Field(default=None, alias="CostCodeIndex_02")
    cost_code_index_03: Optional[CostCodeIndex] = Field(default=None, alias="CostCodeIndex_03")

    # Contract Values
    scheduled_value: Optional[Decimal] = None
    contract_quantity: Optional[Decimal] = None
    contract_unit_value: Optional[Decimal] = None
    contract_total_value: Optional[Decimal] = None

    # Previous Billing
    previous_quantity: Optional[Decimal] = None
    previous_total_value: Optional[Decimal] = None
    previous_percent_complete: Optional[Decimal] = None

    # Current Billing
    current_quantity: Optional[Decimal] = None
    current_total_value: Optional[Decimal] = None
    current_percent_complete: Optional[Decimal] = None

    # Totals
    total_completed_quantity: Optional[Decimal] = None
    total_completed_value: Optional[Decimal] = None
    total_percent_complete: Optional[Decimal] = None
    balance_to_finish: Optional[Decimal] = None

    # Retainage
    retainage_rate: Optional[Decimal] = None
    retainage_amount: Optional[Decimal] = None
    previous_retainage: Optional[Decimal] = None
    current_retainage: Optional[Decimal] = None
    total_retainage: Optional[Decimal] = None
    retainage_released: Optional[Decimal] = None

    # Stored Materials
    stored_materials_previous: Optional[Decimal] = None
    stored_materials_current: Optional[Decimal] = None
    stored_materials_total: Optional[Decimal] = None

    # Tax
    is_taxable: Optional[bool] = None
    tax_rate: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None


class InvoiceModel(KahuaBaseModel):
    """
    Invoice/Payment Application entity for construction billing.

    Tracks payment applications with line items, retainage calculations,
    stored materials, and approval workflow.
    """

    # Entity Definition (for template generator)
    entity_def: str = Field(default="kahua.invoice", exclude=True)

    # Identification
    number: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    type_: Optional[str] = Field(default=None, alias="Type")

    # Related Contract
    contract: Optional[JSONDict] = None
    contract_number: Optional[str] = None

    # Key Dates
    date: Optional[date] = None
    period_from: Optional[date] = None
    period_to: Optional[date] = None
    date_submitted: Optional[date] = None
    date_approved: Optional[date] = None
    date_paid: Optional[date] = None
    due_date: Optional[date] = None

    # Vendor/Contractor Info
    contractor_company: Optional[JSONDict] = None
    contractor_contact: Optional[ContactFull] = None
    vendor_invoice_number: Optional[str] = None
    vendor_invoice_date: Optional[date] = None

    # Line Items
    items: Optional[List[InvoiceItem]] = None

    # Summary - Contract
    original_contract_amount: Optional[Decimal] = None
    approved_changes_amount: Optional[Decimal] = None
    current_contract_amount: Optional[Decimal] = None

    # Summary - Billing
    total_scheduled_value: Optional[Decimal] = None
    previous_applications_total: Optional[Decimal] = None
    current_payment_due: Optional[Decimal] = None
    total_completed_to_date: Optional[Decimal] = None
    balance_to_finish: Optional[Decimal] = None
    percent_complete: Optional[Decimal] = None

    # Retainage
    retainage_rate: Optional[Decimal] = None
    previous_retainage_total: Optional[Decimal] = None
    current_retainage: Optional[Decimal] = None
    total_retainage_held: Optional[Decimal] = None
    retainage_released: Optional[Decimal] = None
    net_retainage: Optional[Decimal] = None

    # Stored Materials
    stored_materials_previous: Optional[Decimal] = None
    stored_materials_current: Optional[Decimal] = None
    stored_materials_total: Optional[Decimal] = None

    # Tax
    tax_total: Optional[Decimal] = None
    taxable_amount: Optional[Decimal] = None
    non_taxable_amount: Optional[Decimal] = None

    # Net Payment
    gross_amount_due: Optional[Decimal] = None
    less_retainage: Optional[Decimal] = None
    net_amount_due: Optional[Decimal] = None

    # Currency
    currency_code: Optional[str] = None
    currency_rate_to_domain: Optional[Decimal] = None

    # Notes & Comments
    notes: Optional[str] = None
    comments: Optional[List[Comment]] = None

    # Custom Fields
    custom_text1: Optional[str] = None
    custom_text2: Optional[str] = None
    custom_text3: Optional[str] = None
    custom_text4: Optional[str] = None
    custom_text5: Optional[str] = None
    custom_date1: Optional[date] = None
    custom_date2: Optional[date] = None
    custom_date3: Optional[date] = None
    custom_date4: Optional[date] = None
    custom_date5: Optional[date] = None
    custom_contact1: Optional[ContactFull] = None
    custom_contact2: Optional[ContactFull] = None
    custom_contact3: Optional[ContactFull] = None
    custom_lookup1: Optional[str] = None
    custom_lookup2: Optional[str] = None
    custom_lookup3: Optional[str] = None

    # References
    outward_references: Optional[List[OutwardReference]] = None

    # Distribution
    distribution: Optional[List[DistributionEntry]] = None
    notification: Optional[List[NotificationEntry]] = None


def _rebuild_models() -> None:
    """Rebuild models to resolve forward references."""
    models = [
        InvoiceItem,
        InvoiceModel,
    ]
    for model in models:
        if hasattr(model, "model_rebuild"):
            model.model_rebuild()


_rebuild_models()
