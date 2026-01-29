"""
RFI (Request for Information) entity model for Kahua Portable View templates.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import AnyUrl, Field

from .common import (
    Comment,
    ContactFull,
    ContactShortLabel,
    CSICode,
    CurrentFile,
    DistributionEntry,
    KahuaBaseModel,
    Location,
    MarkupFile,
    NotificationEntry,
    OutwardReference,
    SecondaryComment,
    SourceFile,
    WorkPackage,
)


class SourceCompany(KahuaBaseModel):
    """Company that originated the RFI."""

    government_id: Optional[str] = None
    db_no: Optional[str] = Field(default=None, alias="DBNo")
    is_published: Optional[bool] = None
    name: Optional[str] = None
    short_label: Optional[str] = None
    vendor_number: Optional[str] = None
    website: Optional[AnyUrl] = None


class RFIModel(KahuaBaseModel):
    author: Optional[ContactFull] = None
    cost_effect: Optional[str] = None
    date: Optional[date] = None
    date_responded: Optional[date] = None
    due_date: Optional[date] = None
    date_sent: Optional[date] = None
    csi_code: Optional[CSICode] = Field(default=None, alias="CSICode")
    location: Optional[Location] = None
    number: Optional[str] = None
    official_responder: Optional[ContactFull] = None
    current_official_responder: Optional[ContactFull] = None
    responders: Optional[List[ContactFull]] = None
    distribution: Optional[List[DistributionEntry]] = None
    proposed_solution: Optional[str] = None
    question: Optional[str] = None
    project: Optional[str] = None
    reason: Optional[str] = None
    discipline: Optional[str] = None
    type_: Optional[str] = Field(default=None, alias="Type")
    reference: Optional[str] = None
    response: Optional[str] = None
    response_secondary: Optional[str] = None
    assigned_to: Optional[ContactFull] = None
    sheet_detail: Optional[str] = None
    status: Optional[str] = None
    subject: Optional[str] = None
    time_effect: Optional[str] = None
    is_unsubmitted: Optional[bool] = None
    notification: Optional[List[NotificationEntry]] = None
    cost_amount: Optional[Decimal] = None
    priority: Optional[str] = None
    source_company: Optional[SourceCompany] = None
    source_rfi: Optional[str] = Field(default=None, alias="SourceRFI")
    number_of_days: Optional[int] = None
    owner_representative: Optional[ContactFull] = None
    sent_to_owner_date: Optional[date] = None
    owner_responded_date: Optional[date] = None
    owner_remarks: Optional[str] = None
    autosend_to_official_responder: Optional[bool] = None
    instructions_to_official_responder: Optional[str] = None
    autosend_to_responders: Optional[bool] = None
    instructions_to_responders: Optional[str] = None
    responders_can_add_responders: Optional[bool] = None
    responders_see_all_responses: Optional[bool] = None
    notify_all_responders: Optional[bool] = None
    secondary_comments: Optional[List[SecondaryComment]] = None
    outward_references: Optional[List[OutwardReference]] = None
    notes: Optional[str] = None
    disclaimer: Optional[str] = None
    comments: Optional[List[Comment]] = None
    work_suspended: Optional[bool] = None
    completed_date: Optional[date] = None
    root_cause: Optional[str] = None
    work_package: Optional[WorkPackage] = None
    rfi_reference_number1: Optional[str] = Field(default=None, alias="RFIReferenceNumber1")
    rfi_reference_number2: Optional[str] = Field(default=None, alias="RFIReferenceNumber2")
    universal_lookup1: Optional[str] = None
    universal_lookup2: Optional[str] = None
    universal_lookup3: Optional[str] = None
    universal_lookup4: Optional[str] = None
    universal_lookup5: Optional[str] = None
    review_start_date: Optional[date] = None
    review_end_date: Optional[date] = None

    # Entity Definition (for template generator)
    entity_def: str = Field(default="kahua.rfi", exclude=True)


def _rebuild_models() -> None:
    """Rebuild models to resolve forward references."""
    models = [RFIModel]
    for model in models:
        if hasattr(model, "model_rebuild"):
            model.model_rebuild()


_rebuild_models()
