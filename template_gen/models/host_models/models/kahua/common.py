"""
Common base models and shared types for Kahua Portable View templates.
"""

from __future__ import annotations

from datetime import date as DateType, datetime as DateTimeType
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union

from pydantic import AnyUrl, BaseModel, ConfigDict, Field

# Re-export for convenience  
date = DateType
datetime = DateTimeType


class KahuaBaseModel(BaseModel):
    """Base model for all Kahua entities with common configuration."""

    model_config = ConfigDict(
        populate_by_name=True,
        use_enum_values=True,
        str_strip_whitespace=True,
        extra="allow",
    )

    # Common base entity attributes
    id: Optional[int] = None
    created_by: Optional[ContactShortLabel] = None
    created_date_time: Optional[datetime] = None
    modified_date_time: Optional[datetime] = None
    domain_partition_id: Optional[int] = None
    short_label: Optional[str] = None
    long_label: Optional[str] = None
    detail_label: Optional[str] = None


class ContactShortLabel(BaseModel):
    """Minimal contact reference with short label."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    id: Optional[int] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email_address: Optional[str] = None
    short_label: Optional[str] = None


class ContactFull(BaseModel):
    """Full contact model with all attributes."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    id: Optional[int] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email_address: Optional[str] = None
    direct: Optional[str] = None
    mobile: Optional[str] = None
    fax: Optional[str] = None
    title: Optional[str] = None
    prefix: Optional[str] = None
    suffix: Optional[str] = None
    short_label: Optional[str] = None
    contact_company_label: Optional[str] = None
    company: Optional[CompanyShortLabel] = None
    office: Optional[OfficeShortLabel] = None
    profile_photo: Optional[KahuaFile] = None


class CompanyShortLabel(BaseModel):
    """Minimal company reference."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    id: Optional[int] = None
    name: Optional[str] = None
    short_label: Optional[str] = None


class CompanyFull(BaseModel):
    """Full company model with all attributes."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    id: Optional[int] = None
    name: Optional[str] = None
    address: Optional[str] = None
    address2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    phone: Optional[str] = None
    fax: Optional[str] = None
    website: Optional[AnyUrl] = None
    short_label: Optional[str] = None
    government_id: Optional[str] = None
    vendor_number: Optional[str] = None
    db_no: Optional[str] = Field(default=None, alias="DBNo")
    is_published: Optional[bool] = None


class OfficeShortLabel(BaseModel):
    """Minimal office reference."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    id: Optional[int] = None
    name: Optional[str] = None
    short_label: Optional[str] = None


class OfficeFull(BaseModel):
    """Full office model."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    id: Optional[int] = None
    name: Optional[str] = None
    address: Optional[str] = None
    address2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    phone: Optional[str] = None
    fax: Optional[str] = None
    short_label: Optional[str] = None
    company: Optional[CompanyShortLabel] = None


class Location(BaseModel):
    """Location reference model."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    id: Optional[int] = None
    name: Optional[str] = None
    type: Optional[str] = None
    description: Optional[str] = None
    notes: Optional[str] = None
    short_label: Optional[str] = None
    parent: Optional[Location] = None


class CSICode(BaseModel):
    """CSI Code reference model."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    id: Optional[int] = None
    code: Optional[str] = None
    description: Optional[str] = None
    short_label: Optional[str] = None


class KahuaFile(BaseModel):
    """File attachment model."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    id: Optional[int] = None
    name: Optional[str] = None
    extension: Optional[str] = None
    size: Optional[int] = None
    created_date_time: Optional[datetime] = None
    contributor: Optional[str] = None
    short_label: Optional[str] = None


class CurrentFile(BaseModel):
    """Current file reference for documents."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    id: Optional[int] = None
    name: Optional[str] = None
    extension: Optional[str] = None
    size: Optional[int] = None
    revision: Optional[str] = None
    version: Optional[int] = None


class SourceFile(BaseModel):
    """Source file reference."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    id: Optional[int] = None
    name: Optional[str] = None
    extension: Optional[str] = None
    short_label: Optional[str] = None


class MarkupFile(BaseModel):
    """Markup/annotation file reference."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    id: Optional[int] = None
    name: Optional[str] = None
    markup_type: Optional[str] = None


class Comment(BaseModel):
    """Comment model."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    id: Optional[int] = None
    text: Optional[str] = None
    author: Optional[ContactShortLabel] = None
    created_date_time: Optional[datetime] = None


class SecondaryComment(BaseModel):
    """Secondary comment model with additional metadata."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    id: Optional[int] = None
    text: Optional[str] = None
    author: Optional[ContactFull] = None
    created_date_time: Optional[datetime] = None
    comment_type: Optional[str] = None
    is_internal: Optional[bool] = None


class DistributionEntry(BaseModel):
    """Distribution list entry (message participant)."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    id: Optional[int] = None
    contact: Optional[ContactFull] = None
    participation_type: Optional[str] = None
    is_read: Optional[bool] = None
    read_date_time: Optional[datetime] = None


class NotificationEntry(BaseModel):
    """Notification list entry."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    id: Optional[int] = None
    contact: Optional[ContactFull] = None
    notification_type: Optional[str] = None


class OutwardReference(BaseModel):
    """Outward reference to another entity."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    id: Optional[int] = None
    reference_type: Optional[str] = None
    reference_label: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None


class WorkPackage(BaseModel):
    """Work package reference."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    id: Optional[int] = None
    name: Optional[str] = None
    number: Optional[str] = None
    description: Optional[str] = None
    short_label: Optional[str] = None


class DomainPartition(BaseModel):
    """Domain partition (project) reference."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    id: Optional[int] = None
    name: Optional[str] = None
    number: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    short_label: Optional[str] = None


class CostItemStatus(BaseModel):
    """Cost item status model."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    id: Optional[int] = None
    name: Optional[str] = None
    status_type: Optional[str] = None
    is_closed: Optional[bool] = None
    short_label: Optional[str] = None


class WorkBreakdownSegment(BaseModel):
    """Work breakdown structure segment."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    id: Optional[int] = None
    name: Optional[str] = None
    code: Optional[str] = None
    level: Optional[int] = None
    parent: Optional[WorkBreakdownSegment] = None
    short_label: Optional[str] = None


class WorkBreakdownItem(BaseModel):
    """Work breakdown structure item."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    id: Optional[int] = None
    name: Optional[str] = None
    number: Optional[str] = None
    description: Optional[str] = None
    budget_amount: Optional[Decimal] = None
    segments: Optional[List[WorkBreakdownSegment]] = None
    short_label: Optional[str] = None


class CurrencyValue(BaseModel):
    """Currency value with formatting info."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    amount: Optional[Decimal] = None
    currency_code: Optional[str] = None
    formatted: Optional[str] = None


class ApprovalInfo(BaseModel):
    """Approval information."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    id: Optional[int] = None
    approver: Optional[ContactFull] = None
    approval_date: Optional[datetime] = None
    approval_status: Optional[str] = None
    comments: Optional[str] = None


class WorkflowInfo(BaseModel):
    """Workflow information."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    id: Optional[int] = None
    workflow_name: Optional[str] = None
    current_step: Optional[str] = None
    status: Optional[str] = None
    started_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None


class Tag(BaseModel):
    """Tag/label reference."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    id: Optional[int] = None
    name: Optional[str] = None
    color: Optional[str] = None


class ExternalLink(BaseModel):
    """External link reference."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    id: Optional[int] = None
    name: Optional[str] = None
    url: Optional[AnyUrl] = None
    description: Optional[str] = None


# Update forward references
def _rebuild_common_models() -> None:
    """Rebuild models to resolve forward references."""
    models = [
        ContactShortLabel,
        ContactFull,
        CompanyShortLabel,
        CompanyFull,
        OfficeShortLabel,
        OfficeFull,
        Location,
        KahuaBaseModel,
        WorkBreakdownSegment,
    ]
    for model in models:
        if hasattr(model, "model_rebuild"):
            model.model_rebuild()


_rebuild_common_models()
