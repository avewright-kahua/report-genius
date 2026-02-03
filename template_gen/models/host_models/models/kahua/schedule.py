"""
Schedule entity models for Kahua Portable View templates.
Entities: kahua_Schedule.ScheduleTask, Milestone, Activity
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import Field

from .common import (
    Comment,
    CompanyFull,
    ContactFull,
    CostItemStatus,
    CSICode,
    KahuaBaseModel,
    KahuaFile,
    Location,
    OutwardReference,
    WorkBreakdownItem,
)


class ScheduleBaselineModel(KahuaBaseModel):
    """Schedule baseline entry."""

    baseline_number: Optional[int] = Field(default=None, alias="BaselineNumber")
    baseline_name: Optional[str] = Field(default=None, alias="BaselineName")
    description: Optional[str] = Field(default=None, alias="Description")
    
    baseline_date: Optional[date] = Field(default=None, alias="BaselineDate")
    baseline_start: Optional[date] = Field(default=None, alias="BaselineStart")
    baseline_finish: Optional[date] = Field(default=None, alias="BaselineFinish")
    baseline_duration: Optional[int] = Field(default=None, alias="BaselineDuration")
    
    is_active: Optional[bool] = Field(default=None, alias="IsActive")


class ResourceAssignmentModel(KahuaBaseModel):
    """Resource assignment to a schedule task."""

    resource_name: Optional[str] = Field(default=None, alias="ResourceName")
    resource_type: Optional[str] = Field(default=None, alias="ResourceType")  # Labor, Equipment, Material
    
    contact: Optional[ContactFull] = Field(default=None, alias="Contact")
    company: Optional[CompanyFull] = Field(default=None, alias="Company")
    
    # Allocation
    units: Optional[float] = Field(default=None, alias="Units")
    percent_allocation: Optional[float] = Field(default=None, alias="PercentAllocation")
    
    # Hours/Work
    planned_work: Optional[float] = Field(default=None, alias="PlannedWork")
    actual_work: Optional[float] = Field(default=None, alias="ActualWork")
    remaining_work: Optional[float] = Field(default=None, alias="RemainingWork")
    
    # Costs
    planned_cost: Optional[Decimal] = Field(default=None, alias="PlannedCost")
    actual_cost: Optional[Decimal] = Field(default=None, alias="ActualCost")
    
    # Dates
    start_date: Optional[date] = Field(default=None, alias="StartDate")
    finish_date: Optional[date] = Field(default=None, alias="FinishDate")


class ScheduleTaskModel(KahuaBaseModel):
    """
    Schedule task/activity entity model.
    Entity Definition: kahua_Schedule.ScheduleTask
    """

    # Identification
    task_id: Optional[str] = Field(default=None, alias="TaskId")
    number: Optional[str] = Field(default=None, alias="Number")
    wbs: Optional[str] = Field(default=None, alias="WBS")
    name: Optional[str] = Field(default=None, alias="Name")
    description: Optional[str] = Field(default=None, alias="Description")
    
    # Status
    status: Optional[CostItemStatus] = Field(default=None, alias="Status")
    task_status: Optional[str] = Field(default=None, alias="TaskStatus")
    is_complete: Optional[bool] = Field(default=None, alias="IsComplete")
    is_milestone: Optional[bool] = Field(default=None, alias="IsMilestone")
    is_summary: Optional[bool] = Field(default=None, alias="IsSummary")
    is_critical: Optional[bool] = Field(default=None, alias="IsCritical")
    
    # Classification
    task_type: Optional[str] = Field(default=None, alias="TaskType")
    activity_type: Optional[str] = Field(default=None, alias="ActivityType")
    phase: Optional[str] = Field(default=None, alias="Phase")
    csi_code: Optional[CSICode] = Field(default=None, alias="CSICode")
    work_breakdown_item: Optional[WorkBreakdownItem] = Field(default=None, alias="WorkBreakdownItem")
    
    # Location
    location: Optional[Location] = Field(default=None, alias="Location")
    
    # Dates - Planned
    planned_start: Optional[date] = Field(default=None, alias="PlannedStart")
    planned_finish: Optional[date] = Field(default=None, alias="PlannedFinish")
    early_start: Optional[date] = Field(default=None, alias="EarlyStart")
    early_finish: Optional[date] = Field(default=None, alias="EarlyFinish")
    late_start: Optional[date] = Field(default=None, alias="LateStart")
    late_finish: Optional[date] = Field(default=None, alias="LateFinish")
    
    # Dates - Actual
    actual_start: Optional[date] = Field(default=None, alias="ActualStart")
    actual_finish: Optional[date] = Field(default=None, alias="ActualFinish")
    
    # Dates - Baseline
    baseline_start: Optional[date] = Field(default=None, alias="BaselineStart")
    baseline_finish: Optional[date] = Field(default=None, alias="BaselineFinish")
    
    # Duration
    planned_duration: Optional[int] = Field(default=None, alias="PlannedDuration")
    actual_duration: Optional[int] = Field(default=None, alias="ActualDuration")
    remaining_duration: Optional[int] = Field(default=None, alias="RemainingDuration")
    baseline_duration: Optional[int] = Field(default=None, alias="BaselineDuration")
    duration_unit: Optional[str] = Field(default=None, alias="DurationUnit")  # Days, Hours, Weeks
    
    # Progress
    percent_complete: Optional[float] = Field(default=None, alias="PercentComplete")
    physical_percent_complete: Optional[float] = Field(default=None, alias="PhysicalPercentComplete")
    
    # Float/Slack
    total_float: Optional[int] = Field(default=None, alias="TotalFloat")
    free_float: Optional[int] = Field(default=None, alias="FreeFloat")
    
    # Variance
    start_variance: Optional[int] = Field(default=None, alias="StartVariance")
    finish_variance: Optional[int] = Field(default=None, alias="FinishVariance")
    duration_variance: Optional[int] = Field(default=None, alias="DurationVariance")
    
    # Constraints
    constraint_type: Optional[str] = Field(default=None, alias="ConstraintType")
    constraint_date: Optional[date] = Field(default=None, alias="ConstraintDate")
    deadline: Optional[date] = Field(default=None, alias="Deadline")
    
    # Dependencies
    predecessors: Optional[List[OutwardReference]] = Field(default=None, alias="Predecessors")
    successors: Optional[List[OutwardReference]] = Field(default=None, alias="Successors")
    predecessor_ids: Optional[List[str]] = Field(default=None, alias="PredecessorIds")
    successor_ids: Optional[List[str]] = Field(default=None, alias="SuccessorIds")
    
    # Hierarchy
    parent_task: Optional[OutwardReference] = Field(default=None, alias="ParentTask")
    child_tasks: Optional[List[OutwardReference]] = Field(default=None, alias="ChildTasks")
    outline_level: Optional[int] = Field(default=None, alias="OutlineLevel")
    
    # Responsibility
    assigned_to: Optional[ContactFull] = Field(default=None, alias="AssignedTo")
    responsible_party: Optional[ContactFull] = Field(default=None, alias="ResponsibleParty")
    responsible_company: Optional[CompanyFull] = Field(default=None, alias="ResponsibleCompany")
    
    # Resources
    resources: Optional[List[ResourceAssignmentModel]] = Field(default=None, alias="Resources")
    
    # Work
    planned_work: Optional[float] = Field(default=None, alias="PlannedWork")
    actual_work: Optional[float] = Field(default=None, alias="ActualWork")
    remaining_work: Optional[float] = Field(default=None, alias="RemainingWork")
    work_unit: Optional[str] = Field(default=None, alias="WorkUnit")
    
    # Cost
    planned_cost: Optional[Decimal] = Field(default=None, alias="PlannedCost")
    actual_cost: Optional[Decimal] = Field(default=None, alias="ActualCost")
    remaining_cost: Optional[Decimal] = Field(default=None, alias="RemainingCost")
    baseline_cost: Optional[Decimal] = Field(default=None, alias="BaselineCost")
    
    # Earned Value
    bcws: Optional[Decimal] = Field(default=None, alias="BCWS")  # Budgeted Cost of Work Scheduled
    bcwp: Optional[Decimal] = Field(default=None, alias="BCWP")  # Budgeted Cost of Work Performed
    acwp: Optional[Decimal] = Field(default=None, alias="ACWP")  # Actual Cost of Work Performed
    
    # Calendar
    calendar: Optional[str] = Field(default=None, alias="Calendar")
    
    # Baselines
    baselines: Optional[List[ScheduleBaselineModel]] = Field(default=None, alias="Baselines")
    
    # Attachments
    attachments: Optional[List[KahuaFile]] = Field(default=None, alias="Attachments")
    
    # Comments
    comments: Optional[List[Comment]] = Field(default=None, alias="Comments")
    
    # Notes
    notes: Optional[str] = Field(default=None, alias="Notes")

    entity_def: str = Field(default="kahua_Schedule.ScheduleTask", exclude=True)


class MilestoneModel(KahuaBaseModel):
    """
    Milestone entity model.
    Entity Definition: kahua_Schedule.Milestone
    """

    # Identification
    number: Optional[str] = Field(default=None, alias="Number")
    name: Optional[str] = Field(default=None, alias="Name")
    description: Optional[str] = Field(default=None, alias="Description")
    
    # Status
    status: Optional[CostItemStatus] = Field(default=None, alias="Status")
    milestone_status: Optional[str] = Field(default=None, alias="MilestoneStatus")
    is_complete: Optional[bool] = Field(default=None, alias="IsComplete")
    
    # Classification
    milestone_type: Optional[str] = Field(default=None, alias="MilestoneType")
    phase: Optional[str] = Field(default=None, alias="Phase")
    is_key_milestone: Optional[bool] = Field(default=None, alias="IsKeyMilestone")
    is_contractual: Optional[bool] = Field(default=None, alias="IsContractual")
    
    # Dates
    planned_date: Optional[date] = Field(default=None, alias="PlannedDate")
    forecast_date: Optional[date] = Field(default=None, alias="ForecastDate")
    actual_date: Optional[date] = Field(default=None, alias="ActualDate")
    baseline_date: Optional[date] = Field(default=None, alias="BaselineDate")
    
    # Variance
    variance_days: Optional[int] = Field(default=None, alias="VarianceDays")
    
    # Responsibility
    responsible_party: Optional[ContactFull] = Field(default=None, alias="ResponsibleParty")
    responsible_company: Optional[CompanyFull] = Field(default=None, alias="ResponsibleCompany")
    
    # Related task
    related_task: Optional[OutwardReference] = Field(default=None, alias="RelatedTask")
    
    # Deliverables
    deliverables: Optional[str] = Field(default=None, alias="Deliverables")
    
    # Attachments
    attachments: Optional[List[KahuaFile]] = Field(default=None, alias="Attachments")
    
    notes: Optional[str] = Field(default=None, alias="Notes")

    entity_def: str = Field(default="kahua_Schedule.Milestone", exclude=True)


class ScheduleModel(KahuaBaseModel):
    """
    Schedule entity model (container).
    Entity Definition: kahua_Schedule.Schedule
    """

    # Identification
    name: Optional[str] = Field(default=None, alias="Name")
    number: Optional[str] = Field(default=None, alias="Number")
    description: Optional[str] = Field(default=None, alias="Description")
    
    # Status
    status: Optional[str] = Field(default=None, alias="Status")
    schedule_type: Optional[str] = Field(default=None, alias="ScheduleType")
    
    # Dates
    start_date: Optional[date] = Field(default=None, alias="StartDate")
    finish_date: Optional[date] = Field(default=None, alias="FinishDate")
    status_date: Optional[date] = Field(default=None, alias="StatusDate")
    data_date: Optional[date] = Field(default=None, alias="DataDate")
    
    # Progress
    overall_percent_complete: Optional[float] = Field(default=None, alias="OverallPercentComplete")
    
    # Tasks
    tasks: Optional[List[ScheduleTaskModel]] = Field(default=None, alias="Tasks")
    milestones: Optional[List[MilestoneModel]] = Field(default=None, alias="Milestones")
    task_count: Optional[int] = Field(default=None, alias="TaskCount")
    milestone_count: Optional[int] = Field(default=None, alias="MilestoneCount")
    
    # Baselines
    baselines: Optional[List[ScheduleBaselineModel]] = Field(default=None, alias="Baselines")
    active_baseline: Optional[int] = Field(default=None, alias="ActiveBaseline")
    
    # Calendar
    calendar: Optional[str] = Field(default=None, alias="Calendar")
    
    # Source
    source_file: Optional[KahuaFile] = Field(default=None, alias="SourceFile")
    source_system: Optional[str] = Field(default=None, alias="SourceSystem")  # P6, MSP, etc.
    last_import: Optional[datetime] = Field(default=None, alias="LastImport")
    
    # Owner
    schedule_manager: Optional[ContactFull] = Field(default=None, alias="ScheduleManager")
    
    notes: Optional[str] = Field(default=None, alias="Notes")

    entity_def: str = Field(default="kahua_Schedule.Schedule", exclude=True)


def _rebuild_models() -> None:
    """Rebuild models to resolve forward references."""
    models = [
        ScheduleBaselineModel,
        ResourceAssignmentModel,
        ScheduleTaskModel,
        MilestoneModel,
        ScheduleModel,
    ]
    for model in models:
        if hasattr(model, "model_rebuild"):
            model.model_rebuild()


_rebuild_models()
