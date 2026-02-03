"""
Project (Domain Partition) entity model for Kahua Portable View templates.
Entity: kahua_Core.kahua_DomainPartition
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import AnyUrl, Field

from .common import (
    CompanyFull,
    ContactFull,
    KahuaBaseModel,
    KahuaFile,
    Location,
    Tag,
    WorkBreakdownItem,
)


class ProjectPhaseModel(KahuaBaseModel):
    """Project phase/stage model."""

    name: Optional[str] = None
    phase_type: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[str] = None
    percent_complete: Optional[Decimal] = None
    notes: Optional[str] = None


class ProjectModel(KahuaBaseModel):
    """
    Project (Domain Partition) entity model.
    Entity Definition: kahua_Core.kahua_DomainPartition
    """

    # Basic info
    name: Optional[str] = None
    number: Optional[str] = None
    description: Optional[str] = None
    
    # Address
    address: Optional[str] = None
    address2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    
    # Dates
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    planned_start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    actual_start_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    substantial_completion_date: Optional[date] = None
    final_completion_date: Optional[date] = None
    
    # Status
    status: Optional[str] = None
    phase: Optional[str] = None
    project_type: Optional[str] = None
    delivery_method: Optional[str] = None
    
    # Financial
    budget: Optional[Decimal] = None
    contract_value: Optional[Decimal] = None
    current_contract_value: Optional[Decimal] = None
    square_footage: Optional[Decimal] = None
    
    # Team
    owner: Optional[CompanyFull] = None
    owner_representative: Optional[ContactFull] = None
    project_manager: Optional[ContactFull] = None
    superintendent: Optional[ContactFull] = None
    architect: Optional[CompanyFull] = None
    engineer: Optional[CompanyFull] = None
    general_contractor: Optional[CompanyFull] = None
    construction_manager: Optional[CompanyFull] = None
    
    # Related entities
    locations: Optional[List[Location]] = None
    work_breakdown: Optional[List[WorkBreakdownItem]] = None
    phases: Optional[List[ProjectPhaseModel]] = None
    tags: Optional[List[Tag]] = None
    
    # Files
    project_image: Optional[KahuaFile] = None
    attachments: Optional[List[KahuaFile]] = None
    
    # Metadata
    time_zone: Optional[str] = None
    currency_code: Optional[str] = None
    notes: Optional[str] = None
    
    # Universal lookups
    universal_lookup1: Optional[str] = None
    universal_lookup2: Optional[str] = None
    universal_lookup3: Optional[str] = None
    universal_lookup4: Optional[str] = None
    universal_lookup5: Optional[str] = None

    entity_def: str = Field(default="kahua_Core.kahua_DomainPartition", exclude=True)


class ProjectSummaryModel(KahuaBaseModel):
    """
    Project summary model with aggregated data.
    Entity Definition: kahua_ProjectSummary.ProjectSummary
    """

    project: Optional[ProjectModel] = None
    total_rfis: Optional[int] = None
    open_rfis: Optional[int] = None
    total_submittals: Optional[int] = None
    open_submittals: Optional[int] = None
    total_change_orders: Optional[int] = None
    pending_change_orders: Optional[int] = None
    total_cost: Optional[Decimal] = None
    committed_cost: Optional[Decimal] = None
    actual_cost: Optional[Decimal] = None
    budget_variance: Optional[Decimal] = None
    schedule_variance_days: Optional[int] = None
    percent_complete: Optional[Decimal] = None

    entity_def: str = Field(default="kahua_ProjectSummary.ProjectSummary", exclude=True)


class ProgramSummaryModel(KahuaBaseModel):
    """
    Program summary model (multiple projects).
    Entity Definition: kahua_ProgramSummary.ProgramSummary
    """

    name: Optional[str] = None
    description: Optional[str] = None
    projects: Optional[List[ProjectModel]] = None
    total_budget: Optional[Decimal] = None
    total_actual_cost: Optional[Decimal] = None
    total_committed_cost: Optional[Decimal] = None
    total_projects: Optional[int] = None
    active_projects: Optional[int] = None

    entity_def: str = Field(default="kahua_ProgramSummary.ProgramSummary", exclude=True)


def _rebuild_models() -> None:
    """Rebuild models to resolve forward references."""
    models = [ProjectPhaseModel, ProjectModel, ProjectSummaryModel, ProgramSummaryModel]
    for model in models:
        if hasattr(model, "model_rebuild"):
            model.model_rebuild()


_rebuild_models()
