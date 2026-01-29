"""
Submittal entity model for Kahua Portable View templates.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import Field

from .common import (
    ContactFull,
    ContactShortLabel,
    CSICode,
    KahuaBaseModel,
    Location,
)

JSONDict = Dict[str, Any]


class ContactLabel(KahuaBaseModel):
    """Contact with short label and company label."""

    short_label: Optional[str] = None
    contact_company_label: Optional[str] = None


class Contributor(KahuaBaseModel):
    """File contributor reference."""

    short_label: Optional[str] = None


class FileComment(KahuaBaseModel):
    """Comment on a file attachment."""

    contact: Optional[ContactFull] = None
    comment: Optional[str] = None
    comment_created_date_time: Optional[datetime] = None


class MarkupFile(KahuaBaseModel):
    """Markup/annotation file reference."""

    current_file: Optional["FileCurrent"] = None


class FileCurrent(KahuaBaseModel):
    file_id: Optional[int] = None
    guid: Optional[UUID] = None
    version: Optional[int] = None
    file_name: Optional[str] = None
    size_in_bytes: Optional[int] = None
    extension: Optional[str] = None
    created_domain_user_id: Optional[int] = None
    created_date_time: Optional[datetime] = None
    security_scan_status_id: Optional[int] = None
    last_security_scan_date: Optional[datetime] = None
    is_markup_enabled: Optional[bool] = None
    has_markups: Optional[bool] = None
    markup_source: Optional[str] = None
    is_document: Optional[bool] = None
    preview_status_id: Optional[int] = None
    page_count: Optional[int] = None
    created_default_domain_id: Optional[int] = None
    created_by_display_name: Optional[str] = None
    created_by_person_id: Optional[UUID] = None
    view_name: Optional[str] = None
    report_name: Optional[str] = None
    contribution_date_time: Optional[datetime] = None
    contributor: Optional[Contributor] = None
    comments: Optional[List[FileComment]] = None
    markup_file: Optional[MarkupFile] = None


class PortableView(KahuaBaseModel):
    current_file: Optional[FileCurrent] = None


class SourceFile(KahuaBaseModel):
    current_file: Optional[FileCurrent] = None


class SourceEntity(KahuaBaseModel):
    short_label: Optional[str] = None


class CompositeReferenceItem(KahuaBaseModel):
    display_order: Optional[int] = None
    reference_original_instance_id: Optional[int] = None
    reference: Optional[JSONDict] = None


class SubmittalOutwardReference(KahuaBaseModel):
    """External reference from a submittal to another entity or file."""

    composite_requires_render: Optional[bool] = None
    description: Optional[str] = None
    create_source: Optional[str] = None
    creator_domain_key: Optional[str] = None
    include_on_send: Optional[bool] = None
    include_markup_on_send: Optional[bool] = None
    include_in_default_composite: Optional[bool] = None
    is_composite: Optional[bool] = None
    is_current: Optional[bool] = None
    is_removed: Optional[bool] = None
    reference_type: Optional[str] = None
    source_entity: Optional[SourceEntity] = None
    reference_entity: Optional[JSONDict] = None
    source_file: Optional[SourceFile] = None
    source_last_updated: Optional[datetime] = None
    original_instance_id: Optional[int] = None
    composite_reference_items: Optional[List[CompositeReferenceItem]] = None
    is_template: Optional[bool] = None
    is_document_source: Optional[bool] = None


class SubmittalItem(KahuaBaseModel):
    """Individual submittal item within a submittal package."""

    id: Optional[int] = None
    number: Optional[str] = None
    revision: Optional[Decimal] = None
    package_number: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    category: Optional[str] = None
    type_: Optional[str] = Field(default=None, alias="Type")
    location: Optional[Location] = None
    csi_code: Optional[CSICode] = Field(default=None, alias="CSICode")
    submitting_vendor: Optional[ContactLabel] = None
    submittal_coordinator: Optional[ContactLabel] = None
    lead_time: Optional[int] = None
    is_critical_path: Optional[bool] = None
    is_material_tracking: Optional[bool] = None
    is_as_specified: Optional[bool] = None
    reviewers: Optional[List[ContactFull]] = None
    portable_view: Optional[PortableView] = None
    official_reviewer: Optional[ContactLabel] = None
    response: Optional[str] = None
    response_notes: Optional[str] = None
    submission_due_date: Optional[date] = None
    date_submitted_by_vendor: Optional[date] = None
    date_sent_to_reviewers: Optional[date] = None
    review_period: Optional[int] = None
    response_due_date: Optional[date] = None
    reviewer_response_date: Optional[date] = None
    date_returned_to_vendor: Optional[date] = None
    date_required_onsite: Optional[date] = None
    outward_references: Optional[List[SubmittalOutwardReference]] = None


class ReviewItem(KahuaBaseModel):
    """Review action on a submittal."""

    reviewer: Optional[ContactFull] = None
    response: Optional[str] = None
    response_date: Optional[date] = None
    comments: Optional[str] = None


class SubmittalDistributionEntry(KahuaBaseModel):
    """Distribution entry for submittal routing."""

    type_: Optional[str] = Field(default=None, alias="Type")
    contact: Optional[ContactShortLabel] = None
    short_label: Optional[str] = None
    email: Optional[str] = None


class SubmittalModel(KahuaBaseModel):
    """
    Submittal entity for construction document submissions.

    Tracks submittal packages with items, review workflow, and distribution.
    """

    # Entity Definition (for template generator)
    entity_def: str = Field(default="kahua.submittal", exclude=True)

    # Identification
    number: Optional[str] = None
    revision: Optional[Decimal] = None
    description: Optional[str] = None
    status: Optional[str] = None
    category: Optional[str] = None
    type_: Optional[str] = Field(default=None, alias="Type")

    # Classification
    csi_code: Optional[CSICode] = Field(default=None, alias="CSICode")
    location: Optional[Location] = None

    # Contacts
    submitting_vendor: Optional[ContactLabel] = None
    submittal_coordinator: Optional[ContactLabel] = None
    official_reviewer: Optional[ContactLabel] = None
    reviewers: Optional[List[ContactFull]] = None

    # Flags
    is_critical_path: Optional[bool] = None
    is_material_tracking: Optional[bool] = None
    is_as_specified: Optional[bool] = None
    lead_time: Optional[int] = None
    review_period: Optional[int] = None

    # Response
    response: Optional[str] = None
    response_notes: Optional[str] = None

    # Key Dates
    submission_due_date: Optional[date] = None
    date_submitted_by_vendor: Optional[date] = None
    date_sent_to_reviewers: Optional[date] = None
    response_due_date: Optional[date] = None
    reviewer_response_date: Optional[date] = None
    date_returned_to_vendor: Optional[date] = None
    date_required_onsite: Optional[date] = None

    # Items and References
    items: Optional[List[SubmittalItem]] = None
    review_items: Optional[List[ReviewItem]] = None
    outward_references: Optional[List[SubmittalOutwardReference]] = None
    portable_view: Optional[PortableView] = None

    # Distribution
    distribution: Optional[List[SubmittalDistributionEntry]] = None
    notification: Optional[List[SubmittalDistributionEntry]] = None

    # Notes
    notes: Optional[str] = None


def _rebuild_models() -> None:
    """Rebuild models to resolve forward references."""
    models = [
        MarkupFile,
        FileCurrent,
        PortableView,
        SourceFile,
        SubmittalOutwardReference,
        SubmittalItem,
        SubmittalModel,
    ]
    for model in models:
        if hasattr(model, "model_rebuild"):
            model.model_rebuild()


_rebuild_models()
