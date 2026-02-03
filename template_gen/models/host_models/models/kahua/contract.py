"""
Contract entity models for Kahua Portable View templates.
Entities: kahua_Contract.Contract and related
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


class ContractLineItemModel(KahuaBaseModel):
    """Contract line item/schedule of values item."""

    number: Optional[str] = None
    description: Optional[str] = None
    unit_of_measure: Optional[str] = None
    quantity: Optional[Decimal] = None
    unit_price: Optional[Decimal] = None
    amount: Optional[Decimal] = None
    completed_to_date: Optional[Decimal] = None
    stored_materials: Optional[Decimal] = None
    total_completed_and_stored: Optional[Decimal] = None
    percent_complete: Optional[Decimal] = None
    balance_to_finish: Optional[Decimal] = None
    retainage: Optional[Decimal] = None
    csi_code: Optional[CSICode] = Field(default=None, alias="CSICode")
    work_breakdown_item: Optional[WorkBreakdownItem] = None


class ContractModel(KahuaBaseModel):
    """
    Contract entity model.
    Entity Definition: kahua_Contract.Contract
    """

    # Basic info
    number: Optional[str] = None
    subject: Optional[str] = None
    description: Optional[str] = None
    contract_type: Optional[str] = None
    status: Optional[CostItemStatus] = None
    
    # Dates
    date: Optional[DateType] = None
    effective_date: Optional[DateType] = None
    execution_date: Optional[DateType] = None
    start_date: Optional[DateType] = None
    end_date: Optional[DateType] = None
    completion_date: Optional[DateType] = None
    expiration_date: Optional[DateType] = None
    warranty_expiration_date: Optional[DateType] = None
    
    # Parties
    contractor: Optional[CompanyFull] = None
    contractor_contact: Optional[ContactFull] = None
    subcontractor: Optional[CompanyFull] = None
    vendor: Optional[CompanyFull] = None
    responsible_contact: Optional[ContactFull] = None
    project_manager: Optional[ContactFull] = None
    
    # Financial
    original_contract_amount: Optional[Decimal] = None
    current_contract_amount: Optional[Decimal] = None
    approved_changes: Optional[Decimal] = None
    pending_changes: Optional[Decimal] = None
    revised_contract_amount: Optional[Decimal] = None
    billed_to_date: Optional[Decimal] = None
    paid_to_date: Optional[Decimal] = None
    retainage_held: Optional[Decimal] = None
    retainage_percentage: Optional[Decimal] = None
    balance_to_finish: Optional[Decimal] = None
    
    # Allowances
    allowance_amount: Optional[Decimal] = None
    allowance_used: Optional[Decimal] = None
    allowance_balance: Optional[Decimal] = None
    
    # Insurance/bonding
    insurance_required: Optional[bool] = None
    insurance_expiration_date: Optional[DateType] = None
    bond_required: Optional[bool] = None
    bond_amount: Optional[Decimal] = None
    bond_expiration_date: Optional[DateType] = None
    
    # Related entities
    csi_code: Optional[CSICode] = Field(default=None, alias="CSICode")
    location: Optional[Location] = None
    work_package: Optional[WorkPackage] = None
    work_breakdown_item: Optional[WorkBreakdownItem] = None
    line_items: Optional[List[ContractLineItemModel]] = None
    
    # Communications
    distribution: Optional[List[DistributionEntry]] = None
    notification: Optional[List[NotificationEntry]] = None
    comments: Optional[List[Comment]] = None
    secondary_comments: Optional[List[SecondaryComment]] = None
    
    # Files
    attachments: Optional[List[KahuaFile]] = None
    executed_contract: Optional[KahuaFile] = None
    
    # References
    outward_references: Optional[List[OutwardReference]] = None
    parent_contract: Optional[ContractModel] = None
    
    # Workflow
    workflow: Optional[WorkflowInfo] = None
    approval: Optional[ApprovalInfo] = None
    
    # Notes
    notes: Optional[str] = None
    terms_and_conditions: Optional[str] = None
    scope_of_work: Optional[str] = None
    
    # Universal lookups
    universal_lookup1: Optional[str] = None
    universal_lookup2: Optional[str] = None
    universal_lookup3: Optional[str] = None
    universal_lookup4: Optional[str] = None
    universal_lookup5: Optional[str] = None

    entity_def: str = Field(default="kahua_Contract.Contract", exclude=True)


class SubcontractModel(ContractModel):
    """
    Subcontract entity model (extends Contract).
    """

    prime_contract: Optional[ContractModel] = None
    scope_description: Optional[str] = None
    
    entity_def: str = Field(default="kahua_Contract.Subcontract", exclude=True)


class PurchaseOrderModel(KahuaBaseModel):
    """
    Purchase order entity model.
    """

    number: Optional[str] = None
    subject: Optional[str] = None
    description: Optional[str] = None
    status: Optional[CostItemStatus] = None
    
    # Dates
    date: Optional[DateType] = None
    required_date: Optional[DateType] = None
    delivery_date: Optional[DateType] = None
    
    # Parties
    vendor: Optional[CompanyFull] = None
    vendor_contact: Optional[ContactFull] = None
    ship_to_contact: Optional[ContactFull] = None
    ship_to_address: Optional[str] = None
    
    # Financial
    subtotal: Optional[Decimal] = None
    tax: Optional[Decimal] = None
    shipping: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    
    # Related entities
    contract: Optional[ContractModel] = None
    line_items: Optional[List[ContractLineItemModel]] = None
    
    # Files
    attachments: Optional[List[KahuaFile]] = None
    
    # Notes
    notes: Optional[str] = None
    shipping_instructions: Optional[str] = None

    entity_def: str = Field(default="kahua_Contract.PurchaseOrder", exclude=True)


def _rebuild_models() -> None:
    """Rebuild models to resolve forward references."""
    models = [ContractLineItemModel, ContractModel, SubcontractModel, PurchaseOrderModel]
    for model in models:
        if hasattr(model, "model_rebuild"):
            model.model_rebuild()


_rebuild_models()
