"""
Document and file entity models for Kahua Portable View templates.
Entities: kahua_Documents.Document, Folder, DrawingLog
"""

from __future__ import annotations

from datetime import date as DateType, datetime as DateTimeType
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


class FolderModel(KahuaBaseModel):
    """
    Folder entity model.
    Entity Definition: kahua_Documents.Folder
    """

    # Identification
    name: Optional[str] = Field(default=None, alias="Name")
    path: Optional[str] = Field(default=None, alias="Path")
    description: Optional[str] = Field(default=None, alias="Description")
    
    # Parent/child
    parent_folder: Optional[OutwardReference] = Field(default=None, alias="ParentFolder")
    child_folders: Optional[List[OutwardReference]] = Field(default=None, alias="ChildFolders")
    
    # Permissions
    is_public: Optional[bool] = Field(default=None, alias="IsPublic")
    permissions: Optional[str] = Field(default=None, alias="Permissions")
    
    # Metadata
    created_by: Optional[ContactFull] = Field(default=None, alias="CreatedBy")
    created_date: Optional[DateType] = Field(default=None, alias="CreatedDate")
    modified_by: Optional[ContactFull] = Field(default=None, alias="ModifiedBy")
    modified_date: Optional[DateType] = Field(default=None, alias="ModifiedDate")
    
    # Counts
    document_count: Optional[int] = Field(default=None, alias="DocumentCount")
    folder_count: Optional[int] = Field(default=None, alias="FolderCount")

    entity_def: str = Field(default="kahua_Documents.Folder", exclude=True)


class DocumentVersionModel(KahuaBaseModel):
    """Document version entry."""

    version_number: Optional[str] = Field(default=None, alias="VersionNumber")
    version_label: Optional[str] = Field(default=None, alias="VersionLabel")
    description: Optional[str] = Field(default=None, alias="Description")
    
    # File info
    file: Optional[KahuaFile] = Field(default=None, alias="File")
    file_name: Optional[str] = Field(default=None, alias="FileName")
    file_size: Optional[int] = Field(default=None, alias="FileSize")
    file_type: Optional[str] = Field(default=None, alias="FileType")
    
    # Dates
    uploaded_date: Optional[DateTimeType] = Field(default=None, alias="UploadedDate")
    uploaded_by: Optional[ContactFull] = Field(default=None, alias="UploadedBy")
    
    is_current: Optional[bool] = Field(default=None, alias="IsCurrent")
    notes: Optional[str] = Field(default=None, alias="Notes")


class DocumentModel(KahuaBaseModel):
    """
    Document entity model.
    Entity Definition: kahua_Documents.Document
    """

    # Identification
    number: Optional[str] = Field(default=None, alias="Number")
    document_number: Optional[str] = Field(default=None, alias="DocumentNumber")
    name: Optional[str] = Field(default=None, alias="Name")
    title: Optional[str] = Field(default=None, alias="Title")
    description: Optional[str] = Field(default=None, alias="Description")
    
    # Status
    status: Optional[CostItemStatus] = Field(default=None, alias="Status")
    document_status: Optional[str] = Field(default=None, alias="DocumentStatus")
    
    # Classification
    document_type: Optional[str] = Field(default=None, alias="DocumentType")
    document_category: Optional[str] = Field(default=None, alias="DocumentCategory")
    discipline: Optional[str] = Field(default=None, alias="Discipline")
    csi_code: Optional[CSICode] = Field(default=None, alias="CSICode")
    
    # File info
    file: Optional[KahuaFile] = Field(default=None, alias="File")
    file_name: Optional[str] = Field(default=None, alias="FileName")
    file_extension: Optional[str] = Field(default=None, alias="FileExtension")
    file_size: Optional[int] = Field(default=None, alias="FileSize")
    mime_type: Optional[str] = Field(default=None, alias="MimeType")
    
    # Version info
    version: Optional[str] = Field(default=None, alias="Version")
    revision: Optional[str] = Field(default=None, alias="Revision")
    revision_number: Optional[int] = Field(default=None, alias="RevisionNumber")
    versions: Optional[List[DocumentVersionModel]] = Field(default=None, alias="Versions")
    version_count: Optional[int] = Field(default=None, alias="VersionCount")
    
    # Folder
    folder: Optional[FolderModel] = Field(default=None, alias="Folder")
    folder_path: Optional[str] = Field(default=None, alias="FolderPath")
    
    # Dates
    document_date: Optional[DateType] = Field(default=None, alias="DocumentDate")
    date_created: Optional[DateType] = Field(default=None, alias="DateCreated")
    date_uploaded: Optional[DateTimeType] = Field(default=None, alias="DateUploaded")
    date_modified: Optional[DateTimeType] = Field(default=None, alias="DateModified")
    date_approved: Optional[DateType] = Field(default=None, alias="DateApproved")
    effective_date: Optional[DateType] = Field(default=None, alias="EffectiveDate")
    expiration_date: Optional[DateType] = Field(default=None, alias="ExpirationDate")
    
    # People
    author: Optional[ContactFull] = Field(default=None, alias="Author")
    created_by: Optional[ContactFull] = Field(default=None, alias="CreatedBy")
    uploaded_by: Optional[ContactFull] = Field(default=None, alias="UploadedBy")
    modified_by: Optional[ContactFull] = Field(default=None, alias="ModifiedBy")
    approved_by: Optional[ContactFull] = Field(default=None, alias="ApprovedBy")
    owner: Optional[ContactFull] = Field(default=None, alias="Owner")
    
    # Company
    originating_company: Optional[CompanyFull] = Field(default=None, alias="OriginatingCompany")
    
    # Access control
    is_public: Optional[bool] = Field(default=None, alias="IsPublic")
    is_confidential: Optional[bool] = Field(default=None, alias="IsConfidential")
    access_level: Optional[str] = Field(default=None, alias="AccessLevel")
    
    # Related items
    related_documents: Optional[List[OutwardReference]] = Field(default=None, alias="RelatedDocuments")
    supersedes: Optional[OutwardReference] = Field(default=None, alias="Supersedes")
    superseded_by: Optional[OutwardReference] = Field(default=None, alias="SupersededBy")
    
    # Distribution
    distribution: Optional[List[DistributionEntry]] = Field(default=None, alias="Distribution")
    
    # Keywords and tags
    keywords: Optional[List[str]] = Field(default=None, alias="Keywords")
    tags: Optional[List[str]] = Field(default=None, alias="Tags")
    
    # Comments
    comments: Optional[List[Comment]] = Field(default=None, alias="Comments")
    
    # Workflow
    workflow_info: Optional[WorkflowInfo] = Field(default=None, alias="WorkflowInfo")
    approval_info: Optional[ApprovalInfo] = Field(default=None, alias="ApprovalInfo")
    
    # Notes
    notes: Optional[str] = Field(default=None, alias="Notes")

    entity_def: str = Field(default="kahua_Documents.Document", exclude=True)


class DrawingModel(KahuaBaseModel):
    """
    Drawing entity model.
    Entity Definition: kahua_Drawings.Drawing or kahua_AEC_DrawingLog.Drawing
    """

    # Identification
    number: Optional[str] = Field(default=None, alias="Number")
    drawing_number: Optional[str] = Field(default=None, alias="DrawingNumber")
    sheet_number: Optional[str] = Field(default=None, alias="SheetNumber")
    title: Optional[str] = Field(default=None, alias="Title")
    name: Optional[str] = Field(default=None, alias="Name")
    description: Optional[str] = Field(default=None, alias="Description")
    
    # Status
    status: Optional[CostItemStatus] = Field(default=None, alias="Status")
    drawing_status: Optional[str] = Field(default=None, alias="DrawingStatus")
    
    # Version/Revision
    revision: Optional[str] = Field(default=None, alias="Revision")
    revision_number: Optional[int] = Field(default=None, alias="RevisionNumber")
    revision_date: Optional[DateType] = Field(default=None, alias="RevisionDate")
    revision_description: Optional[str] = Field(default=None, alias="RevisionDescription")
    
    # Classification
    discipline: Optional[str] = Field(default=None, alias="Discipline")
    drawing_type: Optional[str] = Field(default=None, alias="DrawingType")
    drawing_set: Optional[str] = Field(default=None, alias="DrawingSet")
    phase: Optional[str] = Field(default=None, alias="Phase")
    csi_code: Optional[CSICode] = Field(default=None, alias="CSICode")
    
    # File info
    file: Optional[KahuaFile] = Field(default=None, alias="File")
    file_name: Optional[str] = Field(default=None, alias="FileName")
    file_format: Optional[str] = Field(default=None, alias="FileFormat")  # PDF, DWG, etc.
    
    # Paper info
    paper_size: Optional[str] = Field(default=None, alias="PaperSize")
    scale: Optional[str] = Field(default=None, alias="Scale")
    
    # Dates
    date_issued: Optional[DateType] = Field(default=None, alias="DateIssued")
    date_received: Optional[DateType] = Field(default=None, alias="DateReceived")
    date_created: Optional[DateType] = Field(default=None, alias="DateCreated")
    
    # People
    drawn_by: Optional[ContactFull] = Field(default=None, alias="DrawnBy")
    designed_by: Optional[ContactFull] = Field(default=None, alias="DesignedBy")
    checked_by: Optional[ContactFull] = Field(default=None, alias="CheckedBy")
    approved_by: Optional[ContactFull] = Field(default=None, alias="ApprovedBy")
    
    # Company/Origin
    originator: Optional[CompanyFull] = Field(default=None, alias="Originator")
    architect: Optional[CompanyFull] = Field(default=None, alias="Architect")
    engineer: Optional[CompanyFull] = Field(default=None, alias="Engineer")
    
    # Related drawings
    references: Optional[List[str]] = Field(default=None, alias="References")
    related_drawings: Optional[List[OutwardReference]] = Field(default=None, alias="RelatedDrawings")
    supersedes: Optional[OutwardReference] = Field(default=None, alias="Supersedes")
    
    # Version history
    revisions: Optional[List[DocumentVersionModel]] = Field(default=None, alias="Revisions")
    
    # Attachments
    attachments: Optional[List[KahuaFile]] = Field(default=None, alias="Attachments")
    
    # Comments
    comments: Optional[List[Comment]] = Field(default=None, alias="Comments")
    
    notes: Optional[str] = Field(default=None, alias="Notes")

    entity_def: str = Field(default="kahua_Drawings.Drawing", exclude=True)


class TransmittalItemModel(KahuaBaseModel):
    """Transmittal item entry."""

    item_number: Optional[str] = Field(default=None, alias="ItemNumber")
    document: Optional[OutwardReference] = Field(default=None, alias="Document")
    drawing: Optional[OutwardReference] = Field(default=None, alias="Drawing")
    
    description: Optional[str] = Field(default=None, alias="Description")
    copies: Optional[int] = Field(default=None, alias="Copies")
    revision: Optional[str] = Field(default=None, alias="Revision")
    
    action_required: Optional[str] = Field(default=None, alias="ActionRequired")
    remarks: Optional[str] = Field(default=None, alias="Remarks")


class TransmittalModel(KahuaBaseModel):
    """
    Transmittal entity model.
    Entity Definition: kahua_Transmittals.Transmittal
    """

    # Identification
    number: Optional[str] = Field(default=None, alias="Number")
    transmittal_number: Optional[str] = Field(default=None, alias="TransmittalNumber")
    subject: Optional[str] = Field(default=None, alias="Subject")
    description: Optional[str] = Field(default=None, alias="Description")
    
    # Status
    status: Optional[CostItemStatus] = Field(default=None, alias="Status")
    transmittal_type: Optional[str] = Field(default=None, alias="TransmittalType")
    
    # Dates
    date: Optional[DateType] = Field(default=None, alias="Date")
    transmittal_date: Optional[DateType] = Field(default=None, alias="TransmittalDate")
    date_sent: Optional[DateType] = Field(default=None, alias="DateSent")
    date_received: Optional[DateType] = Field(default=None, alias="DateReceived")
    response_due: Optional[DateType] = Field(default=None, alias="ResponseDue")
    
    # People
    from_contact: Optional[ContactFull] = Field(default=None, alias="From")
    to_contact: Optional[ContactFull] = Field(default=None, alias="To")
    sent_by: Optional[ContactFull] = Field(default=None, alias="SentBy")
    prepared_by: Optional[ContactFull] = Field(default=None, alias="PreparedBy")
    
    # Companies
    from_company: Optional[CompanyFull] = Field(default=None, alias="FromCompany")
    to_company: Optional[CompanyFull] = Field(default=None, alias="ToCompany")
    
    # Items
    items: Optional[List[TransmittalItemModel]] = Field(default=None, alias="Items")
    item_count: Optional[int] = Field(default=None, alias="ItemCount")
    
    # Delivery
    delivery_method: Optional[str] = Field(default=None, alias="DeliveryMethod")
    tracking_number: Optional[str] = Field(default=None, alias="TrackingNumber")
    carrier: Optional[str] = Field(default=None, alias="Carrier")
    
    # Purpose/Action
    purpose: Optional[str] = Field(default=None, alias="Purpose")
    action_required: Optional[str] = Field(default=None, alias="ActionRequired")
    
    # Distribution
    distribution: Optional[List[DistributionEntry]] = Field(default=None, alias="Distribution")
    cc_list: Optional[List[ContactFull]] = Field(default=None, alias="CCList")
    
    # Attachments
    attachments: Optional[List[KahuaFile]] = Field(default=None, alias="Attachments")
    
    # Comments
    comments: Optional[List[Comment]] = Field(default=None, alias="Comments")
    
    # Workflow
    workflow_info: Optional[WorkflowInfo] = Field(default=None, alias="WorkflowInfo")
    
    # Notes
    notes: Optional[str] = Field(default=None, alias="Notes")
    remarks: Optional[str] = Field(default=None, alias="Remarks")

    entity_def: str = Field(default="kahua_Transmittals.Transmittal", exclude=True)


def _rebuild_models() -> None:
    """Rebuild models to resolve forward references."""
    models = [
        FolderModel,
        DocumentVersionModel,
        DocumentModel,
        DrawingModel,
        TransmittalItemModel,
        TransmittalModel,
    ]
    for model in models:
        if hasattr(model, "model_rebuild"):
            model.model_rebuild()


_rebuild_models()
