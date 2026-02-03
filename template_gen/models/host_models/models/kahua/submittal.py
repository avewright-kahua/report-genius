"""
Submittal entity models for Kahua Portable View templates.
Entities: kahua_AEC_Submittals.Submittal, SubmittalPackage, SubmittalItem
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


class SubmittalItemModel(KahuaBaseModel):
    """
    Individual submittal item within a package.
    Entity Definition: kahua_AEC_Submittals.SubmittalItem
    """

    # Identification
    number: Optional[str] = Field(default=None, alias="Number")
    item_number: Optional[str] = Field(default=None, alias="ItemNumber")
    description: Optional[str] = Field(default=None, alias="Description")
    status: Optional[CostItemStatus] = Field(default=None, alias="Status")
    
    # Classification
    spec_section: Optional[str] = Field(default=None, alias="SpecSection")
    csi_code: Optional[CSICode] = Field(default=None, alias="CSICode")
    submittal_type: Optional[str] = Field(default=None, alias="SubmittalType")
    
    # Quantities
    quantity: Optional[int] = Field(default=None, alias="Quantity")
    copies: Optional[int] = Field(default=None, alias="Copies")
    
    # Manufacturer/Product info
    manufacturer: Optional[str] = Field(default=None, alias="Manufacturer")
    model_number: Optional[str] = Field(default=None, alias="ModelNumber")
    product_name: Optional[str] = Field(default=None, alias="ProductName")
    catalog_number: Optional[str] = Field(default=None, alias="CatalogNumber")
    
    # Review result
    review_status: Optional[str] = Field(default=None, alias="ReviewStatus")
    review_action: Optional[str] = Field(default=None, alias="ReviewAction")
    review_comments: Optional[str] = Field(default=None, alias="ReviewComments")
    
    # Attachments
    attachments: Optional[List[KahuaFile]] = Field(default=None, alias="Attachments")
    
    notes: Optional[str] = Field(default=None, alias="Notes")

    entity_def: str = Field(default="kahua_AEC_Submittals.SubmittalItem", exclude=True)


class SubmittalModel(KahuaBaseModel):
    """
    Submittal entity model.
    Entity Definition: kahua_AEC_Submittals.Submittal
    """

    # Identification
    number: Optional[str] = Field(default=None, alias="Number")
    subject: Optional[str] = Field(default=None, alias="Subject")
    description: Optional[str] = Field(default=None, alias="Description")
    status: Optional[CostItemStatus] = Field(default=None, alias="Status")
    revision: Optional[str] = Field(default=None, alias="Revision")
    revision_number: Optional[int] = Field(default=None, alias="RevisionNumber")
    
    # Classification
    submittal_type: Optional[str] = Field(default=None, alias="SubmittalType")
    priority: Optional[str] = Field(default=None, alias="Priority")
    discipline: Optional[str] = Field(default=None, alias="Discipline")
    spec_section: Optional[str] = Field(default=None, alias="SpecSection")
    csi_code: Optional[CSICode] = Field(default=None, alias="CSICode")
    location: Optional[Location] = Field(default=None, alias="Location")
    
    # Dates
    date_initiated: Optional[date] = Field(default=None, alias="DateInitiated")
    date_submitted: Optional[date] = Field(default=None, alias="DateSubmitted")
    date_required: Optional[date] = Field(default=None, alias="DateRequired")
    date_due: Optional[date] = Field(default=None, alias="DateDue")
    date_received: Optional[date] = Field(default=None, alias="DateReceived")
    date_returned: Optional[date] = Field(default=None, alias="DateReturned")
    date_approved: Optional[date] = Field(default=None, alias="DateApproved")
    date_sent_for_review: Optional[date] = Field(default=None, alias="DateSentForReview")
    date_review_completed: Optional[date] = Field(default=None, alias="DateReviewCompleted")
    required_on_site: Optional[date] = Field(default=None, alias="RequiredOnSite")
    lead_time: Optional[int] = Field(default=None, alias="LeadTime")
    
    # People
    submitted_by: Optional[ContactFull] = Field(default=None, alias="SubmittedBy")
    from_contact: Optional[ContactFull] = Field(default=None, alias="From")
    to_contact: Optional[ContactFull] = Field(default=None, alias="To")
    assigned_to: Optional[ContactFull] = Field(default=None, alias="AssignedTo")
    reviewed_by: Optional[ContactFull] = Field(default=None, alias="ReviewedBy")
    approved_by: Optional[ContactFull] = Field(default=None, alias="ApprovedBy")
    responsible_party: Optional[ContactFull] = Field(default=None, alias="ResponsibleParty")
    ball_in_court: Optional[ContactFull] = Field(default=None, alias="BallInCourt")
    
    # Companies
    from_company: Optional[CompanyFull] = Field(default=None, alias="FromCompany")
    subcontractor: Optional[CompanyFull] = Field(default=None, alias="Subcontractor")
    gc_company: Optional[CompanyFull] = Field(default=None, alias="GCCompany")
    architect_company: Optional[CompanyFull] = Field(default=None, alias="ArchitectCompany")
    manufacturer: Optional[CompanyFull] = Field(default=None, alias="Manufacturer")
    
    # Manufacturer/Product info (string versions)
    manufacturer_name: Optional[str] = Field(default=None, alias="ManufacturerName")
    model_number: Optional[str] = Field(default=None, alias="ModelNumber")
    product_name: Optional[str] = Field(default=None, alias="ProductName")
    catalog_number: Optional[str] = Field(default=None, alias="CatalogNumber")
    
    # Quantities
    copies_required: Optional[int] = Field(default=None, alias="CopiesRequired")
    copies_received: Optional[int] = Field(default=None, alias="CopiesReceived")
    copies_returned: Optional[int] = Field(default=None, alias="CopiesReturned")
    
    # Review info
    review_status: Optional[str] = Field(default=None, alias="ReviewStatus")
    review_action: Optional[str] = Field(default=None, alias="ReviewAction")
    review_comments: Optional[str] = Field(default=None, alias="ReviewComments")
    approved_as: Optional[str] = Field(default=None, alias="ApprovedAs")
    
    # Drawing references
    drawing_reference: Optional[str] = Field(default=None, alias="DrawingReference")
    sheet_number: Optional[str] = Field(default=None, alias="SheetNumber")
    detail_number: Optional[str] = Field(default=None, alias="DetailNumber")
    
    # Items
    items: Optional[List[SubmittalItemModel]] = Field(default=None, alias="Items")
    
    # Related items
    related_rfis: Optional[List[OutwardReference]] = Field(default=None, alias="RelatedRFIs")
    related_submittals: Optional[List[OutwardReference]] = Field(default=None, alias="RelatedSubmittals")
    related_transmittals: Optional[List[OutwardReference]] = Field(default=None, alias="RelatedTransmittals")
    parent_package: Optional[OutwardReference] = Field(default=None, alias="ParentPackage")
    
    # Distribution
    distribution: Optional[List[DistributionEntry]] = Field(default=None, alias="Distribution")
    notification_list: Optional[List[NotificationEntry]] = Field(default=None, alias="NotificationList")
    cc_list: Optional[List[ContactFull]] = Field(default=None, alias="CCList")
    
    # Comments and attachments
    comments: Optional[List[Comment]] = Field(default=None, alias="Comments")
    secondary_comments: Optional[List[SecondaryComment]] = Field(default=None, alias="SecondaryComments")
    attachments: Optional[List[KahuaFile]] = Field(default=None, alias="Attachments")
    
    # Workflow
    workflow_info: Optional[WorkflowInfo] = Field(default=None, alias="WorkflowInfo")
    approval_info: Optional[ApprovalInfo] = Field(default=None, alias="ApprovalInfo")
    
    # Notes
    notes: Optional[str] = Field(default=None, alias="Notes")
    remarks: Optional[str] = Field(default=None, alias="Remarks")
    internal_notes: Optional[str] = Field(default=None, alias="InternalNotes")

    entity_def: str = Field(default="kahua_AEC_Submittals.Submittal", exclude=True)


class SubmittalPackageModel(KahuaBaseModel):
    """
    Submittal package containing multiple submittals.
    Entity Definition: kahua_AEC_Submittals.SubmittalPackage
    """

    # Identification
    number: Optional[str] = Field(default=None, alias="Number")
    package_number: Optional[str] = Field(default=None, alias="PackageNumber")
    subject: Optional[str] = Field(default=None, alias="Subject")
    description: Optional[str] = Field(default=None, alias="Description")
    status: Optional[CostItemStatus] = Field(default=None, alias="Status")
    
    # Classification
    package_type: Optional[str] = Field(default=None, alias="PackageType")
    discipline: Optional[str] = Field(default=None, alias="Discipline")
    spec_section: Optional[str] = Field(default=None, alias="SpecSection")
    
    # Dates
    date_created: Optional[date] = Field(default=None, alias="DateCreated")
    date_submitted: Optional[date] = Field(default=None, alias="DateSubmitted")
    date_due: Optional[date] = Field(default=None, alias="DateDue")
    date_received: Optional[date] = Field(default=None, alias="DateReceived")
    date_returned: Optional[date] = Field(default=None, alias="DateReturned")
    
    # People
    created_by: Optional[ContactFull] = Field(default=None, alias="CreatedBy")
    submitted_by: Optional[ContactFull] = Field(default=None, alias="SubmittedBy")
    assigned_to: Optional[ContactFull] = Field(default=None, alias="AssignedTo")
    
    # Companies
    from_company: Optional[CompanyFull] = Field(default=None, alias="FromCompany")
    to_company: Optional[CompanyFull] = Field(default=None, alias="ToCompany")
    
    # Submittals in package
    submittals: Optional[List[SubmittalModel]] = Field(default=None, alias="Submittals")
    submittal_count: Optional[int] = Field(default=None, alias="SubmittalCount")
    
    # Transmittal info
    transmittal_number: Optional[str] = Field(default=None, alias="TransmittalNumber")
    
    # Attachments and comments
    attachments: Optional[List[KahuaFile]] = Field(default=None, alias="Attachments")
    comments: Optional[List[Comment]] = Field(default=None, alias="Comments")
    
    notes: Optional[str] = Field(default=None, alias="Notes")

    entity_def: str = Field(default="kahua_AEC_Submittals.SubmittalPackage", exclude=True)


class SubmittalRegisterModel(KahuaBaseModel):
    """
    Submittal register entry.
    Entity Definition: kahua_AEC_Submittals.SubmittalRegister
    """

    number: Optional[str] = Field(default=None, alias="Number")
    spec_section: Optional[str] = Field(default=None, alias="SpecSection")
    description: Optional[str] = Field(default=None, alias="Description")
    submittal_type: Optional[str] = Field(default=None, alias="SubmittalType")
    responsible_party: Optional[CompanyFull] = Field(default=None, alias="ResponsibleParty")
    
    # Schedule
    scheduled_submit_date: Optional[date] = Field(default=None, alias="ScheduledSubmitDate")
    actual_submit_date: Optional[date] = Field(default=None, alias="ActualSubmitDate")
    required_on_site: Optional[date] = Field(default=None, alias="RequiredOnSite")
    lead_time: Optional[int] = Field(default=None, alias="LeadTime")
    
    # Status
    register_status: Optional[str] = Field(default=None, alias="RegisterStatus")
    
    # Related submittal
    submittal: Optional[OutwardReference] = Field(default=None, alias="Submittal")
    
    notes: Optional[str] = Field(default=None, alias="Notes")

    entity_def: str = Field(default="kahua_AEC_Submittals.SubmittalRegister", exclude=True)


def _rebuild_models() -> None:
    """Rebuild models to resolve forward references."""
    models = [
        SubmittalItemModel,
        SubmittalModel,
        SubmittalPackageModel,
        SubmittalRegisterModel,
    ]
    for model in models:
        if hasattr(model, "model_rebuild"):
            model.model_rebuild()


_rebuild_models()
