"""
Change Order entity models for Kahua Portable View templates.
Entities: kahua_Cost.CostItem (Change Orders), PCO, CO, etc.
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
    Location,
    NotificationEntry,
    OutwardReference,
    SecondaryComment,
    WorkBreakdownItem,
    WorkflowInfo,
    WorkPackage,
)


class ChangeOrderLineItemModel(KahuaBaseModel):
    """Change order line item."""

    number: Optional[str] = None
    description: Optional[str] = None
    csi_code: Optional[CSICode] = Field(default=None, alias="CSICode")
    quantity: Optional[Decimal] = None
    unit_of_measure: Optional[str] = None
    unit_price: Optional[Decimal] = None
    amount: Optional[Decimal] = None
    cost_type: Optional[str] = None
    markup_percentage: Optional[Decimal] = None
    markup_amount: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    work_breakdown_item: Optional[WorkBreakdownItem] = None


class PotentialChangeOrderModel(KahuaBaseModel):
    """
    Potential Change Order (PCO) entity model.
    Entity Definition: kahua_Cost.CostItem (PCO type)
    """

    # Basic info
    number: Optional[str] = None
    subject: Optional[str] = None
    description: Optional[str] = None
    status: Optional[CostItemStatus] = None
    pco_type: Optional[str] = Field(default=None, alias="PCOType")
    
    # Dates
    date: Optional[DateType] = None
    created_date: Optional[DateType] = None
    submitted_date: Optional[DateType] = None
    due_date: Optional[DateType] = None
    response_date: Optional[DateType] = None
    decision_date: Optional[DateType] = None
    
    # Parties
    author: Optional[ContactFull] = None
    submitted_by: Optional[ContactFull] = None
    assigned_to: Optional[ContactFull] = None
    contractor: Optional[CompanyFull] = None
    responsible_party: Optional[CompanyFull] = None
    
    # Financial
    proposed_amount: Optional[Decimal] = None
    approved_amount: Optional[Decimal] = None
    rejected_amount: Optional[Decimal] = None
    cost_estimate: Optional[Decimal] = None
    contractor_quote: Optional[Decimal] = None
    owner_allowance: Optional[Decimal] = None
    
    # Time impact
    time_impact_days: Optional[int] = None
    proposed_time_extension: Optional[int] = None
    approved_time_extension: Optional[int] = None
    
    # Reason/cause
    reason: Optional[str] = None
    cause: Optional[str] = None
    responsibility: Optional[str] = None
    cost_code: Optional[str] = None
    
    # Related entities
    csi_code: Optional[CSICode] = Field(default=None, alias="CSICode")
    location: Optional[Location] = None
    work_package: Optional[WorkPackage] = None
    work_breakdown_item: Optional[WorkBreakdownItem] = None
    line_items: Optional[List[ChangeOrderLineItemModel]] = None
    
    # Source documents (what initiated the PCO)
    source_rfi: Optional[str] = Field(default=None, alias="SourceRFI")
    source_submittal: Optional[str] = None
    source_field_order: Optional[str] = None
    
    # Communications
    distribution: Optional[List[DistributionEntry]] = None
    notification: Optional[List[NotificationEntry]] = None
    comments: Optional[List[Comment]] = None
    secondary_comments: Optional[List[SecondaryComment]] = None
    
    # Files
    attachments: Optional[List[KahuaFile]] = None
    backup_documentation: Optional[List[KahuaFile]] = None
    
    # References
    outward_references: Optional[List[OutwardReference]] = None
    
    # Workflow
    workflow: Optional[WorkflowInfo] = None
    approval: Optional[ApprovalInfo] = None
    
    # Notes
    notes: Optional[str] = None
    internal_notes: Optional[str] = None
    
    # Universal lookups
    universal_lookup1: Optional[str] = None
    universal_lookup2: Optional[str] = None
    universal_lookup3: Optional[str] = None
    universal_lookup4: Optional[str] = None
    universal_lookup5: Optional[str] = None

    entity_def: str = Field(default="kahua_Cost.CostItem", exclude=True)


class ChangeOrderModel(KahuaBaseModel):
    """
    Change Order (CO) entity model.
    Entity Definition: kahua_Cost.CostItem (CO type)
    """

    # Basic info
    number: Optional[str] = None
    subject: Optional[str] = None
    description: Optional[str] = None
    status: Optional[CostItemStatus] = None
    change_order_type: Optional[str] = None
    
    # Dates
    date: Optional[DateType] = None
    created_date: Optional[DateType] = None
    submitted_date: Optional[DateType] = None
    executed_date: Optional[DateType] = None
    effective_date: Optional[DateType] = None
    
    # Parties
    author: Optional[ContactFull] = None
    submitted_by: Optional[ContactFull] = None
    contractor: Optional[CompanyFull] = None
    executed_by: Optional[ContactFull] = None
    
    # Financial
    original_contract_amount: Optional[Decimal] = None
    previous_changes: Optional[Decimal] = None
    this_change_amount: Optional[Decimal] = None
    new_contract_amount: Optional[Decimal] = None
    net_change: Optional[Decimal] = None
    
    # Time impact
    original_completion_date: Optional[DateType] = None
    previous_time_extensions: Optional[int] = None
    this_time_extension: Optional[int] = None
    new_completion_date: Optional[DateType] = None
    
    # Related entities
    contract: Optional[str] = None  # Reference to contract
    included_pcos: Optional[List[PotentialChangeOrderModel]] = Field(default=None, alias="IncludedPCOs")
    line_items: Optional[List[ChangeOrderLineItemModel]] = None
    csi_code: Optional[CSICode] = Field(default=None, alias="CSICode")
    location: Optional[Location] = None
    work_package: Optional[WorkPackage] = None
    work_breakdown_item: Optional[WorkBreakdownItem] = None
    
    # Communications
    distribution: Optional[List[DistributionEntry]] = None
    notification: Optional[List[NotificationEntry]] = None
    comments: Optional[List[Comment]] = None
    secondary_comments: Optional[List[SecondaryComment]] = None
    
    # Files
    attachments: Optional[List[KahuaFile]] = None
    executed_document: Optional[KahuaFile] = None
    
    # References
    outward_references: Optional[List[OutwardReference]] = None
    
    # Workflow
    workflow: Optional[WorkflowInfo] = None
    approval: Optional[ApprovalInfo] = None
    
    # Signatures
    contractor_signature: Optional[str] = None
    contractor_signature_date: Optional[DateType] = None
    owner_signature: Optional[str] = None
    owner_signature_date: Optional[DateType] = None
    architect_signature: Optional[str] = None
    architect_signature_date: Optional[DateType] = None
    
    # Notes
    notes: Optional[str] = None
    reason_for_change: Optional[str] = None
    
    # Universal lookups
    universal_lookup1: Optional[str] = None
    universal_lookup2: Optional[str] = None
    universal_lookup3: Optional[str] = None
    universal_lookup4: Optional[str] = None
    universal_lookup5: Optional[str] = None

    entity_def: str = Field(default="kahua_Cost.CostItem", exclude=True)


class OwnerChangeOrderModel(ChangeOrderModel):
    """Owner Change Order (OCO) - extends Change Order."""
    
    owner_co_number: Optional[str] = Field(default=None, alias="OwnerCONumber")
    owner_authorization_date: Optional[DateType] = None
    owner_authorized_by: Optional[ContactFull] = None
    
    entity_def: str = Field(default="kahua_Cost.CostItem", exclude=True)


class ConstructionChangeDirectiveModel(KahuaBaseModel):
    """
    Construction Change Directive (CCD) model.
    """

    number: Optional[str] = None
    subject: Optional[str] = None
    description: Optional[str] = None
    status: Optional[CostItemStatus] = None
    
    # Dates
    date: Optional[DateType] = None
    issued_date: Optional[DateType] = None
    
    # Financial
    estimated_cost: Optional[Decimal] = None
    not_to_exceed: Optional[Decimal] = None
    final_cost: Optional[Decimal] = None
    
    # Time impact
    estimated_time_impact: Optional[int] = None
    
    # Method of adjustment
    adjustment_method: Optional[str] = None  # Lump Sum, Unit Prices, Time & Materials
    
    # Parties
    issued_by: Optional[ContactFull] = None
    contractor: Optional[CompanyFull] = None
    
    # Related entities
    change_order: Optional[ChangeOrderModel] = None  # Resulting CO
    attachments: Optional[List[KahuaFile]] = None
    
    # Notes
    notes: Optional[str] = None
    work_description: Optional[str] = None

    entity_def: str = Field(default="kahua_Cost.ConstructionChangeDirective", exclude=True)


def _rebuild_models() -> None:
    """Rebuild models to resolve forward references."""
    models = [
        ChangeOrderLineItemModel,
        PotentialChangeOrderModel,
        ChangeOrderModel,
        OwnerChangeOrderModel,
        ConstructionChangeDirectiveModel,
    ]
    for model in models:
        if hasattr(model, "model_rebuild"):
            model.model_rebuild()


_rebuild_models()
