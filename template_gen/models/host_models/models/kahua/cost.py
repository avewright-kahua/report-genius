"""
Cost management entity models for Kahua Portable View templates.
Entities: kahua_Cost.CostItem, Budget, Commitment, etc.
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
    WorkBreakdownSegment,
    WorkflowInfo,
)


class BudgetLineItemModel(KahuaBaseModel):
    """Budget line item."""

    number: Optional[str] = None
    description: Optional[str] = None
    cost_code: Optional[str] = None
    csi_code: Optional[CSICode] = Field(default=None, alias="CSICode")
    work_breakdown_item: Optional[WorkBreakdownItem] = None
    segments: Optional[List[WorkBreakdownSegment]] = None
    
    # Amounts
    original_budget: Optional[Decimal] = None
    budget_transfers_in: Optional[Decimal] = None
    budget_transfers_out: Optional[Decimal] = None
    revised_budget: Optional[Decimal] = None
    
    # Commitments
    committed_costs: Optional[Decimal] = None
    pending_commitments: Optional[Decimal] = None
    
    # Actual costs
    actual_costs: Optional[Decimal] = None
    
    # Forecast
    forecast_to_complete: Optional[Decimal] = None
    estimate_at_completion: Optional[Decimal] = None
    variance: Optional[Decimal] = None
    variance_percentage: Optional[Decimal] = None


class BudgetModel(KahuaBaseModel):
    """
    Budget entity model.
    Entity Definition: kahua_WorkBreakdown.Budget
    """

    # Basic info
    name: Optional[str] = None
    number: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    budget_type: Optional[str] = None
    
    # Dates
    effective_date: Optional[DateType] = None
    approved_date: Optional[DateType] = None
    
    # Summary amounts
    total_original_budget: Optional[Decimal] = None
    total_revised_budget: Optional[Decimal] = None
    total_committed: Optional[Decimal] = None
    total_actual: Optional[Decimal] = None
    total_forecast: Optional[Decimal] = None
    total_variance: Optional[Decimal] = None
    
    # Line items
    line_items: Optional[List[BudgetLineItemModel]] = None
    
    # Related
    approved_by: Optional[ContactFull] = None
    attachments: Optional[List[KahuaFile]] = None
    notes: Optional[str] = None

    entity_def: str = Field(default="kahua_WorkBreakdown.Budget", exclude=True)


class BudgetTransferModel(KahuaBaseModel):
    """Budget transfer model."""

    number: Optional[str] = None
    subject: Optional[str] = None
    description: Optional[str] = None
    status: Optional[CostItemStatus] = None
    date: Optional[DateType] = None
    
    # Transfer details
    from_budget_line: Optional[BudgetLineItemModel] = None
    to_budget_line: Optional[BudgetLineItemModel] = None
    amount: Optional[Decimal] = None
    
    # Approval
    requested_by: Optional[ContactFull] = None
    approved_by: Optional[ContactFull] = None
    approved_date: Optional[DateType] = None
    
    # Files
    attachments: Optional[List[KahuaFile]] = None
    
    notes: Optional[str] = None
    reason: Optional[str] = None

    entity_def: str = Field(default="kahua_Cost.BudgetTransfer", exclude=True)


class CommitmentModel(KahuaBaseModel):
    """
    Commitment (contracted cost) model.
    Entity Definition: kahua_Cost.CostItem (Commitment type)
    """

    number: Optional[str] = None
    subject: Optional[str] = None
    description: Optional[str] = None
    status: Optional[CostItemStatus] = None
    commitment_type: Optional[str] = None  # Contract, PO, Subcontract
    
    # Dates
    date: Optional[DateType] = None
    effective_date: Optional[DateType] = None
    expiration_date: Optional[DateType] = None
    
    # Parties
    vendor: Optional[CompanyFull] = None
    contractor: Optional[CompanyFull] = None
    
    # Financial
    original_amount: Optional[Decimal] = None
    approved_changes: Optional[Decimal] = None
    pending_changes: Optional[Decimal] = None
    revised_amount: Optional[Decimal] = None
    invoiced_amount: Optional[Decimal] = None
    paid_amount: Optional[Decimal] = None
    remaining_amount: Optional[Decimal] = None
    
    # Related
    contract_number: Optional[str] = None
    csi_code: Optional[CSICode] = Field(default=None, alias="CSICode")
    work_breakdown_item: Optional[WorkBreakdownItem] = None
    
    # Files
    attachments: Optional[List[KahuaFile]] = None
    
    notes: Optional[str] = None

    entity_def: str = Field(default="kahua_Cost.CostItem", exclude=True)


class CostSummaryModel(KahuaBaseModel):
    """Cost summary/report model."""

    # Budget
    original_budget: Optional[Decimal] = None
    budget_adjustments: Optional[Decimal] = None
    revised_budget: Optional[Decimal] = None
    
    # Commitments
    original_commitments: Optional[Decimal] = None
    approved_changes: Optional[Decimal] = None
    pending_changes: Optional[Decimal] = None
    revised_commitments: Optional[Decimal] = None
    
    # Actual costs
    actual_costs: Optional[Decimal] = None
    unbilled_costs: Optional[Decimal] = None
    
    # Projected
    estimated_cost_to_complete: Optional[Decimal] = None
    projected_final_cost: Optional[Decimal] = None
    
    # Variance
    budget_vs_committed_variance: Optional[Decimal] = None
    budget_vs_projected_variance: Optional[Decimal] = None
    committed_vs_projected_variance: Optional[Decimal] = None
    
    # Percentages
    percent_budget_committed: Optional[Decimal] = None
    percent_committed_invoiced: Optional[Decimal] = None
    percent_complete: Optional[Decimal] = None

    entity_def: str = Field(default="kahua_Cost.CostSummary", exclude=True)


class AllowanceModel(KahuaBaseModel):
    """
    Allowance entity model.
    Entity Definition: kahua_Allowances.Allowance
    """

    number: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    
    # Company
    company: Optional[CompanyFull] = None
    contract: Optional[str] = None
    
    # Amount tracking
    allowance_amount: Optional[Decimal] = None
    total_spent: Optional[Decimal] = None
    balance: Optional[Decimal] = None
    
    # Quantity tracking
    is_quantity_allowance: Optional[bool] = None
    quantity_allowance: Optional[Decimal] = None
    total_spent_quantity: Optional[Decimal] = None
    quantity_balance: Optional[Decimal] = None
    quantity_allowance_uom: Optional[str] = Field(default=None, alias="QuantityAllowanceUOM")
    
    # Items
    items: Optional[List[AllowanceItemModel]] = None
    
    # Related
    csi_code: Optional[CSICode] = Field(default=None, alias="CSICode")
    work_breakdown_item: Optional[WorkBreakdownItem] = None
    
    # Files
    attachments: Optional[List[KahuaFile]] = None
    
    notes: Optional[str] = None

    entity_def: str = Field(default="kahua_Allowances.Allowance", exclude=True)


class AllowanceItemModel(KahuaBaseModel):
    """Allowance item (draw against allowance)."""

    date: Optional[DateType] = None
    description: Optional[str] = None
    amount: Optional[Decimal] = None
    quantity: Optional[Decimal] = None
    parent_allowance: Optional[str] = None
    reference: Optional[str] = None
    notes: Optional[str] = None

    entity_def: str = Field(default="kahua_Allowances.AllowanceItem", exclude=True)


class FundingSourceModel(KahuaBaseModel):
    """
    Funding source model.
    Entity Definition: kahua_Funding.FundingSource
    """

    name: Optional[str] = None
    number: Optional[str] = None
    description: Optional[str] = None
    funding_type: Optional[str] = None
    status: Optional[str] = None
    
    # Amounts
    total_funding: Optional[Decimal] = None
    allocated_amount: Optional[Decimal] = None
    remaining_amount: Optional[Decimal] = None
    
    # Dates
    effective_date: Optional[DateType] = None
    expiration_date: Optional[DateType] = None
    
    # Related
    funding_agency: Optional[CompanyFull] = None
    
    notes: Optional[str] = None

    entity_def: str = Field(default="kahua_Funding.FundingSource", exclude=True)


def _rebuild_models() -> None:
    """Rebuild models to resolve forward references."""
    models = [
        BudgetLineItemModel,
        BudgetModel,
        BudgetTransferModel,
        CommitmentModel,
        CostSummaryModel,
        AllowanceModel,
        AllowanceItemModel,
        FundingSourceModel,
    ]
    for model in models:
        if hasattr(model, "model_rebuild"):
            model.model_rebuild()


_rebuild_models()
