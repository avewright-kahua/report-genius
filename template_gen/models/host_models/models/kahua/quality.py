"""
Quality control entity models for Kahua Portable View templates.
Entities: kahua_Quality.NCR, QualityInspection, QualityChecklist
"""

from __future__ import annotations

from datetime import date, datetime
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


class NonConformanceReportModel(KahuaBaseModel):
    """
    Non-conformance report (NCR) entity model.
    Entity Definition: kahua_Quality.NCR
    """

    # Identification
    number: Optional[str] = Field(default=None, alias="Number")
    ncr_number: Optional[str] = Field(default=None, alias="NCRNumber")
    subject: Optional[str] = Field(default=None, alias="Subject")
    title: Optional[str] = Field(default=None, alias="Title")
    description: Optional[str] = Field(default=None, alias="Description")
    
    # Status
    status: Optional[CostItemStatus] = Field(default=None, alias="Status")
    ncr_status: Optional[str] = Field(default=None, alias="NCRStatus")
    
    # Classification
    ncr_type: Optional[str] = Field(default=None, alias="NCRType")
    category: Optional[str] = Field(default=None, alias="Category")
    severity: Optional[str] = Field(default=None, alias="Severity")
    priority: Optional[str] = Field(default=None, alias="Priority")
    discipline: Optional[str] = Field(default=None, alias="Discipline")
    csi_code: Optional[CSICode] = Field(default=None, alias="CSICode")
    
    # Location
    location: Optional[Location] = Field(default=None, alias="Location")
    location_description: Optional[str] = Field(default=None, alias="LocationDescription")
    
    # Non-conformance details
    non_conformance: Optional[str] = Field(default=None, alias="NonConformance")
    requirement: Optional[str] = Field(default=None, alias="Requirement")  # What was required
    deficiency: Optional[str] = Field(default=None, alias="Deficiency")  # What was found
    
    # Reference
    spec_reference: Optional[str] = Field(default=None, alias="SpecReference")
    drawing_reference: Optional[str] = Field(default=None, alias="DrawingReference")
    code_reference: Optional[str] = Field(default=None, alias="CodeReference")
    
    # Dates
    date_identified: Optional[date] = Field(default=None, alias="DateIdentified")
    date_created: Optional[date] = Field(default=None, alias="DateCreated")
    date_due: Optional[date] = Field(default=None, alias="DateDue")
    date_closed: Optional[date] = Field(default=None, alias="DateClosed")
    
    # People
    identified_by: Optional[ContactFull] = Field(default=None, alias="IdentifiedBy")
    created_by: Optional[ContactFull] = Field(default=None, alias="CreatedBy")
    assigned_to: Optional[ContactFull] = Field(default=None, alias="AssignedTo")
    responsible_party: Optional[ContactFull] = Field(default=None, alias="ResponsibleParty")
    verified_by: Optional[ContactFull] = Field(default=None, alias="VerifiedBy")
    closed_by: Optional[ContactFull] = Field(default=None, alias="ClosedBy")
    
    # Company
    responsible_company: Optional[CompanyFull] = Field(default=None, alias="ResponsibleCompany")
    contractor: Optional[CompanyFull] = Field(default=None, alias="Contractor")
    
    # Disposition
    disposition: Optional[str] = Field(default=None, alias="Disposition")  # Rework, Accept As-Is, Reject, etc.
    disposition_reason: Optional[str] = Field(default=None, alias="DispositionReason")
    disposition_by: Optional[ContactFull] = Field(default=None, alias="DispositionBy")
    disposition_date: Optional[date] = Field(default=None, alias="DispositionDate")
    
    # Corrective action
    corrective_action: Optional[str] = Field(default=None, alias="CorrectiveAction")
    root_cause: Optional[str] = Field(default=None, alias="RootCause")
    preventive_action: Optional[str] = Field(default=None, alias="PreventiveAction")
    
    # Verification
    verification_method: Optional[str] = Field(default=None, alias="VerificationMethod")
    verification_date: Optional[date] = Field(default=None, alias="VerificationDate")
    verification_notes: Optional[str] = Field(default=None, alias="VerificationNotes")
    
    # Cost impact
    has_cost_impact: Optional[bool] = Field(default=None, alias="HasCostImpact")
    cost_impact: Optional[float] = Field(default=None, alias="CostImpact")
    back_charge: Optional[bool] = Field(default=None, alias="BackCharge")
    back_charge_amount: Optional[float] = Field(default=None, alias="BackChargeAmount")
    
    # Schedule impact
    has_schedule_impact: Optional[bool] = Field(default=None, alias="HasScheduleImpact")
    schedule_impact_days: Optional[int] = Field(default=None, alias="ScheduleImpactDays")
    
    # Related items
    related_inspections: Optional[List[OutwardReference]] = Field(default=None, alias="RelatedInspections")
    related_ncrs: Optional[List[OutwardReference]] = Field(default=None, alias="RelatedNCRs")
    
    # Distribution
    distribution: Optional[List[DistributionEntry]] = Field(default=None, alias="Distribution")
    notification_list: Optional[List[NotificationEntry]] = Field(default=None, alias="NotificationList")
    
    # Photos and attachments
    photos: Optional[List[KahuaFile]] = Field(default=None, alias="Photos")
    attachments: Optional[List[KahuaFile]] = Field(default=None, alias="Attachments")
    
    # Comments
    comments: Optional[List[Comment]] = Field(default=None, alias="Comments")
    secondary_comments: Optional[List[SecondaryComment]] = Field(default=None, alias="SecondaryComments")
    
    # Workflow
    workflow_info: Optional[WorkflowInfo] = Field(default=None, alias="WorkflowInfo")
    approval_info: Optional[ApprovalInfo] = Field(default=None, alias="ApprovalInfo")
    
    # Notes
    notes: Optional[str] = Field(default=None, alias="Notes")
    internal_notes: Optional[str] = Field(default=None, alias="InternalNotes")

    entity_def: str = Field(default="kahua_Quality.NCR", exclude=True)


class QualityChecklistItemModel(KahuaBaseModel):
    """Quality checklist item."""

    item_number: Optional[str] = Field(default=None, alias="ItemNumber")
    description: Optional[str] = Field(default=None, alias="Description")
    category: Optional[str] = Field(default=None, alias="Category")
    
    # Result
    result: Optional[str] = Field(default=None, alias="Result")  # Pass, Fail, N/A
    is_pass: Optional[bool] = Field(default=None, alias="IsPass")
    is_fail: Optional[bool] = Field(default=None, alias="IsFail")
    is_na: Optional[bool] = Field(default=None, alias="IsNA")
    
    # Inspection details
    inspected_date: Optional[date] = Field(default=None, alias="InspectedDate")
    inspected_by: Optional[ContactFull] = Field(default=None, alias="InspectedBy")
    
    # Reference
    spec_reference: Optional[str] = Field(default=None, alias="SpecReference")
    acceptance_criteria: Optional[str] = Field(default=None, alias="AcceptanceCriteria")
    
    # Comments
    comments: Optional[str] = Field(default=None, alias="Comments")
    
    # Photos
    photos: Optional[List[KahuaFile]] = Field(default=None, alias="Photos")


class QualityInspectionModel(KahuaBaseModel):
    """
    Quality inspection entity model.
    Entity Definition: kahua_Quality.QualityInspection
    """

    # Identification
    number: Optional[str] = Field(default=None, alias="Number")
    inspection_number: Optional[str] = Field(default=None, alias="InspectionNumber")
    title: Optional[str] = Field(default=None, alias="Title")
    description: Optional[str] = Field(default=None, alias="Description")
    
    # Status
    status: Optional[CostItemStatus] = Field(default=None, alias="Status")
    inspection_status: Optional[str] = Field(default=None, alias="InspectionStatus")
    inspection_result: Optional[str] = Field(default=None, alias="InspectionResult")
    
    # Classification
    inspection_type: Optional[str] = Field(default=None, alias="InspectionType")
    category: Optional[str] = Field(default=None, alias="Category")
    discipline: Optional[str] = Field(default=None, alias="Discipline")
    csi_code: Optional[CSICode] = Field(default=None, alias="CSICode")
    
    # Location
    location: Optional[Location] = Field(default=None, alias="Location")
    location_description: Optional[str] = Field(default=None, alias="LocationDescription")
    
    # Dates
    scheduled_date: Optional[date] = Field(default=None, alias="ScheduledDate")
    inspection_date: Optional[date] = Field(default=None, alias="InspectionDate")
    
    # People
    inspector: Optional[ContactFull] = Field(default=None, alias="Inspector")
    requested_by: Optional[ContactFull] = Field(default=None, alias="RequestedBy")
    
    # Company
    contractor: Optional[CompanyFull] = Field(default=None, alias="Contractor")
    
    # Checklist
    checklist_items: Optional[List[QualityChecklistItemModel]] = Field(default=None, alias="ChecklistItems")
    total_items: Optional[int] = Field(default=None, alias="TotalItems")
    passed_items: Optional[int] = Field(default=None, alias="PassedItems")
    failed_items: Optional[int] = Field(default=None, alias="FailedItems")
    
    # Summary
    summary: Optional[str] = Field(default=None, alias="Summary")
    findings: Optional[str] = Field(default=None, alias="Findings")
    recommendations: Optional[str] = Field(default=None, alias="Recommendations")
    
    # Photos and attachments
    photos: Optional[List[KahuaFile]] = Field(default=None, alias="Photos")
    attachments: Optional[List[KahuaFile]] = Field(default=None, alias="Attachments")
    
    # Comments
    comments: Optional[List[Comment]] = Field(default=None, alias="Comments")
    
    # Workflow
    workflow_info: Optional[WorkflowInfo] = Field(default=None, alias="WorkflowInfo")
    
    notes: Optional[str] = Field(default=None, alias="Notes")

    entity_def: str = Field(default="kahua_Quality.QualityInspection", exclude=True)


class TestReportModel(KahuaBaseModel):
    """
    Test report entity model.
    Entity Definition: kahua_Quality.TestReport
    """

    # Identification
    number: Optional[str] = Field(default=None, alias="Number")
    report_number: Optional[str] = Field(default=None, alias="ReportNumber")
    title: Optional[str] = Field(default=None, alias="Title")
    description: Optional[str] = Field(default=None, alias="Description")
    
    # Status
    status: Optional[CostItemStatus] = Field(default=None, alias="Status")
    test_result: Optional[str] = Field(default=None, alias="TestResult")  # Pass, Fail, Inconclusive
    
    # Classification
    test_type: Optional[str] = Field(default=None, alias="TestType")
    test_method: Optional[str] = Field(default=None, alias="TestMethod")
    discipline: Optional[str] = Field(default=None, alias="Discipline")
    csi_code: Optional[CSICode] = Field(default=None, alias="CSICode")
    
    # Location/Material
    location: Optional[Location] = Field(default=None, alias="Location")
    material_tested: Optional[str] = Field(default=None, alias="MaterialTested")
    sample_id: Optional[str] = Field(default=None, alias="SampleId")
    
    # Dates
    sample_date: Optional[date] = Field(default=None, alias="SampleDate")
    test_date: Optional[date] = Field(default=None, alias="TestDate")
    report_date: Optional[date] = Field(default=None, alias="ReportDate")
    
    # Testing party
    testing_lab: Optional[CompanyFull] = Field(default=None, alias="TestingLab")
    tested_by: Optional[ContactFull] = Field(default=None, alias="TestedBy")
    
    # Results
    test_results: Optional[str] = Field(default=None, alias="TestResults")
    specification: Optional[str] = Field(default=None, alias="Specification")
    acceptance_criteria: Optional[str] = Field(default=None, alias="AcceptanceCriteria")
    measured_values: Optional[str] = Field(default=None, alias="MeasuredValues")
    
    # Pass/Fail
    is_pass: Optional[bool] = Field(default=None, alias="IsPass")
    is_fail: Optional[bool] = Field(default=None, alias="IsFail")
    
    # Related NCR
    related_ncr: Optional[OutwardReference] = Field(default=None, alias="RelatedNCR")
    
    # Attachments
    attachments: Optional[List[KahuaFile]] = Field(default=None, alias="Attachments")
    
    # Comments
    comments: Optional[List[Comment]] = Field(default=None, alias="Comments")
    
    notes: Optional[str] = Field(default=None, alias="Notes")

    entity_def: str = Field(default="kahua_Quality.TestReport", exclude=True)


def _rebuild_models() -> None:
    """Rebuild models to resolve forward references."""
    models = [
        NonConformanceReportModel,
        QualityChecklistItemModel,
        QualityInspectionModel,
        TestReportModel,
    ]
    for model in models:
        if hasattr(model, "model_rebuild"):
            model.model_rebuild()


_rebuild_models()
