"""
Invoice entity models for Kahua Portable View templates.
Entities: kahua_Cost.CostItem (Invoice type)
"""

from __future__ import annotations

from datetime import date as DateType, datetime as DateTimeType
from decimal import Decimal
from typing import List, Optional

from pydantic import Field

from .common import (
    ApprovalInfo,
    Comment,
    CompanyFull,
    ContactFull,
    CostItemStatus,
    CSICode,
    DistributionEntry,
    KahuaBaseModel,
    KahuaFile,
    NotificationEntry,
    OutwardReference,
    SecondaryComment,
    WorkBreakdownItem,
    WorkflowInfo,
)


class InvoiceLineItemModel(KahuaBaseModel):
    """Invoice line item."""

    number: Optional[str] = None
    description: Optional[str] = None
    quantity: Optional[Decimal] = None
    unit_of_measure: Optional[str] = None
    unit_price: Optional[Decimal] = None
    amount: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    csi_code: Optional[CSICode] = Field(default=None, alias="CSICode")
    work_breakdown_item: Optional[WorkBreakdownItem] = None
    account_code: Optional[str] = None
    cost_code: Optional[str] = None


class InvoiceModel(KahuaBaseModel):
    """
    Invoice entity model.
    Entity Definition: kahua_Cost.CostItem (Invoice type)
    """

    # Basic info
    number: Optional[str] = None
    invoice_number: Optional[str] = None
    vendor_invoice_number: Optional[str] = None
    subject: Optional[str] = None
    description: Optional[str] = None
    status: Optional[CostItemStatus] = None
    invoice_type: Optional[str] = None
    
    # Dates
    date: Optional[DateType] = None
    invoice_date: Optional[DateType] = None
    received_date: Optional[DateType] = None
    due_date: Optional[DateType] = None
    approved_date: Optional[DateType] = None
    paid_date: Optional[DateType] = None
    posted_date: Optional[DateType] = None
    
    # Parties
    vendor: Optional[CompanyFull] = None
    vendor_contact: Optional[ContactFull] = None
    submitted_by: Optional[ContactFull] = None
    approved_by: Optional[ContactFull] = None
    
    # Related contract/PO
    contract_number: Optional[str] = None
    purchase_order_number: Optional[str] = None
    
    # Financial
    subtotal: Optional[Decimal] = None
    discount_amount: Optional[Decimal] = None
    discount_percentage: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    tax_rate: Optional[Decimal] = None
    shipping_amount: Optional[Decimal] = None
    other_charges: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    amount_due: Optional[Decimal] = None
    amount_paid: Optional[Decimal] = None
    balance_due: Optional[Decimal] = None
    
    # Retainage
    retainage_amount: Optional[Decimal] = None
    retainage_rate: Optional[Decimal] = None
    
    # Payment info
    payment_terms: Optional[str] = None
    payment_method: Optional[str] = None
    check_number: Optional[str] = None
    wire_reference: Optional[str] = None
    
    # GL coding
    gl_account: Optional[str] = None
    cost_center: Optional[str] = None
    
    # Line items
    line_items: Optional[List[InvoiceLineItemModel]] = None
    
    # Communications
    distribution: Optional[List[DistributionEntry]] = None
    notification: Optional[List[NotificationEntry]] = None
    comments: Optional[List[Comment]] = None
    secondary_comments: Optional[List[SecondaryComment]] = None
    
    # Files
    attachments: Optional[List[KahuaFile]] = None
    invoice_document: Optional[KahuaFile] = None
    
    # References
    outward_references: Optional[List[OutwardReference]] = None
    
    # Workflow
    workflow: Optional[WorkflowInfo] = None
    approval: Optional[ApprovalInfo] = None
    
    # Notes
    notes: Optional[str] = None
    payment_notes: Optional[str] = None
    
    # Flags
    is_recurring: Optional[bool] = None
    is_paid: Optional[bool] = None
    is_voided: Optional[bool] = None
    
    # Universal lookups
    universal_lookup1: Optional[str] = None
    universal_lookup2: Optional[str] = None
    universal_lookup3: Optional[str] = None
    universal_lookup4: Optional[str] = None
    universal_lookup5: Optional[str] = None

    entity_def: str = Field(default="kahua_Cost.CostItem", exclude=True)


class VendorInvoiceModel(InvoiceModel):
    """Vendor invoice (extends Invoice)."""
    
    vendor_po_reference: Optional[str] = None
    three_way_match_status: Optional[str] = None
    
    entity_def: str = Field(default="kahua_Cost.VendorInvoice", exclude=True)


class CreditMemoModel(KahuaBaseModel):
    """Credit memo model."""

    number: Optional[str] = None
    credit_memo_number: Optional[str] = None
    date: Optional[DateType] = None
    vendor: Optional[CompanyFull] = None
    amount: Optional[Decimal] = None
    reason: Optional[str] = None
    description: Optional[str] = None
    related_invoice: Optional[str] = None
    status: Optional[CostItemStatus] = None
    attachments: Optional[List[KahuaFile]] = None
    notes: Optional[str] = None

    entity_def: str = Field(default="kahua_Cost.CreditMemo", exclude=True)


def _rebuild_models() -> None:
    """Rebuild models to resolve forward references."""
    models = [InvoiceLineItemModel, InvoiceModel, VendorInvoiceModel, CreditMemoModel]
    for model in models:
        if hasattr(model, "model_rebuild"):
            model.model_rebuild()


_rebuild_models()
