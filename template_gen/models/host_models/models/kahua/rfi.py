"""
RFI (Request for Information) entity models for Kahua Portable View templates.
Entities: kahua_AEC_RFI.RFI
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


class RFIModel(KahuaBaseModel):
    """
    RFI (Request for Information) entity model.
    Entity Definition: kahua_AEC_RFI.RFI
    """

    # Identification
    number: Optional[str] = Field(default=None, alias="Number")
    subject: Optional[str] = Field(default=None, alias="Subject")
    subject_lower: Optional[str] = Field(default=None, alias="SubjectLower")
    discipline: Optional[str] = Field(default=None, alias="Discipline")
    status: Optional[CostItemStatus] = Field(default=None, alias="Status")
    priority: Optional[str] = Field(default=None, alias="Priority")
    
    # Classification
    rfi_type: Optional[str] = Field(default=None, alias="RFIType")
    spec_section: Optional[str] = Field(default=None, alias="SpecSection")
    csi_code: Optional[CSICode] = Field(default=None, alias="CSICode")
    location: Optional[Location] = Field(default=None, alias="Location")
    location_description: Optional[str] = Field(default=None, alias="LocationDescription")
    
    # Dates
    date_initiated: Optional[date] = Field(default=None, alias="DateInitiated")
    date_required: Optional[date] = Field(default=None, alias="DateRequired")
    date_responded: Optional[date] = Field(default=None, alias="DateResponded")
    date_closed: Optional[date] = Field(default=None, alias="DateClosed")
    date_sent: Optional[date] = Field(default=None, alias="DateSent")
    date_received: Optional[date] = Field(default=None, alias="DateReceived")
    date_returned: Optional[date] = Field(default=None, alias="DateReturned")
    date_due: Optional[date] = Field(default=None, alias="DateDue")
    
    # Time tracking
    days_open: Optional[int] = Field(default=None, alias="DaysOpen")
    days_overdue: Optional[int] = Field(default=None, alias="DaysOverdue")
    is_overdue: Optional[bool] = Field(default=None, alias="IsOverdue")
    
    # People
    initiator: Optional[ContactFull] = Field(default=None, alias="Initiator")
    from_contact: Optional[ContactFull] = Field(default=None, alias="From")
    assigned_to: Optional[ContactFull] = Field(default=None, alias="AssignedTo")
    sent_to: Optional[ContactFull] = Field(default=None, alias="SentTo")
    responsible_party: Optional[ContactFull] = Field(default=None, alias="ResponsibleParty")
    ball_in_court: Optional[ContactFull] = Field(default=None, alias="BallInCourt")
    responded_by: Optional[ContactFull] = Field(default=None, alias="RespondedBy")
    closed_by: Optional[ContactFull] = Field(default=None, alias="ClosedBy")
    
    # Companies
    from_company: Optional[CompanyFull] = Field(default=None, alias="FromCompany")
    to_company: Optional[CompanyFull] = Field(default=None, alias="ToCompany")
    gc_company: Optional[CompanyFull] = Field(default=None, alias="GCCompany")
    architect_company: Optional[CompanyFull] = Field(default=None, alias="ArchitectCompany")
    
    # Question and Response
    question: Optional[str] = Field(default=None, alias="Question")
    question_detail: Optional[str] = Field(default=None, alias="QuestionDetail")
    suggested_solution: Optional[str] = Field(default=None, alias="SuggestedSolution")
    response: Optional[str] = Field(default=None, alias="Response")
    response_detail: Optional[str] = Field(default=None, alias="ResponseDetail")
    official_response: Optional[str] = Field(default=None, alias="OfficialResponse")
    
    # Cost impact
    has_cost_impact: Optional[bool] = Field(default=None, alias="HasCostImpact")
    estimated_cost_impact: Optional[str] = Field(default=None, alias="EstimatedCostImpact")
    cost_impact_amount: Optional[float] = Field(default=None, alias="CostImpactAmount")
    cost_impact_description: Optional[str] = Field(default=None, alias="CostImpactDescription")
    
    # Schedule impact
    has_schedule_impact: Optional[bool] = Field(default=None, alias="HasScheduleImpact")
    schedule_impact_days: Optional[int] = Field(default=None, alias="ScheduleImpactDays")
    schedule_impact_description: Optional[str] = Field(default=None, alias="ScheduleImpactDescription")
    
    # Drawing references
    drawing_reference: Optional[str] = Field(default=None, alias="DrawingReference")
    drawing_number: Optional[str] = Field(default=None, alias="DrawingNumber")
    sheet_number: Optional[str] = Field(default=None, alias="SheetNumber")
    detail_number: Optional[str] = Field(default=None, alias="DetailNumber")
    revision: Optional[str] = Field(default=None, alias="Revision")
    
    # Related items
    related_rfis: Optional[List[OutwardReference]] = Field(default=None, alias="RelatedRFIs")
    related_submittals: Optional[List[OutwardReference]] = Field(default=None, alias="RelatedSubmittals")
    related_change_orders: Optional[List[OutwardReference]] = Field(default=None, alias="RelatedChangeOrders")
    
    # Distribution
    distribution: Optional[List[DistributionEntry]] = Field(default=None, alias="Distribution")
    notification_list: Optional[List[NotificationEntry]] = Field(default=None, alias="NotificationList")
    cc_list: Optional[List[ContactFull]] = Field(default=None, alias="CCList")
    
    # Comments and attachments
    comments: Optional[List[Comment]] = Field(default=None, alias="Comments")
    secondary_comments: Optional[List[SecondaryComment]] = Field(default=None, alias="SecondaryComments")
    attachments: Optional[List[KahuaFile]] = Field(default=None, alias="Attachments")
    question_attachments: Optional[List[KahuaFile]] = Field(default=None, alias="QuestionAttachments")
    response_attachments: Optional[List[KahuaFile]] = Field(default=None, alias="ResponseAttachments")
    
    # Workflow
    workflow_info: Optional[WorkflowInfo] = Field(default=None, alias="WorkflowInfo")
    approval_info: Optional[ApprovalInfo] = Field(default=None, alias="ApprovalInfo")
    
    # Custom fields commonly used
    notes: Optional[str] = Field(default=None, alias="Notes")
    remarks: Optional[str] = Field(default=None, alias="Remarks")
    internal_notes: Optional[str] = Field(default=None, alias="InternalNotes")

    entity_def: str = Field(default="kahua_AEC_RFI.RFI", exclude=True)


class RFIResponseModel(KahuaBaseModel):
    """RFI Response (for multi-response RFIs)."""

    response_date: Optional[date] = Field(default=None, alias="ResponseDate")
    responded_by: Optional[ContactFull] = Field(default=None, alias="RespondedBy")
    response: Optional[str] = Field(default=None, alias="Response")
    response_status: Optional[str] = Field(default=None, alias="ResponseStatus")
    attachments: Optional[List[KahuaFile]] = Field(default=None, alias="Attachments")
    notes: Optional[str] = Field(default=None, alias="Notes")

    entity_def: str = Field(default="kahua_AEC_RFI.RFIResponse", exclude=True)


def _rebuild_models() -> None:
    """Rebuild models to resolve forward references."""
    models = [
        RFIModel,
        RFIResponseModel,
    ]
    for model in models:
        if hasattr(model, "model_rebuild"):
            model.model_rebuild()


_rebuild_models()
