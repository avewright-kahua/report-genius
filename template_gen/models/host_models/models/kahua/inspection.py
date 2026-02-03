"""
Inspection entity models for Kahua Portable View templates.
Entities: kahua_Inspections.Inspection, kahua_AEC_Inspections.Inspection
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


class InspectionChecklistItemModel(KahuaBaseModel):
    """Inspection checklist item."""

    item_number: Optional[str] = Field(default=None, alias="ItemNumber")
    description: Optional[str] = Field(default=None, alias="Description")
    category: Optional[str] = Field(default=None, alias="Category")
    
    # Result
    result: Optional[str] = Field(default=None, alias="Result")  # Pass, Fail, N/A
    is_pass: Optional[bool] = Field(default=None, alias="IsPass")
    is_fail: Optional[bool] = Field(default=None, alias="IsFail")
    is_na: Optional[bool] = Field(default=None, alias="IsNA")
    
    # Details
    comments: Optional[str] = Field(default=None, alias="Comments")
    deficiency_description: Optional[str] = Field(default=None, alias="DeficiencyDescription")
    corrective_action: Optional[str] = Field(default=None, alias="CorrectiveAction")
    
    # Reference
    reference_standard: Optional[str] = Field(default=None, alias="ReferenceStandard")
    spec_section: Optional[str] = Field(default=None, alias="SpecSection")
    
    # Attachments
    photos: Optional[List[KahuaFile]] = Field(default=None, alias="Photos")
    attachments: Optional[List[KahuaFile]] = Field(default=None, alias="Attachments")


class ObservationModel(KahuaBaseModel):
    """
    Observation entity model (can be part of inspection or standalone).
    Entity Definition: kahua_Observations.Observation
    """

    # Identification
    number: Optional[str] = Field(default=None, alias="Number")
    subject: Optional[str] = Field(default=None, alias="Subject")
    description: Optional[str] = Field(default=None, alias="Description")
    
    # Status
    status: Optional[CostItemStatus] = Field(default=None, alias="Status")
    observation_type: Optional[str] = Field(default=None, alias="ObservationType")
    severity: Optional[str] = Field(default=None, alias="Severity")
    priority: Optional[str] = Field(default=None, alias="Priority")
    
    # Classification
    category: Optional[str] = Field(default=None, alias="Category")
    discipline: Optional[str] = Field(default=None, alias="Discipline")
    trade: Optional[str] = Field(default=None, alias="Trade")
    csi_code: Optional[CSICode] = Field(default=None, alias="CSICode")
    
    # Location
    location: Optional[Location] = Field(default=None, alias="Location")
    location_description: Optional[str] = Field(default=None, alias="LocationDescription")
    building: Optional[str] = Field(default=None, alias="Building")
    floor: Optional[str] = Field(default=None, alias="Floor")
    room: Optional[str] = Field(default=None, alias="Room")
    
    # Dates
    date_observed: Optional[date] = Field(default=None, alias="DateObserved")
    date_due: Optional[date] = Field(default=None, alias="DateDue")
    date_resolved: Optional[date] = Field(default=None, alias="DateResolved")
    
    # People
    observed_by: Optional[ContactFull] = Field(default=None, alias="ObservedBy")
    assigned_to: Optional[ContactFull] = Field(default=None, alias="AssignedTo")
    responsible_party: Optional[ContactFull] = Field(default=None, alias="ResponsibleParty")
    
    # Company
    responsible_company: Optional[CompanyFull] = Field(default=None, alias="ResponsibleCompany")
    
    # Resolution
    resolution: Optional[str] = Field(default=None, alias="Resolution")
    corrective_action: Optional[str] = Field(default=None, alias="CorrectiveAction")
    
    # Parent inspection reference
    parent_inspection: Optional[OutwardReference] = Field(default=None, alias="ParentInspection")
    
    # Photos and attachments
    photos: Optional[List[KahuaFile]] = Field(default=None, alias="Photos")
    attachments: Optional[List[KahuaFile]] = Field(default=None, alias="Attachments")
    
    # Comments
    comments: Optional[List[Comment]] = Field(default=None, alias="Comments")
    
    notes: Optional[str] = Field(default=None, alias="Notes")

    entity_def: str = Field(default="kahua_Observations.Observation", exclude=True)


class InspectionModel(KahuaBaseModel):
    """
    Inspection entity model.
    Entity Definition: kahua_Inspections.Inspection or kahua_AEC_Inspections.Inspection
    """

    # Identification
    number: Optional[str] = Field(default=None, alias="Number")
    inspection_number: Optional[str] = Field(default=None, alias="InspectionNumber")
    subject: Optional[str] = Field(default=None, alias="Subject")
    title: Optional[str] = Field(default=None, alias="Title")
    description: Optional[str] = Field(default=None, alias="Description")
    
    # Status and result
    status: Optional[CostItemStatus] = Field(default=None, alias="Status")
    inspection_result: Optional[str] = Field(default=None, alias="InspectionResult")  # Pass, Fail, Conditional, etc.
    is_passed: Optional[bool] = Field(default=None, alias="IsPassed")
    is_failed: Optional[bool] = Field(default=None, alias="IsFailed")
    
    # Classification
    inspection_type: Optional[str] = Field(default=None, alias="InspectionType")
    inspection_category: Optional[str] = Field(default=None, alias="InspectionCategory")
    discipline: Optional[str] = Field(default=None, alias="Discipline")
    trade: Optional[str] = Field(default=None, alias="Trade")
    csi_code: Optional[CSICode] = Field(default=None, alias="CSICode")
    spec_section: Optional[str] = Field(default=None, alias="SpecSection")
    
    # Location
    location: Optional[Location] = Field(default=None, alias="Location")
    location_description: Optional[str] = Field(default=None, alias="LocationDescription")
    building: Optional[str] = Field(default=None, alias="Building")
    floor: Optional[str] = Field(default=None, alias="Floor")
    area: Optional[str] = Field(default=None, alias="Area")
    
    # Dates and times
    scheduled_date: Optional[date] = Field(default=None, alias="ScheduledDate")
    inspection_date: Optional[date] = Field(default=None, alias="InspectionDate")
    scheduled_time: Optional[time] = Field(default=None, alias="ScheduledTime")
    start_time: Optional[time] = Field(default=None, alias="StartTime")
    end_time: Optional[time] = Field(default=None, alias="EndTime")
    date_requested: Optional[date] = Field(default=None, alias="DateRequested")
    date_completed: Optional[date] = Field(default=None, alias="DateCompleted")
    reinspection_date: Optional[date] = Field(default=None, alias="ReinspectionDate")
    
    # People
    requested_by: Optional[ContactFull] = Field(default=None, alias="RequestedBy")
    inspector: Optional[ContactFull] = Field(default=None, alias="Inspector")
    inspected_by: Optional[ContactFull] = Field(default=None, alias="InspectedBy")
    lead_inspector: Optional[ContactFull] = Field(default=None, alias="LeadInspector")
    conducted_by: Optional[ContactFull] = Field(default=None, alias="ConductedBy")
    witnessed_by: Optional[ContactFull] = Field(default=None, alias="WitnessedBy")
    approved_by: Optional[ContactFull] = Field(default=None, alias="ApprovedBy")
    
    # Inspection agency
    inspection_agency: Optional[CompanyFull] = Field(default=None, alias="InspectionAgency")
    contractor: Optional[CompanyFull] = Field(default=None, alias="Contractor")
    subcontractor: Optional[CompanyFull] = Field(default=None, alias="Subcontractor")
    
    # Checklist and observations
    checklist_items: Optional[List[InspectionChecklistItemModel]] = Field(default=None, alias="ChecklistItems")
    observations: Optional[List[ObservationModel]] = Field(default=None, alias="Observations")
    deficiencies: Optional[List[ObservationModel]] = Field(default=None, alias="Deficiencies")
    
    # Counts
    total_items: Optional[int] = Field(default=None, alias="TotalItems")
    passed_items: Optional[int] = Field(default=None, alias="PassedItems")
    failed_items: Optional[int] = Field(default=None, alias="FailedItems")
    observation_count: Optional[int] = Field(default=None, alias="ObservationCount")
    deficiency_count: Optional[int] = Field(default=None, alias="DeficiencyCount")
    
    # Summary and findings
    summary: Optional[str] = Field(default=None, alias="Summary")
    findings: Optional[str] = Field(default=None, alias="Findings")
    recommendations: Optional[str] = Field(default=None, alias="Recommendations")
    corrective_actions: Optional[str] = Field(default=None, alias="CorrectiveActions")
    
    # References
    drawing_reference: Optional[str] = Field(default=None, alias="DrawingReference")
    permit_number: Optional[str] = Field(default=None, alias="PermitNumber")
    
    # Related items
    related_inspections: Optional[List[OutwardReference]] = Field(default=None, alias="RelatedInspections")
    related_punch_items: Optional[List[OutwardReference]] = Field(default=None, alias="RelatedPunchItems")
    related_rfis: Optional[List[OutwardReference]] = Field(default=None, alias="RelatedRFIs")
    
    # Re-inspection
    is_reinspection: Optional[bool] = Field(default=None, alias="IsReinspection")
    original_inspection: Optional[OutwardReference] = Field(default=None, alias="OriginalInspection")
    reinspection_required: Optional[bool] = Field(default=None, alias="ReinspectionRequired")
    
    # Distribution
    distribution: Optional[List[DistributionEntry]] = Field(default=None, alias="Distribution")
    notification_list: Optional[List[NotificationEntry]] = Field(default=None, alias="NotificationList")
    
    # Photos and attachments
    photos: Optional[List[KahuaFile]] = Field(default=None, alias="Photos")
    attachments: Optional[List[KahuaFile]] = Field(default=None, alias="Attachments")
    
    # Comments
    comments: Optional[List[Comment]] = Field(default=None, alias="Comments")
    secondary_comments: Optional[List[SecondaryComment]] = Field(default=None, alias="SecondaryComments")
    
    # Workflow
    workflow_info: Optional[WorkflowInfo] = Field(default=None, alias="WorkflowInfo")
    approval_info: Optional[ApprovalInfo] = Field(default=None, alias="ApprovalInfo")
    
    # Notes
    notes: Optional[str] = Field(default=None, alias="Notes")
    internal_notes: Optional[str] = Field(default=None, alias="InternalNotes")
    inspector_notes: Optional[str] = Field(default=None, alias="InspectorNotes")

    entity_def: str = Field(default="kahua_Inspections.Inspection", exclude=True)


class InspectionTypeModel(KahuaBaseModel):
    """Inspection type definition."""

    name: Optional[str] = Field(default=None, alias="Name")
    description: Optional[str] = Field(default=None, alias="Description")
    category: Optional[str] = Field(default=None, alias="Category")
    discipline: Optional[str] = Field(default=None, alias="Discipline")
    checklist_template: Optional[str] = Field(default=None, alias="ChecklistTemplate")
    is_active: Optional[bool] = Field(default=None, alias="IsActive")

    entity_def: str = Field(default="kahua_Inspections.InspectionType", exclude=True)


def _rebuild_models() -> None:
    """Rebuild models to resolve forward references."""
    models = [
        InspectionChecklistItemModel,
        ObservationModel,
        InspectionModel,
        InspectionTypeModel,
    ]
    for model in models:
        if hasattr(model, "model_rebuild"):
            model.model_rebuild()


_rebuild_models()
