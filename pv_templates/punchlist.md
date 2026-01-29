# Punch List Item #{{ Number }}

**{{ Subject }}**

---

| | |
|:--|:--|
| **Project** | {{ DomainPartition.Name | default }} |
| **Status** | {{ Status.Name | default }} |
| **Priority** | {{ Priority | default }} |
| **Location** | {{ Location.Name | default }} |

{% if Description %}
## Description

{{ Description }}
{% endif %}

---

| | |
|:--|:--|
| **Responsible Party** | {{ ResponsibleParty.ShortLabel | default }} |
| **Ball In Court** | {{ BallInCourt.ShortLabel | default }} |
| **Due Date** | {{ DueDate | date }} |
| **Created** | {{ CreatedDateTime | datetime('%b %d, %Y') }} |

{% if ActionRequired %}
## Action Required

{{ ActionRequired }}
{% endif %}

{% if Resolution %}
## Resolution

{{ Resolution }}
{% endif %}

---

*Generated {{ _today }}*
