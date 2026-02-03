"""
Safety entity models for Kahua Portable View templates.
Entities: kahua_Safety.SafetyIncident, SafetyObservation, SafetyInspection
"""

from __future__ import annotations

from datetime import date, datetime, time
from typing import List, Optional

from pydantic import Field

from .common import (
    ApprovalInfo,
    Comment,
    CompanyFull,
    ContactFull,
    CostItemStatus,
    DistributionEntry,
    KahuaBaseModel,
    KahuaFile,
    Location,
    NotificationEntry,
    OutwardReference,
    SecondaryComment,
    WorkflowInfo,
)


class InjuryModel(KahuaBaseModel):
    """Injury details for safety incidents."""

    injured_person: Optional[ContactFull] = Field(default=None, alias="InjuredPerson")
    person_name: Optional[str] = Field(default=None, alias="PersonName")
    company: Optional[CompanyFull] = Field(default=None, alias="Company")
    job_title: Optional[str] = Field(default=None, alias="JobTitle")
    
    injury_type: Optional[str] = Field(default=None, alias="InjuryType")
    body_part: Optional[str] = Field(default=None, alias="BodyPart")
    injury_description: Optional[str] = Field(default=None, alias="InjuryDescription")
    
    treatment_type: Optional[str] = Field(default=None, alias="TreatmentType")  # First Aid, Medical, Hospital
    medical_attention: Optional[bool] = Field(default=None, alias="MedicalAttention")
    hospitalized: Optional[bool] = Field(default=None, alias="Hospitalized")
    
    days_away: Optional[int] = Field(default=None, alias="DaysAway")
    restricted_days: Optional[int] = Field(default=None, alias="RestrictedDays")
    return_to_work_date: Optional[date] = Field(default=None, alias="ReturnToWorkDate")


class WitnessModel(KahuaBaseModel):
    """Witness information for safety incidents."""

    witness: Optional[ContactFull] = Field(default=None, alias="Witness")
    name: Optional[str] = Field(default=None, alias="Name")
    company: Optional[CompanyFull] = Field(default=None, alias="Company")
    phone: Optional[str] = Field(default=None, alias="Phone")
    email: Optional[str] = Field(default=None, alias="Email")
    statement: Optional[str] = Field(default=None, alias="Statement")


class SafetyIncidentModel(KahuaBaseModel):
    """
    Safety incident entity model.
    Entity Definition: kahua_Safety.SafetyIncident
    """

    # Identification
    number: Optional[str] = Field(default=None, alias="Number")
    incident_number: Optional[str] = Field(default=None, alias="IncidentNumber")
    subject: Optional[str] = Field(default=None, alias="Subject")
    title: Optional[str] = Field(default=None, alias="Title")
    description: Optional[str] = Field(default=None, alias="Description")
    
    # Status
    status: Optional[CostItemStatus] = Field(default=None, alias="Status")
    incident_status: Optional[str] = Field(default=None, alias="IncidentStatus")
    
    # Classification
    incident_type: Optional[str] = Field(default=None, alias="IncidentType")
    incident_category: Optional[str] = Field(default=None, alias="IncidentCategory")
    severity: Optional[str] = Field(default=None, alias="Severity")
    
    # Recordability
    is_recordable: Optional[bool] = Field(default=None, alias="IsRecordable")
    osha_recordable: Optional[bool] = Field(default=None, alias="OSHARecordable")
    osha_case_number: Optional[str] = Field(default=None, alias="OSHACaseNumber")
    is_lost_time: Optional[bool] = Field(default=None, alias="IsLostTime")
    is_near_miss: Optional[bool] = Field(default=None, alias="IsNearMiss")
    is_first_aid: Optional[bool] = Field(default=None, alias="IsFirstAid")
    is_fatality: Optional[bool] = Field(default=None, alias="IsFatality")
    
    # Location
    location: Optional[Location] = Field(default=None, alias="Location")
    location_description: Optional[str] = Field(default=None, alias="LocationDescription")
    building: Optional[str] = Field(default=None, alias="Building")
    floor: Optional[str] = Field(default=None, alias="Floor")
    area: Optional[str] = Field(default=None, alias="Area")
    
    # Date and time
    incident_date: Optional[date] = Field(default=None, alias="IncidentDate")
    incident_time: Optional[time] = Field(default=None, alias="IncidentTime")
    date_reported: Optional[date] = Field(default=None, alias="DateReported")
    
    # People involved
    reported_by: Optional[ContactFull] = Field(default=None, alias="ReportedBy")
    supervisor: Optional[ContactFull] = Field(default=None, alias="Supervisor")
    safety_manager: Optional[ContactFull] = Field(default=None, alias="SafetyManager")
    investigated_by: Optional[ContactFull] = Field(default=None, alias="InvestigatedBy")
    
    # Company
    company_involved: Optional[CompanyFull] = Field(default=None, alias="CompanyInvolved")
    contractor: Optional[CompanyFull] = Field(default=None, alias="Contractor")
    
    # Injuries
    injuries: Optional[List[InjuryModel]] = Field(default=None, alias="Injuries")
    injury_count: Optional[int] = Field(default=None, alias="InjuryCount")
    total_days_away: Optional[int] = Field(default=None, alias="TotalDaysAway")
    total_restricted_days: Optional[int] = Field(default=None, alias="TotalRestrictedDays")
    
    # Property/Equipment damage
    property_damage: Optional[bool] = Field(default=None, alias="PropertyDamage")
    property_damage_description: Optional[str] = Field(default=None, alias="PropertyDamageDescription")
    property_damage_cost: Optional[float] = Field(default=None, alias="PropertyDamageCost")
    equipment_involved: Optional[str] = Field(default=None, alias="EquipmentInvolved")
    
    # Witnesses
    witnesses: Optional[List[WitnessModel]] = Field(default=None, alias="Witnesses")
    
    # Investigation
    investigation_date: Optional[date] = Field(default=None, alias="InvestigationDate")
    root_cause: Optional[str] = Field(default=None, alias="RootCause")
    contributing_factors: Optional[str] = Field(default=None, alias="ContributingFactors")
    immediate_cause: Optional[str] = Field(default=None, alias="ImmediateCause")
    
    # Corrective actions
    corrective_actions: Optional[str] = Field(default=None, alias="CorrectiveActions")
    preventive_actions: Optional[str] = Field(default=None, alias="PreventiveActions")
    corrective_action_due: Optional[date] = Field(default=None, alias="CorrectiveActionDue")
    corrective_action_completed: Optional[date] = Field(default=None, alias="CorrectiveActionCompleted")
    
    # Weather/conditions
    weather_conditions: Optional[str] = Field(default=None, alias="WeatherConditions")
    environmental_conditions: Optional[str] = Field(default=None, alias="EnvironmentalConditions")
    
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

    entity_def: str = Field(default="kahua_Safety.SafetyIncident", exclude=True)


class SafetyObservationModel(KahuaBaseModel):
    """
    Safety observation entity model.
    Entity Definition: kahua_Safety.SafetyObservation
    """

    # Identification
    number: Optional[str] = Field(default=None, alias="Number")
    observation_number: Optional[str] = Field(default=None, alias="ObservationNumber")
    subject: Optional[str] = Field(default=None, alias="Subject")
    description: Optional[str] = Field(default=None, alias="Description")
    
    # Status
    status: Optional[CostItemStatus] = Field(default=None, alias="Status")
    observation_status: Optional[str] = Field(default=None, alias="ObservationStatus")
    
    # Classification
    observation_type: Optional[str] = Field(default=None, alias="ObservationType")  # Safe, At-Risk, Hazard
    category: Optional[str] = Field(default=None, alias="Category")
    hazard_type: Optional[str] = Field(default=None, alias="HazardType")
    severity: Optional[str] = Field(default=None, alias="Severity")
    priority: Optional[str] = Field(default=None, alias="Priority")
    
    # Location
    location: Optional[Location] = Field(default=None, alias="Location")
    location_description: Optional[str] = Field(default=None, alias="LocationDescription")
    
    # Date and time
    observation_date: Optional[date] = Field(default=None, alias="ObservationDate")
    observation_time: Optional[time] = Field(default=None, alias="ObservationTime")
    
    # People
    observed_by: Optional[ContactFull] = Field(default=None, alias="ObservedBy")
    assigned_to: Optional[ContactFull] = Field(default=None, alias="AssignedTo")
    responsible_party: Optional[ContactFull] = Field(default=None, alias="ResponsibleParty")
    
    # Company
    company_responsible: Optional[CompanyFull] = Field(default=None, alias="CompanyResponsible")
    
    # Resolution
    date_due: Optional[date] = Field(default=None, alias="DateDue")
    date_corrected: Optional[date] = Field(default=None, alias="DateCorrected")
    corrective_action: Optional[str] = Field(default=None, alias="CorrectiveAction")
    resolution: Optional[str] = Field(default=None, alias="Resolution")
    
    # Safe behavior recognition
    is_positive_observation: Optional[bool] = Field(default=None, alias="IsPositiveObservation")
    recognition_given: Optional[bool] = Field(default=None, alias="RecognitionGiven")
    
    # Photos and attachments
    photos: Optional[List[KahuaFile]] = Field(default=None, alias="Photos")
    attachments: Optional[List[KahuaFile]] = Field(default=None, alias="Attachments")
    
    # Comments
    comments: Optional[List[Comment]] = Field(default=None, alias="Comments")
    
    notes: Optional[str] = Field(default=None, alias="Notes")

    entity_def: str = Field(default="kahua_Safety.SafetyObservation", exclude=True)


class SafetyInspectionModel(KahuaBaseModel):
    """
    Safety inspection entity model.
    Entity Definition: kahua_Safety.SafetyInspection
    """

    # Identification
    number: Optional[str] = Field(default=None, alias="Number")
    inspection_number: Optional[str] = Field(default=None, alias="InspectionNumber")
    title: Optional[str] = Field(default=None, alias="Title")
    description: Optional[str] = Field(default=None, alias="Description")
    
    # Status
    status: Optional[CostItemStatus] = Field(default=None, alias="Status")
    inspection_status: Optional[str] = Field(default=None, alias="InspectionStatus")
    
    # Classification
    inspection_type: Optional[str] = Field(default=None, alias="InspectionType")
    inspection_category: Optional[str] = Field(default=None, alias="InspectionCategory")
    
    # Location
    location: Optional[Location] = Field(default=None, alias="Location")
    location_description: Optional[str] = Field(default=None, alias="LocationDescription")
    
    # Dates
    scheduled_date: Optional[date] = Field(default=None, alias="ScheduledDate")
    inspection_date: Optional[date] = Field(default=None, alias="InspectionDate")
    
    # People
    inspector: Optional[ContactFull] = Field(default=None, alias="Inspector")
    inspected_by: Optional[ContactFull] = Field(default=None, alias="InspectedBy")
    
    # Company inspected
    company_inspected: Optional[CompanyFull] = Field(default=None, alias="CompanyInspected")
    
    # Results
    inspection_result: Optional[str] = Field(default=None, alias="InspectionResult")
    score: Optional[float] = Field(default=None, alias="Score")
    total_items: Optional[int] = Field(default=None, alias="TotalItems")
    compliant_items: Optional[int] = Field(default=None, alias="CompliantItems")
    non_compliant_items: Optional[int] = Field(default=None, alias="NonCompliantItems")
    
    # Observations
    observations: Optional[List[SafetyObservationModel]] = Field(default=None, alias="Observations")
    findings: Optional[str] = Field(default=None, alias="Findings")
    
    # Summary
    summary: Optional[str] = Field(default=None, alias="Summary")
    recommendations: Optional[str] = Field(default=None, alias="Recommendations")
    
    # Photos and attachments
    photos: Optional[List[KahuaFile]] = Field(default=None, alias="Photos")
    attachments: Optional[List[KahuaFile]] = Field(default=None, alias="Attachments")
    
    # Comments
    comments: Optional[List[Comment]] = Field(default=None, alias="Comments")
    
    # Workflow
    workflow_info: Optional[WorkflowInfo] = Field(default=None, alias="WorkflowInfo")
    
    notes: Optional[str] = Field(default=None, alias="Notes")

    entity_def: str = Field(default="kahua_Safety.SafetyInspection", exclude=True)


class PermitToWorkModel(KahuaBaseModel):
    """
    Permit to work entity model.
    Entity Definition: kahua_Safety.PermitToWork
    """

    # Identification
    number: Optional[str] = Field(default=None, alias="Number")
    permit_number: Optional[str] = Field(default=None, alias="PermitNumber")
    title: Optional[str] = Field(default=None, alias="Title")
    description: Optional[str] = Field(default=None, alias="Description")
    
    # Status
    status: Optional[CostItemStatus] = Field(default=None, alias="Status")
    permit_status: Optional[str] = Field(default=None, alias="PermitStatus")  # Requested, Active, Closed, Expired
    
    # Classification
    permit_type: Optional[str] = Field(default=None, alias="PermitType")  # Hot Work, Confined Space, Excavation, etc.
    
    # Location
    location: Optional[Location] = Field(default=None, alias="Location")
    work_area: Optional[str] = Field(default=None, alias="WorkArea")
    
    # Dates
    requested_date: Optional[date] = Field(default=None, alias="RequestedDate")
    start_date: Optional[date] = Field(default=None, alias="StartDate")
    end_date: Optional[date] = Field(default=None, alias="EndDate")
    start_time: Optional[time] = Field(default=None, alias="StartTime")
    end_time: Optional[time] = Field(default=None, alias="EndTime")
    
    # People
    requested_by: Optional[ContactFull] = Field(default=None, alias="RequestedBy")
    issued_by: Optional[ContactFull] = Field(default=None, alias="IssuedBy")
    supervisor: Optional[ContactFull] = Field(default=None, alias="Supervisor")
    
    # Company
    contractor: Optional[CompanyFull] = Field(default=None, alias="Contractor")
    
    # Work details
    work_description: Optional[str] = Field(default=None, alias="WorkDescription")
    hazards_identified: Optional[str] = Field(default=None, alias="HazardsIdentified")
    precautions: Optional[str] = Field(default=None, alias="Precautions")
    ppe_required: Optional[str] = Field(default=None, alias="PPERequired")
    emergency_procedures: Optional[str] = Field(default=None, alias="EmergencyProcedures")
    
    # Approvals
    approved_by: Optional[ContactFull] = Field(default=None, alias="ApprovedBy")
    approved_date: Optional[date] = Field(default=None, alias="ApprovedDate")
    
    # Attachments
    attachments: Optional[List[KahuaFile]] = Field(default=None, alias="Attachments")
    
    notes: Optional[str] = Field(default=None, alias="Notes")

    entity_def: str = Field(default="kahua_Safety.PermitToWork", exclude=True)


def _rebuild_models() -> None:
    """Rebuild models to resolve forward references."""
    models = [
        InjuryModel,
        WitnessModel,
        SafetyIncidentModel,
        SafetyObservationModel,
        SafetyInspectionModel,
        PermitToWorkModel,
    ]
    for model in models:
        if hasattr(model, "model_rebuild"):
            model.model_rebuild()


_rebuild_models()
