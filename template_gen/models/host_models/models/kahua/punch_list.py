"""
Punch list entity models for Kahua Portable View templates.
Entities: kahua_PunchList.PunchItem, kahua_AEC_PunchList.PunchListItem
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


class PunchItemModel(KahuaBaseModel):
    """
    Punch list item entity model.
    Entity Definition: kahua_PunchList.PunchItem or kahua_AEC_PunchList.PunchListItem
    """

    # Identification
    number: Optional[str] = Field(default=None, alias="Number")
    item_number: Optional[str] = Field(default=None, alias="ItemNumber")
    subject: Optional[str] = Field(default=None, alias="Subject")
    description: Optional[str] = Field(default=None, alias="Description")
    
    # Status and priority
    status: Optional[CostItemStatus] = Field(default=None, alias="Status")
    item_status: Optional[str] = Field(default=None, alias="ItemStatus")
    priority: Optional[str] = Field(default=None, alias="Priority")
    severity: Optional[str] = Field(default=None, alias="Severity")
    punch_type: Optional[str] = Field(default=None, alias="PunchType")
    
    # Classification
    category: Optional[str] = Field(default=None, alias="Category")
    discipline: Optional[str] = Field(default=None, alias="Discipline")
    csi_code: Optional[CSICode] = Field(default=None, alias="CSICode")
    trade: Optional[str] = Field(default=None, alias="Trade")
    
    # Location
    location: Optional[Location] = Field(default=None, alias="Location")
    location_description: Optional[str] = Field(default=None, alias="LocationDescription")
    building: Optional[str] = Field(default=None, alias="Building")
    floor: Optional[str] = Field(default=None, alias="Floor")
    room: Optional[str] = Field(default=None, alias="Room")
    area: Optional[str] = Field(default=None, alias="Area")
    
    # Dates
    date_identified: Optional[date] = Field(default=None, alias="DateIdentified")
    date_created: Optional[date] = Field(default=None, alias="DateCreated")
    date_due: Optional[date] = Field(default=None, alias="DateDue")
    date_completed: Optional[date] = Field(default=None, alias="DateCompleted")
    date_verified: Optional[date] = Field(default=None, alias="DateVerified")
    date_closed: Optional[date] = Field(default=None, alias="DateClosed")
    
    # People
    identified_by: Optional[ContactFull] = Field(default=None, alias="IdentifiedBy")
    created_by: Optional[ContactFull] = Field(default=None, alias="CreatedBy")
    assigned_to: Optional[ContactFull] = Field(default=None, alias="AssignedTo")
    responsible_party: Optional[ContactFull] = Field(default=None, alias="ResponsibleParty")
    ball_in_court: Optional[ContactFull] = Field(default=None, alias="BallInCourt")
    completed_by: Optional[ContactFull] = Field(default=None, alias="CompletedBy")
    verified_by: Optional[ContactFull] = Field(default=None, alias="VerifiedBy")
    closed_by: Optional[ContactFull] = Field(default=None, alias="ClosedBy")
    
    # Companies
    responsible_company: Optional[CompanyFull] = Field(default=None, alias="ResponsibleCompany")
    subcontractor: Optional[CompanyFull] = Field(default=None, alias="Subcontractor")
    
    # Resolution
    resolution: Optional[str] = Field(default=None, alias="Resolution")
    corrective_action: Optional[str] = Field(default=None, alias="CorrectiveAction")
    verification_notes: Optional[str] = Field(default=None, alias="VerificationNotes")
    
    # Drawing reference
    drawing_reference: Optional[str] = Field(default=None, alias="DrawingReference")
    sheet_number: Optional[str] = Field(default=None, alias="SheetNumber")
    
    # Cost tracking
    estimated_cost: Optional[float] = Field(default=None, alias="EstimatedCost")
    actual_cost: Optional[float] = Field(default=None, alias="ActualCost")
    back_charge: Optional[bool] = Field(default=None, alias="BackCharge")
    back_charge_amount: Optional[float] = Field(default=None, alias="BackChargeAmount")
    
    # Parent list reference
    parent_list: Optional[OutwardReference] = Field(default=None, alias="ParentList")
    punch_list_number: Optional[str] = Field(default=None, alias="PunchListNumber")
    
    # Photos and attachments
    photos: Optional[List[KahuaFile]] = Field(default=None, alias="Photos")
    before_photos: Optional[List[KahuaFile]] = Field(default=None, alias="BeforePhotos")
    after_photos: Optional[List[KahuaFile]] = Field(default=None, alias="AfterPhotos")
    attachments: Optional[List[KahuaFile]] = Field(default=None, alias="Attachments")
    
    # Comments
    comments: Optional[List[Comment]] = Field(default=None, alias="Comments")
    secondary_comments: Optional[List[SecondaryComment]] = Field(default=None, alias="SecondaryComments")
    
    # Workflow
    workflow_info: Optional[WorkflowInfo] = Field(default=None, alias="WorkflowInfo")
    
    # Notes
    notes: Optional[str] = Field(default=None, alias="Notes")
    internal_notes: Optional[str] = Field(default=None, alias="InternalNotes")

    entity_def: str = Field(default="kahua_PunchList.PunchItem", exclude=True)


class PunchListModel(KahuaBaseModel):
    """
    Punch list (container) entity model.
    Entity Definition: kahua_PunchList.PunchList or kahua_AEC_PunchList.PunchList
    """

    # Identification
    number: Optional[str] = Field(default=None, alias="Number")
    list_number: Optional[str] = Field(default=None, alias="ListNumber")
    name: Optional[str] = Field(default=None, alias="Name")
    subject: Optional[str] = Field(default=None, alias="Subject")
    description: Optional[str] = Field(default=None, alias="Description")
    
    # Status
    status: Optional[CostItemStatus] = Field(default=None, alias="Status")
    list_type: Optional[str] = Field(default=None, alias="ListType")
    priority: Optional[str] = Field(default=None, alias="Priority")
    
    # Location
    location: Optional[Location] = Field(default=None, alias="Location")
    location_description: Optional[str] = Field(default=None, alias="LocationDescription")
    building: Optional[str] = Field(default=None, alias="Building")
    floor: Optional[str] = Field(default=None, alias="Floor")
    
    # Dates
    date_created: Optional[date] = Field(default=None, alias="DateCreated")
    date_due: Optional[date] = Field(default=None, alias="DateDue")
    date_completed: Optional[date] = Field(default=None, alias="DateCompleted")
    date_closed: Optional[date] = Field(default=None, alias="DateClosed")
    inspection_date: Optional[date] = Field(default=None, alias="InspectionDate")
    
    # People
    created_by: Optional[ContactFull] = Field(default=None, alias="CreatedBy")
    assigned_to: Optional[ContactFull] = Field(default=None, alias="AssignedTo")
    inspector: Optional[ContactFull] = Field(default=None, alias="Inspector")
    responsible_party: Optional[ContactFull] = Field(default=None, alias="ResponsibleParty")
    
    # Companies
    responsible_company: Optional[CompanyFull] = Field(default=None, alias="ResponsibleCompany")
    contractor: Optional[CompanyFull] = Field(default=None, alias="Contractor")
    
    # Items
    items: Optional[List[PunchItemModel]] = Field(default=None, alias="Items")
    item_count: Optional[int] = Field(default=None, alias="ItemCount")
    open_item_count: Optional[int] = Field(default=None, alias="OpenItemCount")
    closed_item_count: Optional[int] = Field(default=None, alias="ClosedItemCount")
    
    # Distribution
    distribution: Optional[List[DistributionEntry]] = Field(default=None, alias="Distribution")
    notification_list: Optional[List[NotificationEntry]] = Field(default=None, alias="NotificationList")
    
    # Attachments and comments
    attachments: Optional[List[KahuaFile]] = Field(default=None, alias="Attachments")
    comments: Optional[List[Comment]] = Field(default=None, alias="Comments")
    
    # Workflow
    workflow_info: Optional[WorkflowInfo] = Field(default=None, alias="WorkflowInfo")
    
    notes: Optional[str] = Field(default=None, alias="Notes")

    entity_def: str = Field(default="kahua_PunchList.PunchList", exclude=True)


def _rebuild_models() -> None:
    """Rebuild models to resolve forward references."""
    models = [
        PunchItemModel,
        PunchListModel,
    ]
    for model in models:
        if hasattr(model, "model_rebuild"):
            model.model_rebuild()


_rebuild_models()
