"""
Pay Request / Pay Application entity models for Kahua Portable View templates.
Entities: kahua_Cost.CostItem (Pay Application type)
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


class PayRequestLineItemModel(KahuaBaseModel):
    """Pay request line item (Schedule of Values item)."""

    number: Optional[str] = None
    description: Optional[str] = None
    scheduled_value: Optional[Decimal] = None
    
    # Previous billing
    previous_applications: Optional[Decimal] = None
    previous_percent_complete: Optional[Decimal] = None
    
    # This period
    work_completed: Optional[Decimal] = None
    materials_stored: Optional[Decimal] = None
    total_completed_and_stored: Optional[Decimal] = None
    percent_complete: Optional[Decimal] = None
    
    # Retainage
    retainage_rate: Optional[Decimal] = None
    retainage_this_period: Optional[Decimal] = None
    retainage_released: Optional[Decimal] = None
    total_retainage: Optional[Decimal] = None
    
    # Balance
    balance_to_finish: Optional[Decimal] = None
    
    # Related
    csi_code: Optional[CSICode] = Field(default=None, alias="CSICode")
    work_breakdown_item: Optional[WorkBreakdownItem] = None


class PayRequestModel(KahuaBaseModel):
    """
    Pay Request / Pay Application entity model.
    Entity Definition: kahua_Cost.CostItem (Pay Application type)
    """

    # Basic info
    number: Optional[str] = None
    application_number: Optional[int] = None
    subject: Optional[str] = None
    description: Optional[str] = None
    status: Optional[CostItemStatus] = None
    pay_request_type: Optional[str] = None
    
    # Period
    period_from: Optional[DateType] = None
    period_to: Optional[DateType] = None
    application_date: Optional[DateType] = None
    
    # Dates
    date: Optional[DateType] = None
    submitted_date: Optional[DateType] = None
    received_date: Optional[DateType] = None
    certified_date: Optional[DateType] = None
    approved_date: Optional[DateType] = None
    paid_date: Optional[DateType] = None
    due_date: Optional[DateType] = None
    
    # Parties
    contractor: Optional[CompanyFull] = None
    contractor_contact: Optional[ContactFull] = None
    submitted_by: Optional[ContactFull] = None
    certified_by: Optional[ContactFull] = None
    approved_by: Optional[ContactFull] = None
    project_manager: Optional[ContactFull] = None
    
    # Contract info
    contract_number: Optional[str] = None
    contract_name: Optional[str] = None
    project_name: Optional[str] = None
    project_number: Optional[str] = None
    
    # Financial - Original Contract
    original_contract_sum: Optional[Decimal] = None
    
    # Financial - Changes
    change_orders_approved: Optional[Decimal] = None
    change_orders_approved_count: Optional[int] = None
    
    # Financial - Current Contract
    current_contract_sum: Optional[Decimal] = None
    
    # Financial - This Application
    total_completed_and_stored: Optional[Decimal] = None
    total_completed_this_period: Optional[Decimal] = None
    materials_stored_this_period: Optional[Decimal] = None
    
    # Financial - Retainage
    retainage_rate: Optional[Decimal] = None
    retainage_on_completed_work: Optional[Decimal] = None
    retainage_on_stored_materials: Optional[Decimal] = None
    total_retainage: Optional[Decimal] = None
    retainage_released: Optional[Decimal] = None
    retainage_released_this_period: Optional[Decimal] = None
    
    # Financial - Summary
    total_earned_less_retainage: Optional[Decimal] = None
    less_previous_certificates: Optional[Decimal] = None
    current_payment_due: Optional[Decimal] = None
    amount_requested: Optional[Decimal] = None
    amount_certified: Optional[Decimal] = None
    amount_approved: Optional[Decimal] = None
    amount_paid: Optional[Decimal] = None
    
    # Financial - Balance
    balance_to_finish: Optional[Decimal] = None
    percent_complete: Optional[Decimal] = None
    
    # Deductions
    deductions: Optional[Decimal] = None
    deduction_description: Optional[str] = None
    
    # Adjustments
    adjustments: Optional[Decimal] = None
    adjustment_description: Optional[str] = None
    
    # Line items
    line_items: Optional[List[PayRequestLineItemModel]] = None
    
    # Communications
    distribution: Optional[List[DistributionEntry]] = None
    notification: Optional[List[NotificationEntry]] = None
    comments: Optional[List[Comment]] = None
    secondary_comments: Optional[List[SecondaryComment]] = None
    
    # Files
    attachments: Optional[List[KahuaFile]] = None
    lien_waivers: Optional[List[KahuaFile]] = None
    certified_payroll: Optional[List[KahuaFile]] = None
    
    # References
    outward_references: Optional[List[OutwardReference]] = None
    
    # Workflow
    workflow: Optional[WorkflowInfo] = None
    approval: Optional[ApprovalInfo] = None
    
    # Certification
    architect_certification: Optional[str] = None
    architect_certification_date: Optional[DateType] = None
    notarized: Optional[bool] = None
    notary_date: Optional[DateType] = None
    
    # Notes
    notes: Optional[str] = None
    certification_notes: Optional[str] = None
    
    # Universal lookups
    universal_lookup1: Optional[str] = None
    universal_lookup2: Optional[str] = None
    universal_lookup3: Optional[str] = None
    universal_lookup4: Optional[str] = None
    universal_lookup5: Optional[str] = None
    
    # Flags
    is_final: Optional[bool] = None
    is_partial: Optional[bool] = None

    entity_def: str = Field(default="kahua_Cost.CostItem", exclude=True)


class LienWaiverModel(KahuaBaseModel):
    """Lien waiver model."""

    number: Optional[str] = None
    waiver_type: Optional[str] = None  # Conditional, Unconditional, Partial, Final
    date: Optional[DateType] = None
    through_date: Optional[DateType] = None
    amount: Optional[Decimal] = None
    contractor: Optional[CompanyFull] = None
    signed_by: Optional[ContactFull] = None
    signature_date: Optional[DateType] = None
    notarized: Optional[bool] = None
    notary_date: Optional[DateType] = None
    attachment: Optional[KahuaFile] = None
    pay_request: Optional[str] = None  # Reference to pay request

    entity_def: str = Field(default="kahua_Cost.LienWaiver", exclude=True)


def _rebuild_models() -> None:
    """Rebuild models to resolve forward references."""
    models = [PayRequestLineItemModel, PayRequestModel, LienWaiverModel]
    for model in models:
        if hasattr(model, "model_rebuild"):
            model.model_rebuild()


_rebuild_models()
