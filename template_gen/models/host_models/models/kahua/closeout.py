"""
Closeout entity models for Kahua Portable View templates.
Entities: kahua_Closeout.WarrantyItem, AsBuilt, Commissioning
"""

from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from pydantic import Field

from .common import (
    Comment,
    CompanyFull,
    ContactFull,
    CostItemStatus,
    CSICode,
    DistributionEntry,
    KahuaBaseModel,
    KahuaFile,
    Location,
    OutwardReference,
    WorkflowInfo,
)


class WarrantyItemModel(KahuaBaseModel):
    """
    Warranty item entity model.
    Entity Definition: kahua_Closeout.WarrantyItem
    """

    # Identification
    number: Optional[str] = Field(default=None, alias="Number")
    warranty_number: Optional[str] = Field(default=None, alias="WarrantyNumber")
    name: Optional[str] = Field(default=None, alias="Name")
    description: Optional[str] = Field(default=None, alias="Description")
    
    # Status
    status: Optional[CostItemStatus] = Field(default=None, alias="Status")
    warranty_status: Optional[str] = Field(default=None, alias="WarrantyStatus")
    
    # Classification
    warranty_type: Optional[str] = Field(default=None, alias="WarrantyType")
    category: Optional[str] = Field(default=None, alias="Category")
    csi_code: Optional[CSICode] = Field(default=None, alias="CSICode")
    
    # Item covered
    item_covered: Optional[str] = Field(default=None, alias="ItemCovered")
    equipment: Optional[str] = Field(default=None, alias="Equipment")
    system: Optional[str] = Field(default=None, alias="System")
    location: Optional[Location] = Field(default=None, alias="Location")
    
    # Dates
    start_date: Optional[date] = Field(default=None, alias="StartDate")
    end_date: Optional[date] = Field(default=None, alias="EndDate")
    duration_months: Optional[int] = Field(default=None, alias="DurationMonths")
    substantial_completion: Optional[date] = Field(default=None, alias="SubstantialCompletion")
    
    # Is active
    is_active: Optional[bool] = Field(default=None, alias="IsActive")
    is_expired: Optional[bool] = Field(default=None, alias="IsExpired")
    days_remaining: Optional[int] = Field(default=None, alias="DaysRemaining")
    
    # Warranty holder
    warranty_holder: Optional[CompanyFull] = Field(default=None, alias="WarrantyHolder")
    contractor: Optional[CompanyFull] = Field(default=None, alias="Contractor")
    manufacturer: Optional[CompanyFull] = Field(default=None, alias="Manufacturer")
    
    # Contact info
    warranty_contact: Optional[ContactFull] = Field(default=None, alias="WarrantyContact")
    service_phone: Optional[str] = Field(default=None, alias="ServicePhone")
    service_email: Optional[str] = Field(default=None, alias="ServiceEmail")
    
    # Coverage
    coverage_description: Optional[str] = Field(default=None, alias="CoverageDescription")
    exclusions: Optional[str] = Field(default=None, alias="Exclusions")
    terms_and_conditions: Optional[str] = Field(default=None, alias="TermsAndConditions")
    
    # Related
    related_asset: Optional[OutwardReference] = Field(default=None, alias="RelatedAsset")
    
    # Documents
    warranty_document: Optional[KahuaFile] = Field(default=None, alias="WarrantyDocument")
    attachments: Optional[List[KahuaFile]] = Field(default=None, alias="Attachments")
    
    notes: Optional[str] = Field(default=None, alias="Notes")

    entity_def: str = Field(default="kahua_Closeout.WarrantyItem", exclude=True)


class WarrantyClaimModel(KahuaBaseModel):
    """
    Warranty claim entity model.
    Entity Definition: kahua_Closeout.WarrantyClaim
    """

    # Identification
    number: Optional[str] = Field(default=None, alias="Number")
    claim_number: Optional[str] = Field(default=None, alias="ClaimNumber")
    subject: Optional[str] = Field(default=None, alias="Subject")
    description: Optional[str] = Field(default=None, alias="Description")
    
    # Status
    status: Optional[CostItemStatus] = Field(default=None, alias="Status")
    claim_status: Optional[str] = Field(default=None, alias="ClaimStatus")
    
    # Related warranty
    warranty_item: Optional[OutwardReference] = Field(default=None, alias="WarrantyItem")
    
    # Issue details
    issue_description: Optional[str] = Field(default=None, alias="IssueDescription")
    defect_type: Optional[str] = Field(default=None, alias="DefectType")
    location: Optional[Location] = Field(default=None, alias="Location")
    
    # Dates
    date_reported: Optional[date] = Field(default=None, alias="DateReported")
    date_submitted: Optional[date] = Field(default=None, alias="DateSubmitted")
    date_resolved: Optional[date] = Field(default=None, alias="DateResolved")
    
    # People
    reported_by: Optional[ContactFull] = Field(default=None, alias="ReportedBy")
    assigned_to: Optional[ContactFull] = Field(default=None, alias="AssignedTo")
    
    # Resolution
    resolution: Optional[str] = Field(default=None, alias="Resolution")
    work_performed: Optional[str] = Field(default=None, alias="WorkPerformed")
    
    # Is covered
    is_covered: Optional[bool] = Field(default=None, alias="IsCovered")
    denial_reason: Optional[str] = Field(default=None, alias="DenialReason")
    
    # Photos and attachments
    photos: Optional[List[KahuaFile]] = Field(default=None, alias="Photos")
    attachments: Optional[List[KahuaFile]] = Field(default=None, alias="Attachments")
    
    # Comments
    comments: Optional[List[Comment]] = Field(default=None, alias="Comments")
    
    notes: Optional[str] = Field(default=None, alias="Notes")

    entity_def: str = Field(default="kahua_Closeout.WarrantyClaim", exclude=True)


class AsBuiltModel(KahuaBaseModel):
    """
    As-built document entity model.
    Entity Definition: kahua_Closeout.AsBuilt
    """

    # Identification
    number: Optional[str] = Field(default=None, alias="Number")
    drawing_number: Optional[str] = Field(default=None, alias="DrawingNumber")
    title: Optional[str] = Field(default=None, alias="Title")
    description: Optional[str] = Field(default=None, alias="Description")
    
    # Status
    status: Optional[CostItemStatus] = Field(default=None, alias="Status")
    review_status: Optional[str] = Field(default=None, alias="ReviewStatus")
    
    # Classification
    document_type: Optional[str] = Field(default=None, alias="DocumentType")
    discipline: Optional[str] = Field(default=None, alias="Discipline")
    csi_code: Optional[CSICode] = Field(default=None, alias="CSICode")
    
    # Dates
    date_submitted: Optional[date] = Field(default=None, alias="DateSubmitted")
    date_reviewed: Optional[date] = Field(default=None, alias="DateReviewed")
    date_accepted: Optional[date] = Field(default=None, alias="DateAccepted")
    
    # People
    submitted_by: Optional[ContactFull] = Field(default=None, alias="SubmittedBy")
    reviewed_by: Optional[ContactFull] = Field(default=None, alias="ReviewedBy")
    
    # Company
    contractor: Optional[CompanyFull] = Field(default=None, alias="Contractor")
    
    # File
    file: Optional[KahuaFile] = Field(default=None, alias="File")
    attachments: Optional[List[KahuaFile]] = Field(default=None, alias="Attachments")
    
    # Review comments
    review_comments: Optional[str] = Field(default=None, alias="ReviewComments")
    
    notes: Optional[str] = Field(default=None, alias="Notes")

    entity_def: str = Field(default="kahua_Closeout.AsBuilt", exclude=True)


class OperationsManualModel(KahuaBaseModel):
    """
    Operations and maintenance manual entity model.
    Entity Definition: kahua_Closeout.OMManual
    """

    # Identification
    number: Optional[str] = Field(default=None, alias="Number")
    name: Optional[str] = Field(default=None, alias="Name")
    title: Optional[str] = Field(default=None, alias="Title")
    description: Optional[str] = Field(default=None, alias="Description")
    
    # Status
    status: Optional[CostItemStatus] = Field(default=None, alias="Status")
    review_status: Optional[str] = Field(default=None, alias="ReviewStatus")
    
    # Classification
    manual_type: Optional[str] = Field(default=None, alias="ManualType")
    system: Optional[str] = Field(default=None, alias="System")
    equipment: Optional[str] = Field(default=None, alias="Equipment")
    csi_code: Optional[CSICode] = Field(default=None, alias="CSICode")
    
    # Dates
    date_submitted: Optional[date] = Field(default=None, alias="DateSubmitted")
    date_reviewed: Optional[date] = Field(default=None, alias="DateReviewed")
    date_accepted: Optional[date] = Field(default=None, alias="DateAccepted")
    
    # People
    submitted_by: Optional[ContactFull] = Field(default=None, alias="SubmittedBy")
    reviewed_by: Optional[ContactFull] = Field(default=None, alias="ReviewedBy")
    
    # Company
    contractor: Optional[CompanyFull] = Field(default=None, alias="Contractor")
    manufacturer: Optional[CompanyFull] = Field(default=None, alias="Manufacturer")
    
    # File
    file: Optional[KahuaFile] = Field(default=None, alias="File")
    attachments: Optional[List[KahuaFile]] = Field(default=None, alias="Attachments")
    
    notes: Optional[str] = Field(default=None, alias="Notes")

    entity_def: str = Field(default="kahua_Closeout.OMManual", exclude=True)


class CommissioningItemModel(KahuaBaseModel):
    """
    Commissioning item entity model.
    Entity Definition: kahua_Closeout.CommissioningItem
    """

    # Identification
    number: Optional[str] = Field(default=None, alias="Number")
    item_number: Optional[str] = Field(default=None, alias="ItemNumber")
    name: Optional[str] = Field(default=None, alias="Name")
    description: Optional[str] = Field(default=None, alias="Description")
    
    # Status
    status: Optional[CostItemStatus] = Field(default=None, alias="Status")
    commissioning_status: Optional[str] = Field(default=None, alias="CommissioningStatus")
    test_result: Optional[str] = Field(default=None, alias="TestResult")  # Pass, Fail, N/A
    
    # Classification
    commissioning_type: Optional[str] = Field(default=None, alias="CommissioningType")
    system: Optional[str] = Field(default=None, alias="System")
    equipment: Optional[str] = Field(default=None, alias="Equipment")
    csi_code: Optional[CSICode] = Field(default=None, alias="CSICode")
    
    # Location
    location: Optional[Location] = Field(default=None, alias="Location")
    
    # Dates
    scheduled_date: Optional[date] = Field(default=None, alias="ScheduledDate")
    actual_date: Optional[date] = Field(default=None, alias="ActualDate")
    
    # People
    commissioning_agent: Optional[ContactFull] = Field(default=None, alias="CommissioningAgent")
    witnessed_by: Optional[ContactFull] = Field(default=None, alias="WitnessedBy")
    
    # Company
    contractor: Optional[CompanyFull] = Field(default=None, alias="Contractor")
    
    # Test details
    test_procedure: Optional[str] = Field(default=None, alias="TestProcedure")
    acceptance_criteria: Optional[str] = Field(default=None, alias="AcceptanceCriteria")
    test_results: Optional[str] = Field(default=None, alias="TestResults")
    deficiencies: Optional[str] = Field(default=None, alias="Deficiencies")
    
    # Attachments
    test_report: Optional[KahuaFile] = Field(default=None, alias="TestReport")
    attachments: Optional[List[KahuaFile]] = Field(default=None, alias="Attachments")
    
    # Comments
    comments: Optional[List[Comment]] = Field(default=None, alias="Comments")
    
    notes: Optional[str] = Field(default=None, alias="Notes")

    entity_def: str = Field(default="kahua_Closeout.CommissioningItem", exclude=True)


class CloseoutChecklistModel(KahuaBaseModel):
    """
    Closeout checklist entity model.
    Entity Definition: kahua_Closeout.CloseoutChecklist
    """

    # Identification
    number: Optional[str] = Field(default=None, alias="Number")
    name: Optional[str] = Field(default=None, alias="Name")
    description: Optional[str] = Field(default=None, alias="Description")
    
    # Status
    status: Optional[CostItemStatus] = Field(default=None, alias="Status")
    percent_complete: Optional[float] = Field(default=None, alias="PercentComplete")
    
    # Classification
    checklist_type: Optional[str] = Field(default=None, alias="ChecklistType")
    
    # Company
    contractor: Optional[CompanyFull] = Field(default=None, alias="Contractor")
    
    # Items
    total_items: Optional[int] = Field(default=None, alias="TotalItems")
    completed_items: Optional[int] = Field(default=None, alias="CompletedItems")
    pending_items: Optional[int] = Field(default=None, alias="PendingItems")
    
    # Required documents
    warranties_received: Optional[bool] = Field(default=None, alias="WarrantiesReceived")
    as_builts_received: Optional[bool] = Field(default=None, alias="AsBuiltsReceived")
    om_manuals_received: Optional[bool] = Field(default=None, alias="OManualsReceived")
    training_complete: Optional[bool] = Field(default=None, alias="TrainingComplete")
    commissioning_complete: Optional[bool] = Field(default=None, alias="CommissioningComplete")
    punch_list_complete: Optional[bool] = Field(default=None, alias="PunchListComplete")
    final_inspection_complete: Optional[bool] = Field(default=None, alias="FinalInspectionComplete")
    lien_waivers_received: Optional[bool] = Field(default=None, alias="LienWaiversReceived")
    
    # Attachments
    attachments: Optional[List[KahuaFile]] = Field(default=None, alias="Attachments")
    
    notes: Optional[str] = Field(default=None, alias="Notes")

    entity_def: str = Field(default="kahua_Closeout.CloseoutChecklist", exclude=True)


def _rebuild_models() -> None:
    """Rebuild models to resolve forward references."""
    models = [
        WarrantyItemModel,
        WarrantyClaimModel,
        AsBuiltModel,
        OperationsManualModel,
        CommissioningItemModel,
        CloseoutChecklistModel,
    ]
    for model in models:
        if hasattr(model, "model_rebuild"):
            model.model_rebuild()


_rebuild_models()
