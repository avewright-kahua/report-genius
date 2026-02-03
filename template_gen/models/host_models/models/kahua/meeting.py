"""
Meeting entity models for Kahua Portable View templates.
Entities: kahua_MeetingMinutes.MeetingMinutes, MeetingItem
"""

from __future__ import annotations

from datetime import date, datetime, time
from typing import List, Optional

from pydantic import Field

from .common import (
    ApprovalInfo,
    Comment,
    CompanyFull,
    ContactFull,
    CostItemStatus,
    DistributionEntry,
    KahuaBaseModel,
    KahuaFile,
    Location,
    NotificationEntry,
    OutwardReference,
    SecondaryComment,
    WorkflowInfo,
)


class MeetingAttendeeModel(KahuaBaseModel):
    """Meeting attendee entry."""

    contact: Optional[ContactFull] = Field(default=None, alias="Contact")
    name: Optional[str] = Field(default=None, alias="Name")
    company: Optional[CompanyFull] = Field(default=None, alias="Company")
    company_name: Optional[str] = Field(default=None, alias="CompanyName")
    role: Optional[str] = Field(default=None, alias="Role")
    email: Optional[str] = Field(default=None, alias="Email")
    phone: Optional[str] = Field(default=None, alias="Phone")
    
    attendance_status: Optional[str] = Field(default=None, alias="AttendanceStatus")  # Attended, Absent, Excused
    is_required: Optional[bool] = Field(default=None, alias="IsRequired")
    is_optional: Optional[bool] = Field(default=None, alias="IsOptional")
    responded: Optional[bool] = Field(default=None, alias="Responded")


class MeetingItemModel(KahuaBaseModel):
    """
    Meeting item/action item entity model.
    Entity Definition: kahua_MeetingMinutes.MeetingItem
    """

    # Identification
    number: Optional[str] = Field(default=None, alias="Number")
    item_number: Optional[str] = Field(default=None, alias="ItemNumber")
    subject: Optional[str] = Field(default=None, alias="Subject")
    description: Optional[str] = Field(default=None, alias="Description")
    
    # Status
    status: Optional[CostItemStatus] = Field(default=None, alias="Status")
    item_status: Optional[str] = Field(default=None, alias="ItemStatus")
    priority: Optional[str] = Field(default=None, alias="Priority")
    item_type: Optional[str] = Field(default=None, alias="ItemType")  # Action, Discussion, Information
    
    # Category
    category: Optional[str] = Field(default=None, alias="Category")
    agenda_section: Optional[str] = Field(default=None, alias="AgendaSection")
    
    # Dates
    date_created: Optional[date] = Field(default=None, alias="DateCreated")
    date_due: Optional[date] = Field(default=None, alias="DateDue")
    date_completed: Optional[date] = Field(default=None, alias="DateCompleted")
    date_closed: Optional[date] = Field(default=None, alias="DateClosed")
    
    # People
    assigned_to: Optional[ContactFull] = Field(default=None, alias="AssignedTo")
    responsible_party: Optional[ContactFull] = Field(default=None, alias="ResponsibleParty")
    owner: Optional[ContactFull] = Field(default=None, alias="Owner")
    completed_by: Optional[ContactFull] = Field(default=None, alias="CompletedBy")
    
    # Company
    responsible_company: Optional[CompanyFull] = Field(default=None, alias="ResponsibleCompany")
    
    # Discussion/Resolution
    discussion: Optional[str] = Field(default=None, alias="Discussion")
    decision: Optional[str] = Field(default=None, alias="Decision")
    resolution: Optional[str] = Field(default=None, alias="Resolution")
    action_required: Optional[str] = Field(default=None, alias="ActionRequired")
    
    # Carry forward
    is_carry_forward: Optional[bool] = Field(default=None, alias="IsCarryForward")
    carried_from_meeting: Optional[OutwardReference] = Field(default=None, alias="CarriedFromMeeting")
    
    # Parent meeting reference
    parent_meeting: Optional[OutwardReference] = Field(default=None, alias="ParentMeeting")
    meeting_number: Optional[str] = Field(default=None, alias="MeetingNumber")
    
    # Attachments
    attachments: Optional[List[KahuaFile]] = Field(default=None, alias="Attachments")
    
    # Comments
    comments: Optional[List[Comment]] = Field(default=None, alias="Comments")
    
    notes: Optional[str] = Field(default=None, alias="Notes")

    entity_def: str = Field(default="kahua_MeetingMinutes.MeetingItem", exclude=True)


class MeetingModel(KahuaBaseModel):
    """
    Meeting minutes entity model.
    Entity Definition: kahua_MeetingMinutes.MeetingMinutes
    """

    # Identification
    number: Optional[str] = Field(default=None, alias="Number")
    meeting_number: Optional[str] = Field(default=None, alias="MeetingNumber")
    subject: Optional[str] = Field(default=None, alias="Subject")
    title: Optional[str] = Field(default=None, alias="Title")
    description: Optional[str] = Field(default=None, alias="Description")
    purpose: Optional[str] = Field(default=None, alias="Purpose")
    
    # Status
    status: Optional[CostItemStatus] = Field(default=None, alias="Status")
    meeting_type: Optional[str] = Field(default=None, alias="MeetingType")
    meeting_category: Optional[str] = Field(default=None, alias="MeetingCategory")
    
    # Date and time
    meeting_date: Optional[date] = Field(default=None, alias="MeetingDate")
    start_time: Optional[time] = Field(default=None, alias="StartTime")
    end_time: Optional[time] = Field(default=None, alias="EndTime")
    duration_minutes: Optional[int] = Field(default=None, alias="DurationMinutes")
    time_zone: Optional[str] = Field(default=None, alias="TimeZone")
    
    # Location
    location: Optional[Location] = Field(default=None, alias="Location")
    location_description: Optional[str] = Field(default=None, alias="LocationDescription")
    room: Optional[str] = Field(default=None, alias="Room")
    virtual_meeting_link: Optional[str] = Field(default=None, alias="VirtualMeetingLink")
    dial_in_number: Optional[str] = Field(default=None, alias="DialInNumber")
    is_virtual: Optional[bool] = Field(default=None, alias="IsVirtual")
    
    # People
    organizer: Optional[ContactFull] = Field(default=None, alias="Organizer")
    chair: Optional[ContactFull] = Field(default=None, alias="Chair")
    facilitator: Optional[ContactFull] = Field(default=None, alias="Facilitator")
    note_taker: Optional[ContactFull] = Field(default=None, alias="NoteTaker")
    prepared_by: Optional[ContactFull] = Field(default=None, alias="PreparedBy")
    approved_by: Optional[ContactFull] = Field(default=None, alias="ApprovedBy")
    
    # Attendees
    attendees: Optional[List[MeetingAttendeeModel]] = Field(default=None, alias="Attendees")
    attendee_count: Optional[int] = Field(default=None, alias="AttendeeCount")
    required_attendees: Optional[List[ContactFull]] = Field(default=None, alias="RequiredAttendees")
    optional_attendees: Optional[List[ContactFull]] = Field(default=None, alias="OptionalAttendees")
    absent_attendees: Optional[List[ContactFull]] = Field(default=None, alias="AbsentAttendees")
    
    # Agenda and minutes
    agenda: Optional[str] = Field(default=None, alias="Agenda")
    agenda_items: Optional[List[str]] = Field(default=None, alias="AgendaItems")
    minutes: Optional[str] = Field(default=None, alias="Minutes")
    summary: Optional[str] = Field(default=None, alias="Summary")
    
    # Meeting items
    items: Optional[List[MeetingItemModel]] = Field(default=None, alias="Items")
    action_items: Optional[List[MeetingItemModel]] = Field(default=None, alias="ActionItems")
    item_count: Optional[int] = Field(default=None, alias="ItemCount")
    open_item_count: Optional[int] = Field(default=None, alias="OpenItemCount")
    
    # Series info
    is_recurring: Optional[bool] = Field(default=None, alias="IsRecurring")
    recurrence_pattern: Optional[str] = Field(default=None, alias="RecurrencePattern")
    series_id: Optional[str] = Field(default=None, alias="SeriesId")
    previous_meeting: Optional[OutwardReference] = Field(default=None, alias="PreviousMeeting")
    next_meeting: Optional[OutwardReference] = Field(default=None, alias="NextMeeting")
    next_meeting_date: Optional[date] = Field(default=None, alias="NextMeetingDate")
    
    # Administrative dates
    date_created: Optional[date] = Field(default=None, alias="DateCreated")
    date_distributed: Optional[date] = Field(default=None, alias="DateDistributed")
    date_approved: Optional[date] = Field(default=None, alias="DateApproved")
    
    # Distribution
    distribution: Optional[List[DistributionEntry]] = Field(default=None, alias="Distribution")
    notification_list: Optional[List[NotificationEntry]] = Field(default=None, alias="NotificationList")
    cc_list: Optional[List[ContactFull]] = Field(default=None, alias="CCList")
    
    # Attachments and comments
    attachments: Optional[List[KahuaFile]] = Field(default=None, alias="Attachments")
    agenda_attachments: Optional[List[KahuaFile]] = Field(default=None, alias="AgendaAttachments")
    comments: Optional[List[Comment]] = Field(default=None, alias="Comments")
    secondary_comments: Optional[List[SecondaryComment]] = Field(default=None, alias="SecondaryComments")
    
    # Workflow
    workflow_info: Optional[WorkflowInfo] = Field(default=None, alias="WorkflowInfo")
    approval_info: Optional[ApprovalInfo] = Field(default=None, alias="ApprovalInfo")
    
    # Notes
    notes: Optional[str] = Field(default=None, alias="Notes")
    internal_notes: Optional[str] = Field(default=None, alias="InternalNotes")

    entity_def: str = Field(default="kahua_MeetingMinutes.MeetingMinutes", exclude=True)


def _rebuild_models() -> None:
    """Rebuild models to resolve forward references."""
    models = [
        MeetingAttendeeModel,
        MeetingItemModel,
        MeetingModel,
    ]
    for model in models:
        if hasattr(model, "model_rebuild"):
            model.model_rebuild()


_rebuild_models()
