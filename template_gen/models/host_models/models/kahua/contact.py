"""
Contact entity model for Kahua Portable View templates.
Entity: kahua_PeopleManager.kahua_Contact
"""

from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from pydantic import AnyUrl, Field

from .common import (
    CompanyFull,
    KahuaBaseModel,
    KahuaFile,
    OfficeFull,
    Tag,
)


class ContactModel(KahuaBaseModel):
    """
    Contact entity model.
    Entity Definition: kahua_PeopleManager.kahua_Contact
    """

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email_address: Optional[str] = None
    direct: Optional[str] = None
    mobile: Optional[str] = None
    fax: Optional[str] = None
    title: Optional[str] = None
    prefix: Optional[str] = None
    suffix: Optional[str] = None
    contact_company_label: Optional[str] = None
    company: Optional[CompanyFull] = None
    office: Optional[OfficeFull] = None
    profile_photo: Optional[KahuaFile] = None
    
    # Additional contact attributes
    department: Optional[str] = None
    job_title: Optional[str] = None
    is_active: Optional[bool] = None
    is_internal: Optional[bool] = None
    last_login_date: Optional[datetime] = None
    tags: Optional[List[Tag]] = None
    notes: Optional[str] = None
    
    # Social/web
    linkedin_url: Optional[AnyUrl] = None
    twitter_handle: Optional[str] = None
    
    # Entity Definition (for template generator)
    entity_def: str = Field(default="kahua_PeopleManager.kahua_Contact", exclude=True)


class PartitionContactModel(KahuaBaseModel):
    """
    Partition contact (project team member) model.
    Entity Definition: kahua_Core.kahua_PartitionContact
    """

    contact: Optional[ContactModel] = None
    role: Optional[str] = None
    is_primary: Optional[bool] = None
    is_active: Optional[bool] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    notes: Optional[str] = None

    entity_def: str = Field(default="kahua_Core.kahua_PartitionContact", exclude=True)


def _rebuild_models() -> None:
    """Rebuild models to resolve forward references."""
    models = [ContactModel, PartitionContactModel]
    for model in models:
        if hasattr(model, "model_rebuild"):
            model.model_rebuild()


_rebuild_models()
