"""
Daily report entity models for Kahua Portable View templates.
Entities: kahua_DailyReport.DailyReport, kahua_AEC_DailyReports.DailyLog
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


class WeatherConditionModel(KahuaBaseModel):
    """Weather condition entry for daily reports."""

    time_of_day: Optional[str] = Field(default=None, alias="TimeOfDay")  # Morning, Afternoon, Evening
    temperature: Optional[float] = Field(default=None, alias="Temperature")
    temperature_unit: Optional[str] = Field(default=None, alias="TemperatureUnit")  # F or C
    temperature_high: Optional[float] = Field(default=None, alias="TemperatureHigh")
    temperature_low: Optional[float] = Field(default=None, alias="TemperatureLow")
    conditions: Optional[str] = Field(default=None, alias="Conditions")  # Sunny, Cloudy, Rain, etc.
    precipitation: Optional[str] = Field(default=None, alias="Precipitation")
    precipitation_amount: Optional[float] = Field(default=None, alias="PrecipitationAmount")
    humidity: Optional[float] = Field(default=None, alias="Humidity")
    wind_speed: Optional[float] = Field(default=None, alias="WindSpeed")
    wind_direction: Optional[str] = Field(default=None, alias="WindDirection")
    ground_conditions: Optional[str] = Field(default=None, alias="GroundConditions")
    weather_delay: Optional[bool] = Field(default=None, alias="WeatherDelay")
    notes: Optional[str] = Field(default=None, alias="Notes")


class ManpowerEntryModel(KahuaBaseModel):
    """Manpower/workforce entry for daily reports."""

    company: Optional[CompanyFull] = Field(default=None, alias="Company")
    company_name: Optional[str] = Field(default=None, alias="CompanyName")
    trade: Optional[str] = Field(default=None, alias="Trade")
    craft: Optional[str] = Field(default=None, alias="Craft")
    
    # Headcount
    workers: Optional[int] = Field(default=None, alias="Workers")
    foremen: Optional[int] = Field(default=None, alias="Foremen")
    superintendents: Optional[int] = Field(default=None, alias="Superintendents")
    apprentices: Optional[int] = Field(default=None, alias="Apprentices")
    total_workers: Optional[int] = Field(default=None, alias="TotalWorkers")
    
    # Hours
    regular_hours: Optional[float] = Field(default=None, alias="RegularHours")
    overtime_hours: Optional[float] = Field(default=None, alias="OvertimeHours")
    double_time_hours: Optional[float] = Field(default=None, alias="DoubleTimeHours")
    total_hours: Optional[float] = Field(default=None, alias="TotalHours")
    
    # Work description
    work_performed: Optional[str] = Field(default=None, alias="WorkPerformed")
    work_area: Optional[str] = Field(default=None, alias="WorkArea")
    location: Optional[Location] = Field(default=None, alias="Location")
    
    notes: Optional[str] = Field(default=None, alias="Notes")


class EquipmentEntryModel(KahuaBaseModel):
    """Equipment entry for daily reports."""

    equipment_type: Optional[str] = Field(default=None, alias="EquipmentType")
    equipment_name: Optional[str] = Field(default=None, alias="EquipmentName")
    equipment_id: Optional[str] = Field(default=None, alias="EquipmentId")
    company: Optional[CompanyFull] = Field(default=None, alias="Company")
    
    quantity: Optional[int] = Field(default=None, alias="Quantity")
    hours_used: Optional[float] = Field(default=None, alias="HoursUsed")
    hours_idle: Optional[float] = Field(default=None, alias="HoursIdle")
    
    status: Optional[str] = Field(default=None, alias="Status")  # Active, Idle, Down
    work_performed: Optional[str] = Field(default=None, alias="WorkPerformed")
    location: Optional[Location] = Field(default=None, alias="Location")
    
    notes: Optional[str] = Field(default=None, alias="Notes")


class MaterialDeliveryModel(KahuaBaseModel):
    """Material delivery entry for daily reports."""

    material: Optional[str] = Field(default=None, alias="Material")
    material_description: Optional[str] = Field(default=None, alias="MaterialDescription")
    quantity: Optional[float] = Field(default=None, alias="Quantity")
    unit: Optional[str] = Field(default=None, alias="Unit")
    
    vendor: Optional[CompanyFull] = Field(default=None, alias="Vendor")
    vendor_name: Optional[str] = Field(default=None, alias="VendorName")
    
    delivery_date: Optional[date] = Field(default=None, alias="DeliveryDate")
    delivery_time: Optional[time] = Field(default=None, alias="DeliveryTime")
    received_by: Optional[ContactFull] = Field(default=None, alias="ReceivedBy")
    
    delivery_ticket: Optional[str] = Field(default=None, alias="DeliveryTicket")
    po_number: Optional[str] = Field(default=None, alias="PONumber")
    
    condition: Optional[str] = Field(default=None, alias="Condition")
    storage_location: Optional[str] = Field(default=None, alias="StorageLocation")
    
    notes: Optional[str] = Field(default=None, alias="Notes")


class VisitorEntryModel(KahuaBaseModel):
    """Visitor entry for daily reports."""

    visitor: Optional[ContactFull] = Field(default=None, alias="Visitor")
    visitor_name: Optional[str] = Field(default=None, alias="VisitorName")
    company: Optional[CompanyFull] = Field(default=None, alias="Company")
    company_name: Optional[str] = Field(default=None, alias="CompanyName")
    
    purpose: Optional[str] = Field(default=None, alias="Purpose")
    time_in: Optional[time] = Field(default=None, alias="TimeIn")
    time_out: Optional[time] = Field(default=None, alias="TimeOut")
    
    badge_number: Optional[str] = Field(default=None, alias="BadgeNumber")
    escorted_by: Optional[ContactFull] = Field(default=None, alias="EscortedBy")
    
    notes: Optional[str] = Field(default=None, alias="Notes")


class SafetyIncidentModel(KahuaBaseModel):
    """Safety incident entry for daily reports."""

    incident_type: Optional[str] = Field(default=None, alias="IncidentType")
    description: Optional[str] = Field(default=None, alias="Description")
    severity: Optional[str] = Field(default=None, alias="Severity")
    
    incident_date: Optional[date] = Field(default=None, alias="IncidentDate")
    incident_time: Optional[time] = Field(default=None, alias="IncidentTime")
    location: Optional[Location] = Field(default=None, alias="Location")
    location_description: Optional[str] = Field(default=None, alias="LocationDescription")
    
    person_involved: Optional[ContactFull] = Field(default=None, alias="PersonInvolved")
    company: Optional[CompanyFull] = Field(default=None, alias="Company")
    
    injuries: Optional[str] = Field(default=None, alias="Injuries")
    medical_attention: Optional[bool] = Field(default=None, alias="MedicalAttention")
    lost_time: Optional[bool] = Field(default=None, alias="LostTime")
    osha_recordable: Optional[bool] = Field(default=None, alias="OSHARecordable")
    
    corrective_action: Optional[str] = Field(default=None, alias="CorrectiveAction")
    reported_to: Optional[ContactFull] = Field(default=None, alias="ReportedTo")
    
    attachments: Optional[List[KahuaFile]] = Field(default=None, alias="Attachments")
    notes: Optional[str] = Field(default=None, alias="Notes")


class WorkActivityModel(KahuaBaseModel):
    """Work activity entry for daily reports."""

    activity: Optional[str] = Field(default=None, alias="Activity")
    description: Optional[str] = Field(default=None, alias="Description")
    csi_code: Optional[CSICode] = Field(default=None, alias="CSICode")
    
    company: Optional[CompanyFull] = Field(default=None, alias="Company")
    location: Optional[Location] = Field(default=None, alias="Location")
    location_description: Optional[str] = Field(default=None, alias="LocationDescription")
    
    percent_complete: Optional[float] = Field(default=None, alias="PercentComplete")
    quantity_installed: Optional[float] = Field(default=None, alias="QuantityInstalled")
    unit: Optional[str] = Field(default=None, alias="Unit")
    
    notes: Optional[str] = Field(default=None, alias="Notes")


class DelayModel(KahuaBaseModel):
    """Delay entry for daily reports."""

    delay_type: Optional[str] = Field(default=None, alias="DelayType")
    description: Optional[str] = Field(default=None, alias="Description")
    cause: Optional[str] = Field(default=None, alias="Cause")
    
    company_affected: Optional[CompanyFull] = Field(default=None, alias="CompanyAffected")
    activity_affected: Optional[str] = Field(default=None, alias="ActivityAffected")
    
    start_time: Optional[time] = Field(default=None, alias="StartTime")
    end_time: Optional[time] = Field(default=None, alias="EndTime")
    duration_hours: Optional[float] = Field(default=None, alias="DurationHours")
    
    impact: Optional[str] = Field(default=None, alias="Impact")
    schedule_impact_days: Optional[int] = Field(default=None, alias="ScheduleImpactDays")
    
    notes: Optional[str] = Field(default=None, alias="Notes")


class DailyReportModel(KahuaBaseModel):
    """
    Daily report entity model.
    Entity Definition: kahua_DailyReport.DailyReport or kahua_AEC_DailyReports.DailyLog
    """

    # Identification
    number: Optional[str] = Field(default=None, alias="Number")
    report_number: Optional[str] = Field(default=None, alias="ReportNumber")
    subject: Optional[str] = Field(default=None, alias="Subject")
    description: Optional[str] = Field(default=None, alias="Description")
    
    # Status
    status: Optional[CostItemStatus] = Field(default=None, alias="Status")
    report_type: Optional[str] = Field(default=None, alias="ReportType")
    
    # Dates
    report_date: Optional[date] = Field(default=None, alias="ReportDate")
    date_created: Optional[date] = Field(default=None, alias="DateCreated")
    date_submitted: Optional[date] = Field(default=None, alias="DateSubmitted")
    date_approved: Optional[date] = Field(default=None, alias="DateApproved")
    work_day: Optional[int] = Field(default=None, alias="WorkDay")
    
    # Work schedule
    scheduled_work_hours: Optional[float] = Field(default=None, alias="ScheduledWorkHours")
    actual_work_hours: Optional[float] = Field(default=None, alias="ActualWorkHours")
    shift: Optional[str] = Field(default=None, alias="Shift")
    
    # People
    created_by: Optional[ContactFull] = Field(default=None, alias="CreatedBy")
    prepared_by: Optional[ContactFull] = Field(default=None, alias="PreparedBy")
    superintendent: Optional[ContactFull] = Field(default=None, alias="Superintendent")
    approved_by: Optional[ContactFull] = Field(default=None, alias="ApprovedBy")
    
    # Company
    company: Optional[CompanyFull] = Field(default=None, alias="Company")
    contractor: Optional[CompanyFull] = Field(default=None, alias="Contractor")
    
    # Weather
    weather_conditions: Optional[List[WeatherConditionModel]] = Field(default=None, alias="WeatherConditions")
    weather_am: Optional[WeatherConditionModel] = Field(default=None, alias="WeatherAM")
    weather_pm: Optional[WeatherConditionModel] = Field(default=None, alias="WeatherPM")
    weather_notes: Optional[str] = Field(default=None, alias="WeatherNotes")
    
    # Manpower
    manpower_entries: Optional[List[ManpowerEntryModel]] = Field(default=None, alias="ManpowerEntries")
    total_workers: Optional[int] = Field(default=None, alias="TotalWorkers")
    total_man_hours: Optional[float] = Field(default=None, alias="TotalManHours")
    
    # Equipment
    equipment_entries: Optional[List[EquipmentEntryModel]] = Field(default=None, alias="EquipmentEntries")
    
    # Materials
    material_deliveries: Optional[List[MaterialDeliveryModel]] = Field(default=None, alias="MaterialDeliveries")
    
    # Visitors
    visitors: Optional[List[VisitorEntryModel]] = Field(default=None, alias="Visitors")
    
    # Safety
    safety_incidents: Optional[List[SafetyIncidentModel]] = Field(default=None, alias="SafetyIncidents")
    safety_meeting_held: Optional[bool] = Field(default=None, alias="SafetyMeetingHeld")
    safety_meeting_topic: Optional[str] = Field(default=None, alias="SafetyMeetingTopic")
    safety_notes: Optional[str] = Field(default=None, alias="SafetyNotes")
    
    # Work performed
    work_activities: Optional[List[WorkActivityModel]] = Field(default=None, alias="WorkActivities")
    work_performed: Optional[str] = Field(default=None, alias="WorkPerformed")
    work_planned_tomorrow: Optional[str] = Field(default=None, alias="WorkPlannedTomorrow")
    
    # Issues and delays
    delays: Optional[List[DelayModel]] = Field(default=None, alias="Delays")
    issues: Optional[str] = Field(default=None, alias="Issues")
    
    # Related items
    related_rfis: Optional[List[OutwardReference]] = Field(default=None, alias="RelatedRFIs")
    related_inspections: Optional[List[OutwardReference]] = Field(default=None, alias="RelatedInspections")
    related_punch_items: Optional[List[OutwardReference]] = Field(default=None, alias="RelatedPunchItems")
    
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
    general_remarks: Optional[str] = Field(default=None, alias="GeneralRemarks")
    internal_notes: Optional[str] = Field(default=None, alias="InternalNotes")

    entity_def: str = Field(default="kahua_DailyReport.DailyReport", exclude=True)


def _rebuild_models() -> None:
    """Rebuild models to resolve forward references."""
    models = [
        WeatherConditionModel,
        ManpowerEntryModel,
        EquipmentEntryModel,
        MaterialDeliveryModel,
        VisitorEntryModel,
        SafetyIncidentModel,
        WorkActivityModel,
        DelayModel,
        DailyReportModel,
    ]
    for model in models:
        if hasattr(model, "model_rebuild"):
            model.model_rebuild()


_rebuild_models()
