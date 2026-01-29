# {{ Number }} - {{ Description }}

| | |
|---|---|
| **Contractor** | {{ ContractorCompany.ShortLabel | default }} |
| **Status** | {{ WorkflowStatus | default }} |
| **Type** | {{ Type | default }} |
| **Currency** | {{ CurrencyCode | default('USD') }} |

---

## Financials

| | |
|---|---:|
| Original Contract Value | {{ OriginalContractValue | currency }} |
| Approved Total | {{ ContractApprovedTotalValue | currency }} |
| Pending Total | {{ ContractPendingTotalValue | currency }} |
| Balance to Finish | {{ BalanceToFinishAmount | currency }} |

{% if ScopeOfWork %}
---

## Scope of Work

{{ ScopeOfWork }}
{% endif %}

{% if ChangeOrders %}
---

## Change Orders

| # | Description | Status | Amount |
|:--|:------------|:------:|-------:|
{% for co in ChangeOrders -%}
| {{ co.Number }} | {{ co.Description }} | {{ co.Status.Name | default }} | {{ co.TotalValue | currency }} |
{% endfor %}
{% endif %}

{% if Invoices %}
---

## Invoices

| # | Description | Date | Amount |
|:--|:------------|:----:|-------:|
{% for inv in Invoices -%}
| {{ inv.Number }} | {{ inv.Description | default }} | {{ inv.InvoiceDate | date }} | {{ inv.TotalDue | currency }} |
{% endfor %}
{% endif %}

---

**Assigned To:** {{ AssignedTo.ShortLabel | default }} | **Last Updated:** {{ ModifiedDateTime | datetime('%b %d, %Y') }}
