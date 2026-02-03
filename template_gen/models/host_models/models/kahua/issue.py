"""
Issue and action item entity models for Kahua Portable View templates.
Entities: kahua_Issues.Issue, kahua_ActionItems.ActionItem
"""

from __future__ import annotations

from datetime import date, datetime
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
    WorkflowInfo,
)


class IssueModel(KahuaBaseModel):
    """
    Issue entity model.
    Entity Definition: kahua_Issues.Issue
    """

    # Identification
    number: Optional[str] = Field(default=None, alias="Number")
    issue_number: Optional[str] = Field(default=None, alias="IssueNumber")
    subject: Optional[str] = Field(default=None, alias="Subject")
    title: Optional[str] = Field(default=None, alias="Title")
    description: Optional[str] = Field(default=None, alias="Description")
    
    # Status
    status: Optional[CostItemStatus] = Field(default=None, alias="Status")
    issue_status: Optional[str] = Field(default=None, alias="IssueStatus")
    priority: Optional[str] = Field(default=None, alias="Priority")
    severity: Optional[str] = Field(default=None, alias="Severity")
    
    # Classification
    issue_type: Optional[str] = Field(default=None, alias="IssueType")
    category: Optional[str] = Field(default=None, alias="Category")
    discipline: Optional[str] = Field(default=None, alias="Discipline")
    csi_code: Optional[CSICode] = Field(default=None, alias="CSICode")
    
    # Location
    location: Optional[Location] = Field(default=None, alias="Location")
    location_description: Optional[str] = Field(default=None, alias="LocationDescription")
    
    # Dates
    date_identified: Optional[date] = Field(default=None, alias="DateIdentified")
    date_created: Optional[date] = Field(default=None, alias="DateCreated")
    date_due: Optional[date] = Field(default=None, alias="DateDue")
    date_resolved: Optional[date] = Field(default=None, alias="DateResolved")
    date_closed: Optional[date] = Field(default=None, alias="DateClosed")
    
    # Time tracking
    days_open: Optional[int] = Field(default=None, alias="DaysOpen")
    days_overdue: Optional[int] = Field(default=None, alias="DaysOverdue")
    is_overdue: Optional[bool] = Field(default=None, alias="IsOverdue")
    
    # People
    identified_by: Optional[ContactFull] = Field(default=None, alias="IdentifiedBy")
    created_by: Optional[ContactFull] = Field(default=None, alias="CreatedBy")
    assigned_to: Optional[ContactFull] = Field(default=None, alias="AssignedTo")
    responsible_party: Optional[ContactFull] = Field(default=None, alias="ResponsibleParty")
    ball_in_court: Optional[ContactFull] = Field(default=None, alias="BallInCourt")
    resolved_by: Optional[ContactFull] = Field(default=None, alias="ResolvedBy")
    closed_by: Optional[ContactFull] = Field(default=None, alias="ClosedBy")
    
    # Companies
    responsible_company: Optional[CompanyFull] = Field(default=None, alias="ResponsibleCompany")
    
    # Impact
    has_cost_impact: Optional[bool] = Field(default=None, alias="HasCostImpact")
    cost_impact_amount: Optional[float] = Field(default=None, alias="CostImpactAmount")
    has_schedule_impact: Optional[bool] = Field(default=None, alias="HasScheduleImpact")
    schedule_impact_days: Optional[int] = Field(default=None, alias="ScheduleImpactDays")
    
    # Resolution
    resolution: Optional[str] = Field(default=None, alias="Resolution")
    resolution_description: Optional[str] = Field(default=None, alias="ResolutionDescription")
    root_cause: Optional[str] = Field(default=None, alias="RootCause")
    corrective_action: Optional[str] = Field(default=None, alias="CorrectiveAction")
    preventive_action: Optional[str] = Field(default=None, alias="PreventiveAction")
    
    # Related items
    related_issues: Optional[List[OutwardReference]] = Field(default=None, alias="RelatedIssues")
    related_rfis: Optional[List[OutwardReference]] = Field(default=None, alias="RelatedRFIs")
    related_change_orders: Optional[List[OutwardReference]] = Field(default=None, alias="RelatedChangeOrders")
    
    # Distribution
    distribution: Optional[List[DistributionEntry]] = Field(default=None, alias="Distribution")
    notification_list: Optional[List[NotificationEntry]] = Field(default=None, alias="NotificationList")
    
    # Attachments
    attachments: Optional[List[KahuaFile]] = Field(default=None, alias="Attachments")
    
    # Comments
    comments: Optional[List[Comment]] = Field(default=None, alias="Comments")
    secondary_comments: Optional[List[SecondaryComment]] = Field(default=None, alias="SecondaryComments")
    
    # Workflow
    workflow_info: Optional[WorkflowInfo] = Field(default=None, alias="WorkflowInfo")
    
    # Notes
    notes: Optional[str] = Field(default=None, alias="Notes")
    internal_notes: Optional[str] = Field(default=None, alias="InternalNotes")

    entity_def: str = Field(default="kahua_Issues.Issue", exclude=True)


class ActionItemModel(KahuaBaseModel):
    """
    Action item entity model.
    Entity Definition: kahua_ActionItems.ActionItem
    """

    # Identification
    number: Optional[str] = Field(default=None, alias="Number")
    action_number: Optional[str] = Field(default=None, alias="ActionNumber")
    subject: Optional[str] = Field(default=None, alias="Subject")
    title: Optional[str] = Field(default=None, alias="Title")
    description: Optional[str] = Field(default=None, alias="Description")
    
    # Status
    status: Optional[CostItemStatus] = Field(default=None, alias="Status")
    action_status: Optional[str] = Field(default=None, alias="ActionStatus")
    priority: Optional[str] = Field(default=None, alias="Priority")
    
    # Classification
    action_type: Optional[str] = Field(default=None, alias="ActionType")
    category: Optional[str] = Field(default=None, alias="Category")
    
    # Dates
    date_created: Optional[date] = Field(default=None, alias="DateCreated")
    date_due: Optional[date] = Field(default=None, alias="DateDue")
    date_completed: Optional[date] = Field(default=None, alias="DateCompleted")
    date_closed: Optional[date] = Field(default=None, alias="DateClosed")
    
    # Time tracking
    days_open: Optional[int] = Field(default=None, alias="DaysOpen")
    days_overdue: Optional[int] = Field(default=None, alias="DaysOverdue")
    is_overdue: Optional[bool] = Field(default=None, alias="IsOverdue")
    
    # People
    created_by: Optional[ContactFull] = Field(default=None, alias="CreatedBy")
    assigned_to: Optional[ContactFull] = Field(default=None, alias="AssignedTo")
    owner: Optional[ContactFull] = Field(default=None, alias="Owner")
    responsible_party: Optional[ContactFull] = Field(default=None, alias="ResponsibleParty")
    ball_in_court: Optional[ContactFull] = Field(default=None, alias="BallInCourt")
    completed_by: Optional[ContactFull] = Field(default=None, alias="CompletedBy")
    
    # Company
    responsible_company: Optional[CompanyFull] = Field(default=None, alias="ResponsibleCompany")
    
    # Resolution
    resolution: Optional[str] = Field(default=None, alias="Resolution")
    action_taken: Optional[str] = Field(default=None, alias="ActionTaken")
    result: Optional[str] = Field(default=None, alias="Result")
    
    # Source
    source: Optional[str] = Field(default=None, alias="Source")
    source_reference: Optional[OutwardReference] = Field(default=None, alias="SourceReference")
    parent_meeting: Optional[OutwardReference] = Field(default=None, alias="ParentMeeting")
    parent_issue: Optional[OutwardReference] = Field(default=None, alias="ParentIssue")
    
    # Related items
    related_items: Optional[List[OutwardReference]] = Field(default=None, alias="RelatedItems")
    
    # Distribution
    notification_list: Optional[List[NotificationEntry]] = Field(default=None, alias="NotificationList")
    
    # Attachments
    attachments: Optional[List[KahuaFile]] = Field(default=None, alias="Attachments")
    
    # Comments
    comments: Optional[List[Comment]] = Field(default=None, alias="Comments")
    
    # Notes
    notes: Optional[str] = Field(default=None, alias="Notes")

    entity_def: str = Field(default="kahua_ActionItems.ActionItem", exclude=True)


class RiskModel(KahuaBaseModel):
    """
    Risk entity model.
    Entity Definition: kahua_Risks.Risk
    """

    # Identification
    number: Optional[str] = Field(default=None, alias="Number")
    risk_id: Optional[str] = Field(default=None, alias="RiskId")
    subject: Optional[str] = Field(default=None, alias="Subject")
    title: Optional[str] = Field(default=None, alias="Title")
    description: Optional[str] = Field(default=None, alias="Description")
    
    # Status
    status: Optional[CostItemStatus] = Field(default=None, alias="Status")
    risk_status: Optional[str] = Field(default=None, alias="RiskStatus")
    
    # Classification
    risk_type: Optional[str] = Field(default=None, alias="RiskType")
    category: Optional[str] = Field(default=None, alias="Category")
    source: Optional[str] = Field(default=None, alias="Source")
    
    # Assessment
    probability: Optional[str] = Field(default=None, alias="Probability")  # Low, Medium, High
    probability_score: Optional[int] = Field(default=None, alias="ProbabilityScore")
    impact: Optional[str] = Field(default=None, alias="Impact")  # Low, Medium, High
    impact_score: Optional[int] = Field(default=None, alias="ImpactScore")
    risk_score: Optional[int] = Field(default=None, alias="RiskScore")
    risk_rating: Optional[str] = Field(default=None, alias="RiskRating")
    
    # Impact details
    cost_impact: Optional[float] = Field(default=None, alias="CostImpact")
    schedule_impact_days: Optional[int] = Field(default=None, alias="ScheduleImpactDays")
    quality_impact: Optional[str] = Field(default=None, alias="QualityImpact")
    
    # Dates
    date_identified: Optional[date] = Field(default=None, alias="DateIdentified")
    date_created: Optional[date] = Field(default=None, alias="DateCreated")
    review_date: Optional[date] = Field(default=None, alias="ReviewDate")
    date_closed: Optional[date] = Field(default=None, alias="DateClosed")
    
    # People
    identified_by: Optional[ContactFull] = Field(default=None, alias="IdentifiedBy")
    risk_owner: Optional[ContactFull] = Field(default=None, alias="RiskOwner")
    assigned_to: Optional[ContactFull] = Field(default=None, alias="AssignedTo")
    
    # Response
    response_strategy: Optional[str] = Field(default=None, alias="ResponseStrategy")  # Accept, Mitigate, Transfer, Avoid
    mitigation_plan: Optional[str] = Field(default=None, alias="MitigationPlan")
    contingency_plan: Optional[str] = Field(default=None, alias="ContingencyPlan")
    trigger: Optional[str] = Field(default=None, alias="Trigger")
    
    # Residual risk
    residual_probability: Optional[str] = Field(default=None, alias="ResidualProbability")
    residual_impact: Optional[str] = Field(default=None, alias="ResidualImpact")
    residual_score: Optional[int] = Field(default=None, alias="ResidualScore")
    
    # Related items
    related_risks: Optional[List[OutwardReference]] = Field(default=None, alias="RelatedRisks")
    related_issues: Optional[List[OutwardReference]] = Field(default=None, alias="RelatedIssues")
    
    # Attachments
    attachments: Optional[List[KahuaFile]] = Field(default=None, alias="Attachments")
    
    # Comments
    comments: Optional[List[Comment]] = Field(default=None, alias="Comments")
    
    # Notes
    notes: Optional[str] = Field(default=None, alias="Notes")

    entity_def: str = Field(default="kahua_Risks.Risk", exclude=True)


def _rebuild_models() -> None:
    """Rebuild models to resolve forward references."""
    models = [
        IssueModel,
        ActionItemModel,
        RiskModel,
    ]
    for model in models:
        if hasattr(model, "model_rebuild"):
            model.model_rebuild()


_rebuild_models()
