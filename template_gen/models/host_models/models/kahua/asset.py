"""
Asset and equipment entity models for Kahua Portable View templates.
Entities: kahua_Assets.Asset, kahua_Equipment.Equipment
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
    KahuaBaseModel,
    KahuaFile,
    Location,
    OutwardReference,
)


class AssetTypeModel(KahuaBaseModel):
    """Asset type/class definition."""

    name: Optional[str] = Field(default=None, alias="Name")
    code: Optional[str] = Field(default=None, alias="Code")
    description: Optional[str] = Field(default=None, alias="Description")
    category: Optional[str] = Field(default=None, alias="Category")
    parent_type: Optional[str] = Field(default=None, alias="ParentType")
    
    # Attributes
    useful_life_years: Optional[int] = Field(default=None, alias="UsefulLifeYears")
    depreciation_method: Optional[str] = Field(default=None, alias="DepreciationMethod")
    
    is_active: Optional[bool] = Field(default=None, alias="IsActive")

    entity_def: str = Field(default="kahua_Assets.AssetType", exclude=True)


class MaintenanceScheduleModel(KahuaBaseModel):
    """Asset maintenance schedule entry."""

    schedule_type: Optional[str] = Field(default=None, alias="ScheduleType")
    description: Optional[str] = Field(default=None, alias="Description")
    frequency: Optional[str] = Field(default=None, alias="Frequency")  # Daily, Weekly, Monthly, etc.
    interval: Optional[int] = Field(default=None, alias="Interval")
    interval_unit: Optional[str] = Field(default=None, alias="IntervalUnit")
    
    last_performed: Optional[date] = Field(default=None, alias="LastPerformed")
    next_due: Optional[date] = Field(default=None, alias="NextDue")
    
    performed_by: Optional[ContactFull] = Field(default=None, alias="PerformedBy")
    vendor: Optional[CompanyFull] = Field(default=None, alias="Vendor")
    
    estimated_cost: Optional[Decimal] = Field(default=None, alias="EstimatedCost")
    notes: Optional[str] = Field(default=None, alias="Notes")


class MaintenanceRecordModel(KahuaBaseModel):
    """Asset maintenance record."""

    # Identification
    number: Optional[str] = Field(default=None, alias="Number")
    work_order_number: Optional[str] = Field(default=None, alias="WorkOrderNumber")
    description: Optional[str] = Field(default=None, alias="Description")
    
    # Type and status
    maintenance_type: Optional[str] = Field(default=None, alias="MaintenanceType")  # Preventive, Corrective, etc.
    status: Optional[str] = Field(default=None, alias="Status")
    priority: Optional[str] = Field(default=None, alias="Priority")
    
    # Dates
    date_scheduled: Optional[date] = Field(default=None, alias="DateScheduled")
    date_performed: Optional[date] = Field(default=None, alias="DatePerformed")
    date_completed: Optional[date] = Field(default=None, alias="DateCompleted")
    
    # People
    performed_by: Optional[ContactFull] = Field(default=None, alias="PerformedBy")
    technician: Optional[ContactFull] = Field(default=None, alias="Technician")
    reported_by: Optional[ContactFull] = Field(default=None, alias="ReportedBy")
    
    # Vendor
    vendor: Optional[CompanyFull] = Field(default=None, alias="Vendor")
    
    # Work performed
    work_performed: Optional[str] = Field(default=None, alias="WorkPerformed")
    parts_replaced: Optional[str] = Field(default=None, alias="PartsReplaced")
    findings: Optional[str] = Field(default=None, alias="Findings")
    
    # Costs
    labor_hours: Optional[float] = Field(default=None, alias="LaborHours")
    labor_cost: Optional[Decimal] = Field(default=None, alias="LaborCost")
    parts_cost: Optional[Decimal] = Field(default=None, alias="PartsCost")
    total_cost: Optional[Decimal] = Field(default=None, alias="TotalCost")
    
    # Parent asset reference
    parent_asset: Optional[OutwardReference] = Field(default=None, alias="ParentAsset")
    
    # Attachments
    attachments: Optional[List[KahuaFile]] = Field(default=None, alias="Attachments")
    
    notes: Optional[str] = Field(default=None, alias="Notes")

    entity_def: str = Field(default="kahua_Assets.MaintenanceRecord", exclude=True)


class AssetModel(KahuaBaseModel):
    """
    Asset entity model.
    Entity Definition: kahua_Assets.Asset
    """

    # Identification
    number: Optional[str] = Field(default=None, alias="Number")
    asset_number: Optional[str] = Field(default=None, alias="AssetNumber")
    asset_tag: Optional[str] = Field(default=None, alias="AssetTag")
    name: Optional[str] = Field(default=None, alias="Name")
    description: Optional[str] = Field(default=None, alias="Description")
    
    # Status
    status: Optional[CostItemStatus] = Field(default=None, alias="Status")
    condition: Optional[str] = Field(default=None, alias="Condition")  # New, Good, Fair, Poor
    operational_status: Optional[str] = Field(default=None, alias="OperationalStatus")  # Active, Inactive, Retired
    
    # Classification
    asset_type: Optional[AssetTypeModel] = Field(default=None, alias="AssetType")
    asset_class: Optional[str] = Field(default=None, alias="AssetClass")
    asset_category: Optional[str] = Field(default=None, alias="AssetCategory")
    
    # Location
    location: Optional[Location] = Field(default=None, alias="Location")
    location_description: Optional[str] = Field(default=None, alias="LocationDescription")
    building: Optional[str] = Field(default=None, alias="Building")
    floor: Optional[str] = Field(default=None, alias="Floor")
    room: Optional[str] = Field(default=None, alias="Room")
    space: Optional[str] = Field(default=None, alias="Space")
    
    # Manufacturer info
    manufacturer: Optional[str] = Field(default=None, alias="Manufacturer")
    model: Optional[str] = Field(default=None, alias="Model")
    model_number: Optional[str] = Field(default=None, alias="ModelNumber")
    serial_number: Optional[str] = Field(default=None, alias="SerialNumber")
    
    # Dates
    date_acquired: Optional[date] = Field(default=None, alias="DateAcquired")
    date_installed: Optional[date] = Field(default=None, alias="DateInstalled")
    date_commissioned: Optional[date] = Field(default=None, alias="DateCommissioned")
    date_retired: Optional[date] = Field(default=None, alias="DateRetired")
    manufacture_date: Optional[date] = Field(default=None, alias="ManufactureDate")
    
    # Lifecycle
    useful_life_years: Optional[int] = Field(default=None, alias="UsefulLifeYears")
    expected_end_of_life: Optional[date] = Field(default=None, alias="ExpectedEndOfLife")
    
    # Financial
    acquisition_cost: Optional[Decimal] = Field(default=None, alias="AcquisitionCost")
    current_value: Optional[Decimal] = Field(default=None, alias="CurrentValue")
    book_value: Optional[Decimal] = Field(default=None, alias="BookValue")
    replacement_cost: Optional[Decimal] = Field(default=None, alias="ReplacementCost")
    depreciation_method: Optional[str] = Field(default=None, alias="DepreciationMethod")
    salvage_value: Optional[Decimal] = Field(default=None, alias="SalvageValue")
    
    # Warranty
    warranty_start: Optional[date] = Field(default=None, alias="WarrantyStart")
    warranty_end: Optional[date] = Field(default=None, alias="WarrantyEnd")
    warranty_vendor: Optional[CompanyFull] = Field(default=None, alias="WarrantyVendor")
    warranty_description: Optional[str] = Field(default=None, alias="WarrantyDescription")
    under_warranty: Optional[bool] = Field(default=None, alias="UnderWarranty")
    
    # Ownership
    owner: Optional[ContactFull] = Field(default=None, alias="Owner")
    custodian: Optional[ContactFull] = Field(default=None, alias="Custodian")
    assigned_to: Optional[ContactFull] = Field(default=None, alias="AssignedTo")
    responsible_party: Optional[ContactFull] = Field(default=None, alias="ResponsibleParty")
    
    # Vendor/Supplier
    vendor: Optional[CompanyFull] = Field(default=None, alias="Vendor")
    supplier: Optional[CompanyFull] = Field(default=None, alias="Supplier")
    
    # Technical specs
    specifications: Optional[str] = Field(default=None, alias="Specifications")
    capacity: Optional[str] = Field(default=None, alias="Capacity")
    power_requirements: Optional[str] = Field(default=None, alias="PowerRequirements")
    dimensions: Optional[str] = Field(default=None, alias="Dimensions")
    weight: Optional[str] = Field(default=None, alias="Weight")
    
    # Maintenance
    maintenance_schedules: Optional[List[MaintenanceScheduleModel]] = Field(default=None, alias="MaintenanceSchedules")
    maintenance_records: Optional[List[MaintenanceRecordModel]] = Field(default=None, alias="MaintenanceRecords")
    last_maintenance: Optional[date] = Field(default=None, alias="LastMaintenance")
    next_maintenance: Optional[date] = Field(default=None, alias="NextMaintenance")
    maintenance_vendor: Optional[CompanyFull] = Field(default=None, alias="MaintenanceVendor")
    
    # Parent/child relationships
    parent_asset: Optional[OutwardReference] = Field(default=None, alias="ParentAsset")
    child_assets: Optional[List[OutwardReference]] = Field(default=None, alias="ChildAssets")
    
    # Related items
    related_documents: Optional[List[OutwardReference]] = Field(default=None, alias="RelatedDocuments")
    
    # Photos and attachments
    photos: Optional[List[KahuaFile]] = Field(default=None, alias="Photos")
    attachments: Optional[List[KahuaFile]] = Field(default=None, alias="Attachments")
    manuals: Optional[List[KahuaFile]] = Field(default=None, alias="Manuals")
    
    # Comments
    comments: Optional[List[Comment]] = Field(default=None, alias="Comments")
    
    # Notes
    notes: Optional[str] = Field(default=None, alias="Notes")
    maintenance_notes: Optional[str] = Field(default=None, alias="MaintenanceNotes")

    entity_def: str = Field(default="kahua_Assets.Asset", exclude=True)


class EquipmentModel(KahuaBaseModel):
    """
    Equipment entity model (construction equipment).
    Entity Definition: kahua_Equipment.Equipment
    """

    # Identification
    number: Optional[str] = Field(default=None, alias="Number")
    equipment_number: Optional[str] = Field(default=None, alias="EquipmentNumber")
    equipment_id: Optional[str] = Field(default=None, alias="EquipmentId")
    name: Optional[str] = Field(default=None, alias="Name")
    description: Optional[str] = Field(default=None, alias="Description")
    
    # Status
    status: Optional[str] = Field(default=None, alias="Status")  # Available, In Use, Down, etc.
    condition: Optional[str] = Field(default=None, alias="Condition")
    
    # Classification
    equipment_type: Optional[str] = Field(default=None, alias="EquipmentType")
    equipment_class: Optional[str] = Field(default=None, alias="EquipmentClass")
    category: Optional[str] = Field(default=None, alias="Category")
    
    # Location
    current_location: Optional[Location] = Field(default=None, alias="CurrentLocation")
    assigned_project: Optional[str] = Field(default=None, alias="AssignedProject")
    
    # Manufacturer info
    manufacturer: Optional[str] = Field(default=None, alias="Manufacturer")
    model: Optional[str] = Field(default=None, alias="Model")
    model_number: Optional[str] = Field(default=None, alias="ModelNumber")
    serial_number: Optional[str] = Field(default=None, alias="SerialNumber")
    vin: Optional[str] = Field(default=None, alias="VIN")
    license_plate: Optional[str] = Field(default=None, alias="LicensePlate")
    year: Optional[int] = Field(default=None, alias="Year")
    
    # Ownership
    ownership_type: Optional[str] = Field(default=None, alias="OwnershipType")  # Owned, Rented, Leased
    owner: Optional[CompanyFull] = Field(default=None, alias="Owner")
    rental_vendor: Optional[CompanyFull] = Field(default=None, alias="RentalVendor")
    
    # Rental info
    rental_start: Optional[date] = Field(default=None, alias="RentalStart")
    rental_end: Optional[date] = Field(default=None, alias="RentalEnd")
    rental_rate: Optional[Decimal] = Field(default=None, alias="RentalRate")
    rental_rate_unit: Optional[str] = Field(default=None, alias="RentalRateUnit")  # Hourly, Daily, Weekly, Monthly
    
    # Usage tracking
    meter_reading: Optional[float] = Field(default=None, alias="MeterReading")
    meter_unit: Optional[str] = Field(default=None, alias="MeterUnit")  # Hours, Miles, etc.
    last_meter_date: Optional[date] = Field(default=None, alias="LastMeterDate")
    
    # Capacity/Specs
    capacity: Optional[str] = Field(default=None, alias="Capacity")
    fuel_type: Optional[str] = Field(default=None, alias="FuelType")
    engine_size: Optional[str] = Field(default=None, alias="EngineSize")
    weight: Optional[str] = Field(default=None, alias="Weight")
    
    # Operator
    operator: Optional[ContactFull] = Field(default=None, alias="Operator")
    operator_required: Optional[bool] = Field(default=None, alias="OperatorRequired")
    certifications_required: Optional[List[str]] = Field(default=None, alias="CertificationsRequired")
    
    # Maintenance
    last_service: Optional[date] = Field(default=None, alias="LastService")
    next_service: Optional[date] = Field(default=None, alias="NextService")
    service_interval: Optional[int] = Field(default=None, alias="ServiceInterval")
    service_interval_unit: Optional[str] = Field(default=None, alias="ServiceIntervalUnit")
    
    # Insurance
    insurance_policy: Optional[str] = Field(default=None, alias="InsurancePolicy")
    insurance_expiration: Optional[date] = Field(default=None, alias="InsuranceExpiration")
    
    # Costs
    hourly_cost: Optional[Decimal] = Field(default=None, alias="HourlyCost")
    daily_cost: Optional[Decimal] = Field(default=None, alias="DailyCost")
    
    # Attachments
    photos: Optional[List[KahuaFile]] = Field(default=None, alias="Photos")
    attachments: Optional[List[KahuaFile]] = Field(default=None, alias="Attachments")
    
    notes: Optional[str] = Field(default=None, alias="Notes")

    entity_def: str = Field(default="kahua_Equipment.Equipment", exclude=True)


def _rebuild_models() -> None:
    """Rebuild models to resolve forward references."""
    models = [
        AssetTypeModel,
        MaintenanceScheduleModel,
        MaintenanceRecordModel,
        AssetModel,
        EquipmentModel,
    ]
    for model in models:
        if hasattr(model, "model_rebuild"):
            model.model_rebuild()


_rebuild_models()
