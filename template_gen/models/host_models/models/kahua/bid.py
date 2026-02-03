"""
Bid and procurement entity models for Kahua Portable View templates.
Entities: kahua_Bidding.Bid, BidPackage, Proposal
"""

from __future__ import annotations

from datetime import date, datetime, time
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
    WorkflowInfo,
)


class BidLineItemModel(KahuaBaseModel):
    """Bid line item/schedule of values item."""

    item_number: Optional[str] = Field(default=None, alias="ItemNumber")
    description: Optional[str] = Field(default=None, alias="Description")
    csi_code: Optional[CSICode] = Field(default=None, alias="CSICode")
    
    # Quantities
    quantity: Optional[float] = Field(default=None, alias="Quantity")
    unit: Optional[str] = Field(default=None, alias="Unit")
    
    # Pricing
    unit_price: Optional[Decimal] = Field(default=None, alias="UnitPrice")
    extended_price: Optional[Decimal] = Field(default=None, alias="ExtendedPrice")
    
    # Alternates
    is_base_bid: Optional[bool] = Field(default=None, alias="IsBaseBid")
    is_alternate: Optional[bool] = Field(default=None, alias="IsAlternate")
    alternate_number: Optional[str] = Field(default=None, alias="AlternateNumber")
    
    notes: Optional[str] = Field(default=None, alias="Notes")


class BidModel(KahuaBaseModel):
    """
    Bid entity model.
    Entity Definition: kahua_Bidding.Bid
    """

    # Identification
    number: Optional[str] = Field(default=None, alias="Number")
    bid_number: Optional[str] = Field(default=None, alias="BidNumber")
    subject: Optional[str] = Field(default=None, alias="Subject")
    description: Optional[str] = Field(default=None, alias="Description")
    
    # Status
    status: Optional[CostItemStatus] = Field(default=None, alias="Status")
    bid_status: Optional[str] = Field(default=None, alias="BidStatus")
    award_status: Optional[str] = Field(default=None, alias="AwardStatus")
    
    # Bidder
    bidder: Optional[CompanyFull] = Field(default=None, alias="Bidder")
    bidder_contact: Optional[ContactFull] = Field(default=None, alias="BidderContact")
    
    # Parent package
    bid_package: Optional[OutwardReference] = Field(default=None, alias="BidPackage")
    
    # Amounts
    base_bid_amount: Optional[Decimal] = Field(default=None, alias="BaseBidAmount")
    alternate_amount: Optional[Decimal] = Field(default=None, alias="AlternateAmount")
    total_bid_amount: Optional[Decimal] = Field(default=None, alias="TotalBidAmount")
    
    # Line items
    line_items: Optional[List[BidLineItemModel]] = Field(default=None, alias="LineItems")
    
    # Dates
    date_submitted: Optional[date] = Field(default=None, alias="DateSubmitted")
    date_received: Optional[date] = Field(default=None, alias="DateReceived")
    date_opened: Optional[date] = Field(default=None, alias="DateOpened")
    bid_valid_until: Optional[date] = Field(default=None, alias="BidValidUntil")
    
    # Evaluation
    is_responsive: Optional[bool] = Field(default=None, alias="IsResponsive")
    is_responsible: Optional[bool] = Field(default=None, alias="IsResponsible")
    evaluation_score: Optional[float] = Field(default=None, alias="EvaluationScore")
    rank: Optional[int] = Field(default=None, alias="Rank")
    is_recommended: Optional[bool] = Field(default=None, alias="IsRecommended")
    is_awarded: Optional[bool] = Field(default=None, alias="IsAwarded")
    
    # Bond info
    bid_bond_included: Optional[bool] = Field(default=None, alias="BidBondIncluded")
    bid_bond_amount: Optional[Decimal] = Field(default=None, alias="BidBondAmount")
    bid_bond_percent: Optional[float] = Field(default=None, alias="BidBondPercent")
    
    # Evaluation comments
    evaluation_comments: Optional[str] = Field(default=None, alias="EvaluationComments")
    exceptions: Optional[str] = Field(default=None, alias="Exceptions")
    clarifications: Optional[str] = Field(default=None, alias="Clarifications")
    
    # Attachments
    attachments: Optional[List[KahuaFile]] = Field(default=None, alias="Attachments")
    
    # Comments
    comments: Optional[List[Comment]] = Field(default=None, alias="Comments")
    
    notes: Optional[str] = Field(default=None, alias="Notes")

    entity_def: str = Field(default="kahua_Bidding.Bid", exclude=True)


class BidAlternateModel(KahuaBaseModel):
    """Bid alternate item."""

    alternate_number: Optional[str] = Field(default=None, alias="AlternateNumber")
    description: Optional[str] = Field(default=None, alias="Description")
    alternate_type: Optional[str] = Field(default=None, alias="AlternateType")  # Add, Deduct
    is_accepted: Optional[bool] = Field(default=None, alias="IsAccepted")
    notes: Optional[str] = Field(default=None, alias="Notes")


class BidPackageModel(KahuaBaseModel):
    """
    Bid package entity model.
    Entity Definition: kahua_Bidding.BidPackage
    """

    # Identification
    number: Optional[str] = Field(default=None, alias="Number")
    package_number: Optional[str] = Field(default=None, alias="PackageNumber")
    name: Optional[str] = Field(default=None, alias="Name")
    title: Optional[str] = Field(default=None, alias="Title")
    description: Optional[str] = Field(default=None, alias="Description")
    
    # Status
    status: Optional[CostItemStatus] = Field(default=None, alias="Status")
    package_status: Optional[str] = Field(default=None, alias="PackageStatus")
    
    # Classification
    package_type: Optional[str] = Field(default=None, alias="PackageType")
    procurement_method: Optional[str] = Field(default=None, alias="ProcurementMethod")
    discipline: Optional[str] = Field(default=None, alias="Discipline")
    csi_codes: Optional[List[CSICode]] = Field(default=None, alias="CSICodes")
    
    # Scope of work
    scope_of_work: Optional[str] = Field(default=None, alias="ScopeOfWork")
    
    # Estimate
    estimated_value: Optional[Decimal] = Field(default=None, alias="EstimatedValue")
    budget_amount: Optional[Decimal] = Field(default=None, alias="BudgetAmount")
    
    # Dates
    issue_date: Optional[date] = Field(default=None, alias="IssueDate")
    bid_due_date: Optional[date] = Field(default=None, alias="BidDueDate")
    bid_due_time: Optional[time] = Field(default=None, alias="BidDueTime")
    pre_bid_date: Optional[date] = Field(default=None, alias="PreBidDate")
    site_visit_date: Optional[date] = Field(default=None, alias="SiteVisitDate")
    question_deadline: Optional[date] = Field(default=None, alias="QuestionDeadline")
    bid_opening_date: Optional[date] = Field(default=None, alias="BidOpeningDate")
    award_date: Optional[date] = Field(default=None, alias="AwardDate")
    
    # Location
    bid_location: Optional[str] = Field(default=None, alias="BidLocation")
    
    # Bids
    bids: Optional[List[BidModel]] = Field(default=None, alias="Bids")
    bid_count: Optional[int] = Field(default=None, alias="BidCount")
    
    # Alternates
    alternates: Optional[List[BidAlternateModel]] = Field(default=None, alias="Alternates")
    
    # Awarded bid info
    awarded_to: Optional[CompanyFull] = Field(default=None, alias="AwardedTo")
    award_amount: Optional[Decimal] = Field(default=None, alias="AwardAmount")
    
    # Requirements
    bond_requirements: Optional[str] = Field(default=None, alias="BondRequirements")
    insurance_requirements: Optional[str] = Field(default=None, alias="InsuranceRequirements")
    prequalification_required: Optional[bool] = Field(default=None, alias="PrequalificationRequired")
    
    # Invited bidders
    invited_bidders: Optional[List[CompanyFull]] = Field(default=None, alias="InvitedBidders")
    
    # People
    bid_manager: Optional[ContactFull] = Field(default=None, alias="BidManager")
    prepared_by: Optional[ContactFull] = Field(default=None, alias="PreparedBy")
    
    # Distribution
    distribution: Optional[List[DistributionEntry]] = Field(default=None, alias="Distribution")
    
    # Documents
    bid_documents: Optional[List[KahuaFile]] = Field(default=None, alias="BidDocuments")
    attachments: Optional[List[KahuaFile]] = Field(default=None, alias="Attachments")
    
    # Comments
    comments: Optional[List[Comment]] = Field(default=None, alias="Comments")
    
    # Workflow
    workflow_info: Optional[WorkflowInfo] = Field(default=None, alias="WorkflowInfo")
    approval_info: Optional[ApprovalInfo] = Field(default=None, alias="ApprovalInfo")
    
    notes: Optional[str] = Field(default=None, alias="Notes")

    entity_def: str = Field(default="kahua_Bidding.BidPackage", exclude=True)


class ProposalModel(KahuaBaseModel):
    """
    Proposal entity model (for qualifications-based selection).
    Entity Definition: kahua_Proposals.Proposal
    """

    # Identification
    number: Optional[str] = Field(default=None, alias="Number")
    proposal_number: Optional[str] = Field(default=None, alias="ProposalNumber")
    title: Optional[str] = Field(default=None, alias="Title")
    subject: Optional[str] = Field(default=None, alias="Subject")
    description: Optional[str] = Field(default=None, alias="Description")
    
    # Status
    status: Optional[CostItemStatus] = Field(default=None, alias="Status")
    proposal_status: Optional[str] = Field(default=None, alias="ProposalStatus")
    
    # Proposer
    proposer: Optional[CompanyFull] = Field(default=None, alias="Proposer")
    proposer_contact: Optional[ContactFull] = Field(default=None, alias="ProposerContact")
    
    # Dates
    date_submitted: Optional[date] = Field(default=None, alias="DateSubmitted")
    date_received: Optional[date] = Field(default=None, alias="DateReceived")
    valid_until: Optional[date] = Field(default=None, alias="ValidUntil")
    
    # Pricing
    proposed_fee: Optional[Decimal] = Field(default=None, alias="ProposedFee")
    proposed_cost: Optional[Decimal] = Field(default=None, alias="ProposedCost")
    hourly_rates: Optional[str] = Field(default=None, alias="HourlyRates")
    
    # Evaluation
    technical_score: Optional[float] = Field(default=None, alias="TechnicalScore")
    price_score: Optional[float] = Field(default=None, alias="PriceScore")
    total_score: Optional[float] = Field(default=None, alias="TotalScore")
    rank: Optional[int] = Field(default=None, alias="Rank")
    is_shortlisted: Optional[bool] = Field(default=None, alias="IsShortlisted")
    is_selected: Optional[bool] = Field(default=None, alias="IsSelected")
    
    # Evaluation comments
    evaluation_comments: Optional[str] = Field(default=None, alias="EvaluationComments")
    strengths: Optional[str] = Field(default=None, alias="Strengths")
    weaknesses: Optional[str] = Field(default=None, alias="Weaknesses")
    
    # Qualifications
    relevant_experience: Optional[str] = Field(default=None, alias="RelevantExperience")
    key_personnel: Optional[str] = Field(default=None, alias="KeyPersonnel")
    references: Optional[str] = Field(default=None, alias="References")
    
    # Attachments
    attachments: Optional[List[KahuaFile]] = Field(default=None, alias="Attachments")
    
    # Comments
    comments: Optional[List[Comment]] = Field(default=None, alias="Comments")
    
    notes: Optional[str] = Field(default=None, alias="Notes")

    entity_def: str = Field(default="kahua_Proposals.Proposal", exclude=True)


def _rebuild_models() -> None:
    """Rebuild models to resolve forward references."""
    models = [
        BidLineItemModel,
        BidModel,
        BidAlternateModel,
        BidPackageModel,
        ProposalModel,
    ]
    for model in models:
        if hasattr(model, "model_rebuild"):
            model.model_rebuild()


_rebuild_models()
