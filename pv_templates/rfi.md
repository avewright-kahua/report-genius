# RFI #{{ Number }}

**{{ Subject }}**

---

| | |
|:--|:--|
| **Project** | {{ DomainPartition.Name | default }} |
| **Status** | {{ Status.Name | default }} |
| **Priority** | {{ Priority | default }} |
| **Discipline** | {{ Discipline | default }} |

{% if Question %}
## Question

{{ Question }}
{% endif %}

---

| | |
|:--|:--|
| **From** | {{ Author.ShortLabel | default }} |
| **To** | {{ AssignedTo.ShortLabel | default }} |
| **Ball In Court** | {{ BallInCourt.ShortLabel | default }} |
| **Date Sent** | {{ DateSent | date }} |
| **Date Required** | {{ DateRequired | date }} |
| **Days Open** | {{ DaysOpen | default }} |

{% if Answer %}
## Answer

{{ Answer }}

**Answered By:** {{ AnsweredBy.ShortLabel | default }}  
**Date Answered:** {{ DateAnswered | date }}
{% endif %}

{% if DesignImpact or ScheduleImpact or CostImpact %}
---

## Impact Assessment

| Impact Type | Assessment |
|:------------|:-----------|
{% if DesignImpact %}| Design | {{ DesignImpact }} |{% endif %}
{% if ScheduleImpact %}| Schedule | {{ ScheduleImpact }} |{% endif %}
{% if CostImpact %}| Cost | {{ CostImpact }} |{% endif %}
{% endif %}

---

*Generated {{ _today }}*
