"""
Entity models - Kahua entity schema definitions.
"""

# Common models (shared types)
from report_genius.models.common import (
    Address,
    Certification,
    Comment,
    Company,
    ContactFull,
    ContactShortLabel,
    CostCodeIndex,
    CostItemIndex,
    CSICode,
    CurrentFile,
    DistributionEntry,
    JSONDict,
    KahuaBaseModel,
    Location,
    MarkupFile,
    NotificationEntry,
    Office,
    OutwardReference,
    Person,
    Project,
    ProjectContact,
    ProjectProperty,
    SecondaryComment,
    SourceFile,
    WorkBreakdownItem,
    WorkPackage,
)

# Entity models
from report_genius.models.expense_change_order import (
    ChangeOrderItem,
    ExpenseChangeOrderModel,
)
from report_genius.models.expense_contract import (
    ContractExhibit,
    ContractItem,
    ContractorCertification,
    ExpenseContractModel,
)
from report_genius.models.field_observation import (
    CompanyRef,
    FieldObservationModel,
    ObservedByContact,
)
from report_genius.models.invoice import (
    InvoiceItem,
    InvoiceModel,
)
from report_genius.models.rfi import (
    RFIModel,
    SourceCompany,
)
from report_genius.models.submittal import (
    ContactLabel,
    Contributor,
    FileComment,
    FileCurrent,
    PortableView,
    ReviewItem,
    SubmittalDistributionEntry,
    SubmittalItem,
    SubmittalModel,
    SubmittalOutwardReference,
)

__all__ = [
    # Common models
    "Address",
    "Certification",
    "Comment",
    "Company",
    "ContactFull",
    "ContactShortLabel",
    "CostCodeIndex",
    "CostItemIndex",
    "CSICode",
    "CurrentFile",
    "DistributionEntry",
    "JSONDict",
    "KahuaBaseModel",
    "Location",
    "MarkupFile",
    "NotificationEntry",
    "Office",
    "OutwardReference",
    "Person",
    "Project",
    "ProjectContact",
    "ProjectProperty",
    "SecondaryComment",
    "SourceFile",
    "WorkBreakdownItem",
    "WorkPackage",
    # Expense Change Order
    "ChangeOrderItem",
    "ExpenseChangeOrderModel",
    # Expense Contract
    "ContractExhibit",
    "ContractItem",
    "ContractorCertification",
    "ExpenseContractModel",
    # Field Observation
    "CompanyRef",
    "FieldObservationModel",
    "ObservedByContact",
    # Invoice
    "InvoiceItem",
    "InvoiceModel",
    # RFI
    "RFIModel",
    "SourceCompany",
    # Submittal
    "ContactLabel",
    "Contributor",
    "FileComment",
    "FileCurrent",
    "PortableView",
    "ReviewItem",
    "SubmittalDistributionEntry",
    "SubmittalItem",
    "SubmittalModel",
    "SubmittalOutwardReference",
]
