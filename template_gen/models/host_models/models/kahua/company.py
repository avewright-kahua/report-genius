"""
Company and Office entity models for Kahua Portable View templates.
Entities: kahua_CompanyManager.kahua_Company, kahua_CompanyManager.kahua_Office
"""

from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from pydantic import AnyUrl, Field

from .common import (
    ContactShortLabel,
    KahuaBaseModel,
    KahuaFile,
    Tag,
)


class CertificationModel(KahuaBaseModel):
    """
    Company certification model.
    Entity Definition: kahua_CompanyManager.kahua_Certification
    """

    name: Optional[str] = None
    certification_type: Optional[str] = None
    certifying_agency: Optional[str] = None
    certification_number: Optional[str] = None
    issue_date: Optional[date] = None
    expiration_date: Optional[date] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None
    attachments: Optional[List[KahuaFile]] = None

    entity_def: str = Field(default="kahua_CompanyManager.kahua_Certification", exclude=True)


class OfficeModel(KahuaBaseModel):
    """
    Office entity model.
    Entity Definition: kahua_CompanyManager.kahua_Office
    """

    name: Optional[str] = None
    address: Optional[str] = None
    address2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    phone: Optional[str] = None
    fax: Optional[str] = None
    is_headquarters: Optional[bool] = None
    office_type: Optional[str] = None
    notes: Optional[str] = None
    
    # Parent company reference (set after CompanyModel is defined)
    company_id: Optional[int] = None

    entity_def: str = Field(default="kahua_CompanyManager.kahua_Office", exclude=True)


class CompanyModel(KahuaBaseModel):
    """
    Company entity model.
    Entity Definition: kahua_CompanyManager.kahua_Company
    """

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
    
    # Business identifiers
    government_id: Optional[str] = None
    vendor_number: Optional[str] = None
    db_no: Optional[str] = Field(default=None, alias="DBNo")
    duns_number: Optional[str] = Field(default=None, alias="DUNSNumber")
    tax_id: Optional[str] = None
    
    # Company info
    company_type: Optional[str] = None
    is_published: Optional[bool] = None
    is_active: Optional[bool] = None
    is_preferred: Optional[bool] = None
    
    # Related entities
    offices: Optional[List[OfficeModel]] = None
    certifications: Optional[List[CertificationModel]] = None
    primary_contact: Optional[ContactShortLabel] = None
    tags: Optional[List[Tag]] = None
    
    # Description
    description: Optional[str] = None
    notes: Optional[str] = None
    
    # Insurance/bonding
    insurance_expiration_date: Optional[date] = None
    bonding_capacity: Optional[str] = None
    
    # Logo
    logo: Optional[KahuaFile] = None

    entity_def: str = Field(default="kahua_CompanyManager.kahua_Company", exclude=True)


def _rebuild_models() -> None:
    """Rebuild models to resolve forward references."""
    models = [CertificationModel, OfficeModel, CompanyModel]
    for model in models:
        if hasattr(model, "model_rebuild"):
            model.model_rebuild()


_rebuild_models()
