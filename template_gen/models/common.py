"""
Common Pydantic models shared across Kahua entity types.

These models represent reusable structures like Person, Company, Office,
Address, Location, Comment, and Certification that appear in multiple
entity definitions.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import AnyUrl, BaseModel, EmailStr, Field

JSONDict = Dict[str, Any]


def _to_pascal(value: str) -> str:
    """Convert snake_case to PascalCase for Kahua API compatibility."""
    parts = value.split("_")
    return "".join(part[:1].upper() + part[1:] for part in parts if part)


class KahuaBaseModel(BaseModel):
    """Base model with PascalCase alias generation for Kahua compatibility."""

    class Config:
        alias_generator = _to_pascal
        populate_by_name = True


# -----------------------------------------------------------------------------
# Address Models
# -----------------------------------------------------------------------------


class Address(KahuaBaseModel):
    """Physical address with full geographic details."""

    address1: Optional[str] = None
    address2: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    country_code: Optional[str] = None
    county_region: Optional[str] = None
    county_region_code: Optional[str] = None
    full: Optional[str] = None
    state_province: Optional[str] = None
    state_province_code: Optional[str] = None
    inline_address: Optional[str] = None
    town: Optional[str] = None
    locality: Optional[str] = None
    postal_code: Optional[str] = None


# -----------------------------------------------------------------------------
# Office Models
# -----------------------------------------------------------------------------


class Office(KahuaBaseModel):
    """Company office with contact information."""

    name: Optional[str] = None
    address: Optional[Address] = None
    office_email: Optional[EmailStr] = None
    primary: Optional[str] = None
    alternate: Optional[str] = None
    fax: Optional[str] = None
    short_label: Optional[str] = None
    long_label: Optional[str] = None


# -----------------------------------------------------------------------------
# Company Models
# -----------------------------------------------------------------------------


class Company(KahuaBaseModel):
    """Organization/company with identification and contact details."""

    name: Optional[str] = None
    legal_name: Optional[str] = None
    government_id: Optional[str] = None
    db_no: Optional[str] = Field(default=None, alias="DBNo")
    vendor_number: Optional[str] = None
    website: Optional[AnyUrl] = None
    company_email: Optional[EmailStr] = None
    primary_office: Optional[Office] = None
    offices: Optional[List[Office]] = None
    short_label: Optional[str] = None
    long_label: Optional[str] = None


# -----------------------------------------------------------------------------
# Person / Contact Models
# -----------------------------------------------------------------------------


class Person(KahuaBaseModel):
    """Individual contact with full details."""

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    prefix: Optional[str] = None
    suffix: Optional[str] = None
    title: Optional[str] = None
    company: Optional[str] = None
    office: Optional[str] = None
    email_address: Optional[EmailStr] = None
    direct: Optional[str] = None
    mobile: Optional[str] = None
    fax: Optional[str] = None
    contact_company_label: Optional[str] = None
    contact_full_name_label: Optional[str] = None
    company_contact_label: Optional[str] = None
    short_label: Optional[str] = None
    long_label: Optional[str] = None


class ContactShortLabel(KahuaBaseModel):
    """Minimal contact reference with just display label."""

    short_label: Optional[str] = None


class ContactFull(KahuaBaseModel):
    """Full contact with display labels and email."""

    short_label: Optional[str] = None
    long_label: Optional[str] = None
    contact_company_label: Optional[str] = None
    company_contact_label: Optional[str] = None
    contact_full_name_label: Optional[str] = None
    email_address: Optional[EmailStr] = None
    title: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    prefix: Optional[str] = None
    suffix: Optional[str] = None
    company: Optional[str] = None
    office: Optional[str] = None
    direct: Optional[str] = None
    mobile: Optional[str] = None
    fax: Optional[str] = None


# -----------------------------------------------------------------------------
# Location Models
# -----------------------------------------------------------------------------


class Location(KahuaBaseModel):
    """Physical location with spatial and descriptive attributes."""

    address: Optional[Address] = None
    attachments: Optional[List[JSONDict]] = None
    name: Optional[str] = None
    description: Optional[str] = None
    notes: Optional[str] = None
    type_: Optional[str] = Field(default=None, alias="Type")
    short_label: Optional[str] = None
    long_label: Optional[str] = None
    omni_class_code: Optional[str] = None
    floor_type: Optional[str] = None
    zone_type: Optional[str] = None
    spaces: Optional[List[JSONDict]] = None
    project_name: Optional[str] = None
    site_name: Optional[str] = None
    linear_units: Optional[str] = None
    area_units: Optional[str] = None
    volume_units: Optional[str] = None
    area_measurement: Optional[str] = None
    phase: Optional[str] = None
    elevation: Optional[Decimal] = None
    height: Optional[Decimal] = None
    room_tag: Optional[str] = None
    usable_height: Optional[Decimal] = None
    gross_area: Optional[Decimal] = None
    net_area: Optional[Decimal] = None
    qr_code_count: Optional[int] = Field(default=None, alias="QRCodeCount")
    qr_code_indicator: Optional[str] = Field(default=None, alias="QRCodeIndicator")


# -----------------------------------------------------------------------------
# Comment Models
# -----------------------------------------------------------------------------


class Comment(KahuaBaseModel):
    """User comment with attribution and timestamp."""

    contact: Optional[ContactFull] = None
    comment: Optional[str] = None
    comment_created_date_time: Optional[datetime] = None


class SecondaryComment(KahuaBaseModel):
    """Secondary/response comment with minimal attribution."""

    contact: Optional[ContactShortLabel] = None
    comment: Optional[str] = None
    created_date_time: Optional[datetime] = None


# -----------------------------------------------------------------------------
# Certification Models
# -----------------------------------------------------------------------------


class Certification(KahuaBaseModel):
    """Professional or compliance certification."""

    issuing_agency: Optional[str] = None
    jurisdiction: Optional[str] = None
    reference_number: Optional[str] = None
    classification: Optional[str] = None
    type_: Optional[str] = Field(default=None, alias="Type")
    issued_date: Optional[date] = None
    expiration_date: Optional[date] = None
    url_link: Optional[AnyUrl] = None
    applies_to_all_offices: Optional[bool] = None
    offices: Optional[List[Office]] = None
    notes: Optional[str] = None
    short_label: Optional[str] = None
    long_label: Optional[str] = None


# -----------------------------------------------------------------------------
# Distribution / Notification Models
# -----------------------------------------------------------------------------


class DistributionEntry(KahuaBaseModel):
    """Distribution list entry for routing documents."""

    type_: Optional[str] = Field(default=None, alias="Type")
    group_name: Optional[str] = None
    group_partition_id: Optional[int] = None
    email: Optional[EmailStr] = None
    community_contact_key: Optional[str] = None
    local_contact_key: Optional[str] = None
    label: Optional[str] = None
    domain_key: Optional[str] = None
    personal_domain_key: Optional[str] = None
    short_label: Optional[str] = None
    contact_company_label: Optional[str] = None
    contact: Optional[ContactShortLabel] = None


class NotificationEntry(DistributionEntry):
    """Notification recipient entry (extends DistributionEntry)."""

    pass


# -----------------------------------------------------------------------------
# File / Attachment Models
# -----------------------------------------------------------------------------


class CurrentFile(KahuaBaseModel):
    """File metadata for attachments."""

    version: Optional[int] = None
    file_name: Optional[str] = None
    size_in_bytes: Optional[int] = None
    extension: Optional[str] = None
    created_domain_user_id: Optional[int] = None
    created_date_time: Optional[datetime] = None
    has_markups: Optional[bool] = None
    markup_source: Optional[str] = None
    preview_status_id: Optional[int] = None
    page_count: Optional[int] = None
    created_by_display_name: Optional[str] = None
    markup_file: Optional["MarkupFile"] = None


class MarkupFile(KahuaBaseModel):
    """Markup/annotation file reference."""

    current_file: Optional[CurrentFile] = None


class SourceFile(KahuaBaseModel):
    """Source file reference."""

    current_file: Optional[CurrentFile] = None


class OutwardReference(KahuaBaseModel):
    """External reference to another entity or file."""

    source_file: Optional[SourceFile] = None
    description: Optional[str] = None
    reference_type: Optional[str] = None
    created_date: Optional[str] = None


# -----------------------------------------------------------------------------
# Code / Classification Models
# -----------------------------------------------------------------------------


class CSICode(KahuaBaseModel):
    """CSI (Construction Specifications Institute) classification code."""

    short_label: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None


class CostCodeIndex(KahuaBaseModel):
    """Cost code classification for budget tracking."""

    code: Optional[str] = None
    description: Optional[str] = None
    short_label: Optional[str] = None
    long_label: Optional[str] = None


class WorkBreakdownItem(KahuaBaseModel):
    """Work breakdown structure item."""

    short_label: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None


class WorkPackage(KahuaBaseModel):
    """Work package grouping."""

    short_label: Optional[str] = None
    title: Optional[str] = None


# -----------------------------------------------------------------------------
# Cost Item Models
# -----------------------------------------------------------------------------


class CostItemIndex(KahuaBaseModel):
    """Cost item tracking with financial metadata."""

    external_links: Optional[List[JSONDict]] = None
    outward_references: Optional[List[OutwardReference]] = None
    participant_task_index: Optional[JSONDict] = None
    entity_link_url: Optional[AnyUrl] = None
    description: Optional[str] = None
    sort_order: Optional[int] = None
    is_tax_item: Optional[bool] = None
    default_tax_rate: Optional[Decimal] = None
    is_taxable: Optional[bool] = None


# -----------------------------------------------------------------------------
# Project Models (for project-level token access)
# -----------------------------------------------------------------------------


class ProjectContact(KahuaBaseModel):
    """Project role contact (Owner, Architect, PM, etc.)."""

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    prefix: Optional[str] = None
    suffix: Optional[str] = None
    title: Optional[str] = None
    company: Optional[str] = None
    office: Optional[str] = None
    email_address: Optional[EmailStr] = None
    direct: Optional[str] = None
    mobile: Optional[str] = None
    fax: Optional[str] = None
    contact_company_label: Optional[str] = None
    contact_full_name_label: Optional[str] = None
    company_contact_label: Optional[str] = None
    short_label: Optional[str] = None
    long_label: Optional[str] = None


class ProjectProperty(KahuaBaseModel):
    """Property associated with a project."""

    property_name: Optional[str] = None
    property_id: Optional[str] = Field(default=None, alias="PropertyID")
    state: Optional[str] = None
    address1: Optional[str] = None
    address2: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    region: Optional[str] = None


class Project(KahuaBaseModel):
    """Project context for entity tokens."""

    number: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    contract_no: Optional[str] = None
    type_: Optional[str] = Field(default=None, alias="Type")
    project_status: Optional[str] = None
    address: Optional[Address] = None
    schedule_start: Optional[date] = None
    schedule_end: Optional[date] = None
    owner: Optional[ProjectContact] = None
    architect: Optional[ProjectContact] = None
    contractor_cm: Optional[ProjectContact] = Field(default=None, alias="ContractorCM")
    owners_rep: Optional[ProjectContact] = None
    project_executive: Optional[ProjectContact] = None
    project_manager: Optional[ProjectContact] = None
    project_engineer: Optional[ProjectContact] = None
    project_admin: Optional[ProjectContact] = None
    superintendent: Optional[ProjectContact] = None
    planning_number: Optional[str] = None
    property_id: Optional[ProjectProperty] = Field(default=None, alias="PropertyID")
    custom_project_number1: Optional[str] = None
    custom_project_number2: Optional[str] = None
    custom_project_number3: Optional[str] = None
    custom_project_number4: Optional[str] = None
    custom_project_number5: Optional[str] = None
    custom_lookup1: Optional[str] = None
    custom_lookup2: Optional[str] = None
    custom_lookup3: Optional[str] = None
    custom_lookup4: Optional[str] = None
    custom_lookup5: Optional[str] = None
    custom_count1: Optional[int] = None
    custom_count2: Optional[int] = None
    custom_count3: Optional[int] = None
    custom_count4: Optional[int] = None
    custom_count5: Optional[int] = None


# -----------------------------------------------------------------------------
# Forward Reference Resolution
# -----------------------------------------------------------------------------


def _rebuild_models() -> None:
    """Rebuild models to resolve forward references."""
    models = [
        CurrentFile,
        MarkupFile,
        SourceFile,
        OutwardReference,
        Location,
    ]
    for model in models:
        if hasattr(model, "model_rebuild"):
            model.model_rebuild()


_rebuild_models()
