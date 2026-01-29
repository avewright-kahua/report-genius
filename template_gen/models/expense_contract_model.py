"""
Expense Contract entity model for Kahua Portable View templates.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import AnyUrl, Field

from .common import (
    CostItemIndex,
    KahuaBaseModel,
)

JSONDict = Dict[str, Any]


class ContractItem(KahuaBaseModel):
    currency_code: Optional[str] = None
    currency_rate_id: Optional[int] = None
    currency_rate_to_domain: Optional[Decimal] = None
    currency_rate_to_document: Optional[Decimal] = None
    accounting_completed_on: Optional[date] = None
    accounting_started_on: Optional[date] = None
    comments: Optional[List[JSONDict]] = None
    cost_current_quantity: Optional[Decimal] = None
    cost_current_total_value: Optional[Decimal] = None
    cost_current_tax_rate: Optional[Decimal] = None
    description: Optional[str] = None
    notes: Optional[str] = None
    schedule_end: Optional[date] = None
    schedule_start: Optional[date] = None
    status: Optional[str] = None
    work_breakdown_item: Optional[JSONDict] = None
    cost_item_index: Optional[CostItemIndex] = None
    currency_rate_type_id: Optional[int] = None
    cost_current_unit_value: Optional[Decimal] = None
    cost_code_index_01: Optional[JSONDict] = Field(default=None, alias="CostCodeIndex_01")
    cost_code_index_02: Optional[JSONDict] = Field(default=None, alias="CostCodeIndex_02")
    cost_code_index_03: Optional[JSONDict] = Field(default=None, alias="CostCodeIndex_03")
    domain_cost_code_index_01: Optional[JSONDict] = Field(default=None, alias="DomainCostCodeIndex_01")
    item_category: Optional[str] = None
    items: Optional[List["ContractItem"]] = None
    scope_of_work: Optional[str] = None
    number: Optional[str] = None
    contract_projected_quantity: Optional[Decimal] = None
    contract_projected_total_value: Optional[Decimal] = None
    contract_projected_unit_of_measurement: Optional[str] = None
    contract_projected_unit_value: Optional[Decimal] = None
    contract_projected_tax_rate: Optional[Decimal] = None
    contract_pending_quantity: Optional[Decimal] = None
    contract_pending_total_value: Optional[Decimal] = None
    contract_pending_unit_of_measurement: Optional[str] = None
    contract_pending_unit_value: Optional[Decimal] = None
    contract_pending_tax_rate: Optional[Decimal] = None
    contract_approved_quantity: Optional[Decimal] = None
    contract_approved_total_value: Optional[Decimal] = None
    contract_approved_unit_of_measurement: Optional[str] = None
    contract_approved_unit_value: Optional[Decimal] = None
    contract_approved_tax_rate: Optional[Decimal] = None


class ContractExhibit(KahuaBaseModel):
    exhibit_type: Optional[str] = None
    exhibit_name: Optional[str] = None
    exhibit_template_file: Optional[JSONDict] = None
    exhibit_file: Optional[JSONDict] = None


class ContractorCertification(KahuaBaseModel):
    issuing_agency: Optional[str] = None
    jurisdiction: Optional[str] = None
    reference_number: Optional[str] = None
    classification: Optional[str] = None
    type_: Optional[str] = Field(default=None, alias="Type")
    issued_date: Optional[date] = None
    expiration_date: Optional[date] = None
    url_link: Optional[AnyUrl] = None
    applies_to_all_offices: Optional[bool] = None
    offices: Optional[List[JSONDict]] = None
    notes: Optional[str] = None
    long_label: Optional[str] = None
    short_label: Optional[str] = None


class ExpenseContractModel(KahuaBaseModel):
    outward_references: Optional[List[JSONDict]] = None
    comments: Optional[List[JSONDict]] = None
    cost_items_total_total_value: Optional[Decimal] = None
    description: Optional[str] = None
    notes: Optional[str] = None
    number: Optional[str] = None
    schedule_end: Optional[date] = None
    schedule_start: Optional[date] = None
    status: Optional[str] = None
    cost_unit_entry_type: Optional[str] = None
    tax_entry_type: Optional[str] = None
    assigned_to: Optional[str] = None
    date_executed: Optional[date] = None
    date_sent_for_review: Optional[date] = None
    date_sent_for_signature: Optional[date] = None
    date_reviewed: Optional[date] = None
    items_include_quantity: Optional[bool] = None
    custom_contact1: Optional[JSONDict] = None
    custom_contact2: Optional[JSONDict] = None
    custom_contact3: Optional[JSONDict] = None
    custom_contact4: Optional[JSONDict] = None
    custom_contact5: Optional[JSONDict] = None
    custom_text1: Optional[str] = None
    custom_text2: Optional[str] = None
    custom_text3: Optional[str] = None
    custom_text4: Optional[str] = None
    custom_text5: Optional[str] = None
    custom_date1: Optional[date] = None
    custom_date2: Optional[date] = None
    custom_date3: Optional[date] = None
    custom_date4: Optional[date] = None
    custom_date5: Optional[date] = None
    custom_unlimited_text1: Optional[str] = None
    custom_unlimited_text2: Optional[str] = None
    custom_unlimited_text3: Optional[str] = None
    custom_unlimited_text4: Optional[str] = None
    custom_unlimited_text5: Optional[str] = None
    items: Optional[List[ContractItem]] = None
    client_contact: Optional[JSONDict] = None
    client_company: Optional[JSONDict] = None
    client_company_location: Optional[JSONDict] = None
    client_company_office: Optional[JSONDict] = None
    contractor_contact: Optional[JSONDict] = None
    contractor_company: Optional[JSONDict] = None
    contractor_company_location: Optional[JSONDict] = None
    contractor_company_office: Optional[JSONDict] = None
    date: Optional[date] = None
    general_provisions: Optional[str] = None
    not_to_exceed_amount: Optional[Decimal] = None
    number_of_pages: Optional[int] = None
    scope_of_work: Optional[str] = None
    stored_material_retainage_rate: Optional[Decimal] = None
    type_: Optional[str] = Field(default=None, alias="Type")
    work_retainage_rate: Optional[Decimal] = None
    overbilling_limits: Optional[str] = None
    contract_approved_total_value: Optional[Decimal] = None
    contract_exhibits: Optional[List[ContractExhibit]] = None
    date_contract_required: Optional[date] = None
    contract_signer_contact: Optional[JSONDict] = None
    custom_lookup1: Optional[str] = None
    custom_lookup2: Optional[str] = None
    custom_lookup3: Optional[str] = None
    custom_lookup4: Optional[str] = None
    custom_lookup5: Optional[str] = None
    addenda: Optional[str] = None
    award_date: Optional[date] = None
    notice_of_award: Optional[date] = None
    substantial_completion_actual: Optional[date] = None
    final_completion: Optional[date] = None
    notice_of_completion: Optional[date] = None
    work_package: Optional[JSONDict] = None
    liquidated_damages: Optional[bool] = None
    liquidated_damages_start_date: Optional[date] = None
    liquidated_damages_per_day: Optional[Decimal] = None
    liquidated_damages_not_to_exceed_amount: Optional[Decimal] = None
    contractor_certifications: Optional[List[ContractorCertification]] = None
    cost_items_tax_total_total_value: Optional[Decimal] = None
    cost_items_non_tax_total_total_value: Optional[Decimal] = None
    contract_items_total_amount: Optional[Decimal] = None
    original_contract_amount: Optional[Decimal] = None
    approved_changes_amount: Optional[Decimal] = None
    current_contract_amount: Optional[Decimal] = None
    contract_gross_total_amount: Optional[Decimal] = None

    # Entity Definition (for template generator)
    entity_def: str = Field(default="kahua.expensecontract", exclude=True)


def _rebuild_models() -> None:
    """Rebuild models to resolve forward references."""
    models = [
        ContractItem,
        ExpenseContractModel,
    ]
    for model in models:
        if hasattr(model, "model_rebuild"):
            model.model_rebuild()


_rebuild_models()
