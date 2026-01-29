"""
Field Observation Item entity model for Kahua Portable View templates.

Represents field observations/inspections with location, classification,
and documentation references.
"""

from __future__ import annotations

from datetime import date
from typing import List, Optional

from pydantic import Field

from .common import (
    Comment,
    ContactFull,
    ContactShortLabel,
    CSICode,
    KahuaBaseModel,
    Location,
    NotificationEntry,
    OutwardReference,
)


class ObservedByContact(KahuaBaseModel):
    """Contact who made the observation."""

    short_label: Optional[str] = None


class CompanyRef(KahuaBaseModel):
    """Company reference with name."""

    name: Optional[str] = None


class FieldObservationModel(KahuaBaseModel):
    """
    Field Observation Item entity for site inspections and observations.

    Tracks observations made during field visits including location,
    classification, and related documentation.
    """

    # Entity Definition (for template generator)
    entity_def: str = Field(default="kahua.fieldobservationitem", exclude=True)

    # Identification
    number: Optional[str] = None
    subject: Optional[str] = None
    status: Optional[str] = None
    type_: Optional[str] = Field(default=None, alias="Type")

    # Classification
    csi_code: Optional[CSICode] = Field(default=None, alias="CSICode")

    # Observation Details
    date: Optional[date] = None
    observed_by: Optional[ObservedByContact] = None
    company: Optional[CompanyRef] = None
    location: Optional[Location] = None

    # Descriptive
    description: Optional[str] = None
    notes: Optional[str] = None

    # Custom Lookups
    universal_lookup1: Optional[str] = None
    universal_lookup2: Optional[str] = None
    universal_lookup3: Optional[str] = None
    universal_lookup4: Optional[str] = None
    universal_lookup5: Optional[str] = None

    # References & Attachments
    outward_references: Optional[List[OutwardReference]] = None

    # Notifications
    cc_notification: Optional[List[NotificationEntry]] = Field(
        default=None, alias="CCNotification"
    )


def _rebuild_models() -> None:
    """Rebuild models to resolve forward references."""
    models = [FieldObservationModel]
    for model in models:
        if hasattr(model, "model_rebuild"):
            model.model_rebuild()


_rebuild_models()
