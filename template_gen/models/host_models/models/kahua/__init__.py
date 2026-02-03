"""
Kahua Entity Models for Portable View Templates.

This package provides comprehensive Pydantic models for all Kahua construction
management entities. These models can be used for:
- API request/response validation
- Data serialization/deserialization
- Type hints and IDE autocomplete
- Documentation generation

Each module corresponds to a domain area in the Kahua platform:
- common: Base models and shared types (Contact, Company, File, etc.)
- contact: Contact and Partition Contact models
- company: Company, Office, Certification models
- project: Project, Program models
- contract: Contract, Subcontract, Purchase Order models
- change_order: PCO, Change Order, Owner CO, CCD models
- pay_request: Pay Request, Lien Waiver models
- invoice: Invoice, Vendor Invoice, Credit Memo models
- cost: Budget, Commitment, Allowance models
- rfi: RFI models
- submittal: Submittal, Submittal Package models
- punch_list: Punch List, Punch Item models
- daily_report: Daily Report, Weather, Manpower models
- meeting: Meeting, Meeting Item, Attendee models
- inspection: Inspection, Observation models
- asset: Asset, Equipment, Maintenance models
- document: Document, Drawing, Transmittal models
- schedule: Schedule Task, Milestone models
- issue: Issue, Action Item, Risk models
- bid: Bid, Bid Package, Proposal models
- safety: Safety Incident, Observation, Permit models
- quality: NCR, Quality Inspection, Test Report models
- closeout: Warranty, As-Built, Commissioning models

Usage:
    from models.kahua import RFIModel, ContractModel, ProjectModel
    
    # Create model from dict
    rfi = RFIModel(**data)
    
    # Serialize to dict
    data = rfi.model_dump()
    
    # Serialize to JSON
    json_str = rfi.model_dump_json()
"""

# Common base models and shared types
from .common import (
    ApprovalInfo,
    Comment,
    CompanyFull,
    CompanyShortLabel,
    ContactFull,
    ContactShortLabel,
    CostItemStatus,
    CSICode,
    DistributionEntry,
    KahuaBaseModel,
    KahuaFile,
    Location,
    NotificationEntry,
    OfficeFull,
    OfficeShortLabel,
    OutwardReference,
    SecondaryComment,
    WorkBreakdownItem,
    WorkBreakdownSegment,
    WorkflowInfo,
)

# Contact models
from .contact import (
    ContactModel,
    PartitionContactModel,
)

# Company models
from .company import (
    CertificationModel,
    CompanyModel,
    OfficeModel,
)

# Project models
from .project import (
    ProgramSummaryModel,
    ProjectModel,
    ProjectPhaseModel,
    ProjectSummaryModel,
)

# Contract models
from .contract import (
    ContractLineItemModel,
    ContractModel,
    PurchaseOrderModel,
    SubcontractModel,
)

# Change order models
from .change_order import (
    ChangeOrderLineItemModel,
    ChangeOrderModel,
    ConstructionChangeDirectiveModel,
    OwnerChangeOrderModel,
    PotentialChangeOrderModel,
)

# Pay request models
from .pay_request import (
    LienWaiverModel,
    PayRequestLineItemModel,
    PayRequestModel,
)

# Invoice models
from .invoice import (
    CreditMemoModel,
    InvoiceLineItemModel,
    InvoiceModel,
    VendorInvoiceModel,
)

# Cost models
from .cost import (
    AllowanceItemModel,
    AllowanceModel,
    BudgetLineItemModel,
    BudgetModel,
    BudgetTransferModel,
    CommitmentModel,
    CostSummaryModel,
    FundingSourceModel,
)

# RFI models
from .rfi import (
    RFIModel,
    RFIResponseModel,
)

# Submittal models
from .submittal import (
    SubmittalItemModel,
    SubmittalModel,
    SubmittalPackageModel,
    SubmittalRegisterModel,
)

# Punch list models
from .punch_list import (
    PunchItemModel,
    PunchListModel,
)

# Daily report models
from .daily_report import (
    DailyReportModel,
    DelayModel,
    EquipmentEntryModel,
    ManpowerEntryModel,
    MaterialDeliveryModel,
    SafetyIncidentModel as DailyReportSafetyIncidentModel,
    VisitorEntryModel,
    WeatherConditionModel,
    WorkActivityModel,
)

# Meeting models
from .meeting import (
    MeetingAttendeeModel,
    MeetingItemModel,
    MeetingModel,
)

# Inspection models
from .inspection import (
    InspectionChecklistItemModel,
    InspectionModel,
    InspectionTypeModel,
    ObservationModel,
)

# Asset models
from .asset import (
    AssetModel,
    AssetTypeModel,
    EquipmentModel,
    MaintenanceRecordModel,
    MaintenanceScheduleModel,
)

# Document models
from .document import (
    DocumentModel,
    DocumentVersionModel,
    DrawingModel,
    FolderModel,
    TransmittalItemModel,
    TransmittalModel,
)

# Schedule models
from .schedule import (
    MilestoneModel,
    ResourceAssignmentModel,
    ScheduleBaselineModel,
    ScheduleModel,
    ScheduleTaskModel,
)

# Issue models
from .issue import (
    ActionItemModel,
    IssueModel,
    RiskModel,
)

# Bid models
from .bid import (
    BidAlternateModel,
    BidLineItemModel,
    BidModel,
    BidPackageModel,
    ProposalModel,
)

# Safety models
from .safety import (
    InjuryModel,
    PermitToWorkModel,
    SafetyIncidentModel,
    SafetyInspectionModel,
    SafetyObservationModel,
    WitnessModel,
)

# Quality models
from .quality import (
    NonConformanceReportModel,
    QualityChecklistItemModel,
    QualityInspectionModel,
    TestReportModel,
)

# Closeout models
from .closeout import (
    AsBuiltModel,
    CloseoutChecklistModel,
    CommissioningItemModel,
    OperationsManualModel,
    WarrantyClaimModel,
    WarrantyItemModel,
)


__all__ = [
    # Common
    "ApprovalInfo",
    "Comment",
    "CompanyFull",
    "CompanyShortLabel",
    "ContactFull",
    "ContactShortLabel",
    "CostItemStatus",
    "CSICode",
    "DistributionEntry",
    "KahuaBaseModel",
    "KahuaFile",
    "Location",
    "NotificationEntry",
    "OfficeFull",
    "OfficeShortLabel",
    "OutwardReference",
    "SecondaryComment",
    "WorkBreakdownItem",
    "WorkBreakdownSegment",
    "WorkflowInfo",
    # Contact
    "ContactModel",
    "PartitionContactModel",
    # Company
    "CertificationModel",
    "CompanyModel",
    "OfficeModel",
    # Project
    "ProgramSummaryModel",
    "ProjectModel",
    "ProjectPhaseModel",
    "ProjectSummaryModel",
    # Contract
    "ContractLineItemModel",
    "ContractModel",
    "PurchaseOrderModel",
    "SubcontractModel",
    # Change Order
    "ChangeOrderLineItemModel",
    "ChangeOrderModel",
    "ConstructionChangeDirectiveModel",
    "OwnerChangeOrderModel",
    "PotentialChangeOrderModel",
    # Pay Request
    "LienWaiverModel",
    "PayRequestLineItemModel",
    "PayRequestModel",
    # Invoice
    "CreditMemoModel",
    "InvoiceLineItemModel",
    "InvoiceModel",
    "VendorInvoiceModel",
    # Cost
    "AllowanceItemModel",
    "AllowanceModel",
    "BudgetLineItemModel",
    "BudgetModel",
    "BudgetTransferModel",
    "CommitmentModel",
    "CostSummaryModel",
    "FundingSourceModel",
    # RFI
    "RFIModel",
    "RFIResponseModel",
    # Submittal
    "SubmittalItemModel",
    "SubmittalModel",
    "SubmittalPackageModel",
    "SubmittalRegisterModel",
    # Punch List
    "PunchItemModel",
    "PunchListModel",
    # Daily Report
    "DailyReportModel",
    "DailyReportSafetyIncidentModel",
    "DelayModel",
    "EquipmentEntryModel",
    "ManpowerEntryModel",
    "MaterialDeliveryModel",
    "VisitorEntryModel",
    "WeatherConditionModel",
    "WorkActivityModel",
    # Meeting
    "MeetingAttendeeModel",
    "MeetingItemModel",
    "MeetingModel",
    # Inspection
    "InspectionChecklistItemModel",
    "InspectionModel",
    "InspectionTypeModel",
    "ObservationModel",
    # Asset
    "AssetModel",
    "AssetTypeModel",
    "EquipmentModel",
    "MaintenanceRecordModel",
    "MaintenanceScheduleModel",
    # Document
    "DocumentModel",
    "DocumentVersionModel",
    "DrawingModel",
    "FolderModel",
    "TransmittalItemModel",
    "TransmittalModel",
    # Schedule
    "MilestoneModel",
    "ResourceAssignmentModel",
    "ScheduleBaselineModel",
    "ScheduleModel",
    "ScheduleTaskModel",
    # Issue
    "ActionItemModel",
    "IssueModel",
    "RiskModel",
    # Bid
    "BidAlternateModel",
    "BidLineItemModel",
    "BidModel",
    "BidPackageModel",
    "ProposalModel",
    # Safety
    "InjuryModel",
    "PermitToWorkModel",
    "SafetyIncidentModel",
    "SafetyInspectionModel",
    "SafetyObservationModel",
    "WitnessModel",
    # Quality
    "NonConformanceReportModel",
    "QualityChecklistItemModel",
    "QualityInspectionModel",
    "TestReportModel",
    # Closeout
    "AsBuiltModel",
    "CloseoutChecklistModel",
    "CommissioningItemModel",
    "OperationsManualModel",
    "WarrantyClaimModel",
    "WarrantyItemModel",
]
