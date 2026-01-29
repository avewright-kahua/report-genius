from pathlib import Path
from pv_template_schema import PortableTemplate
from pv_template_renderer import TemplateRenderer

template = PortableTemplate.from_json(Path('pv_templates/saved/pv-contract-professional.json').read_text())

data = {
    'Number': '0001',
    'Description': 'Example Expense Contract',
    'ContractorCompany': {'ShortLabel': 'ACME General Contractors'},
    'WorkflowStatus': 'Sent for Signatures',
    'Type': 'Cost Plus Fixed Fee',
    'ScopeOfWork': 'General contracting for Phase 2 renovation.',
    'CurrencyCode': 'USD',
    'OriginalContractValue': 25000,
    'ContractApprovedTotalValue': 28500,
    'ContractPendingTotalValue': 30000,
    'BalanceToFinishAmount': 22000,
    'AssignedTo': {'ShortLabel': 'John Quigley'},
    'ModifiedDateTime': '2026-01-27T18:08:53',
    'ChangeOrders': [
        {'Number': 'CO-001', 'Description': 'Electrical outlets', 'Status': {'Name': 'Approved'}, 'TotalValue': 2500}
    ]
}

path, _ = TemplateRenderer().render(template, data, 'contract_v4.docx')
print(f'Generated: {path}')
