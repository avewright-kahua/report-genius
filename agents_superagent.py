import os, json, logging, asyncio
from typing import Optional, List, Any, Dict
import httpx
from pydantic import BaseModel, Field, ValidationError
from openai import AsyncAzureOpenAI

# Report generation
from report_generator import create_report, ReportGenerator, ReportConfig, ChartSpec

try:
    from agents import Agent, Runner, OpenAIChatCompletionsModel, function_tool, SQLiteSession
except Exception as e:
    raise RuntimeError("The 'agents' package must be importable for this script to run.") from e

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("kahua_superagent")

# Azure OpenAI client
azure_client = AsyncAzureOpenAI(
    api_key=os.environ["AZURE_KEY"],
    azure_endpoint=os.environ["AZURE_ENDPOINT"],
    api_version=os.environ["API_VERSION"],
)
MODEL_DEPLOYMENT = os.environ["AZURE_DEPLOYMENT"]

# Kahua constants and auth helpers
# ACTIVITY_URL = "https://devweeklyservice.kahua.com/v2/domains/AWrightCo/projects/{project_id}/apps/kahua_AEC_RFI/activities/run"
QUERY_URL_TEMPLATE = "https://demo01service.kahua.com/v2/domains/Summit/projects/{project_id}/query?returnDefaultAttributes=true"

KAHUA_BASIC_AUTH = os.getenv("KAHUA_BASIC_AUTH")

def _auth_header_value() -> str:
    if not KAHUA_BASIC_AUTH:
        raise RuntimeError("KAHUA_BASIC_AUTH not set")
    return KAHUA_BASIC_AUTH if KAHUA_BASIC_AUTH.strip().lower().startswith("basic ") \
           else f"Basic {KAHUA_BASIC_AUTH}"

HEADERS_JSON = lambda: {"Content-Type": "application/json", "Authorization": _auth_header_value()}

# Entity alias table (extend freely)
ENTITY_ALIASES: Dict[str, str] = {
    "project": "kahua_Project.Project",
    "rfi": "kahua_AEC_RFI.RFI",
    "submittal": "kahua_AEC_Submittal.Submittal",
    "change order": "kahua_AEC_ChangeOrder.ChangeOrder",
    "punchlist": "kahua_AEC_PunchList.PunchListItem",
    "punch list": "kahua_AEC_PunchList.PunchListItem",
    "field observation": "kahua_AEC_FieldObservation.FieldObservationItem",
    "contract": "kahua_Contract.Contract",
    "contract item": "kahua_Contract.ContractItem",

}

def resolve_entity_def(name_or_def: str) -> str:
    key = (name_or_def or "").strip().lower()
    return ENTITY_ALIASES.get(key, name_or_def)

def _extract_first_entity(data: Dict[str, Any], set_name: str) -> Dict[str, Any]:
    sets = data.get("sets") or []
    for s in sets:
        if s.get("name") == set_name:
            ents = s.get("entities") or []
            if ents:
                return ents[0]
    for key in ("entities", "items", "results"):
        if isinstance(data.get(key), list) and data[key]:
            return data[key][0]
    return {}

# Core entity categories for smart discovery
ENTITY_CATEGORIES = {
    "cost": [
        "kahua_Contract.Contract", "kahua_Contract.ContractItem",
        "kahua_ContractChangeOrder.ContractChangeOrder", "kahua_ContractChangeOrder.ContractChangeOrderItem",
        "kahua_ContractInvoice.ContractInvoice", "kahua_ContractInvoice.ContractInvoiceItem",
        "kahua_PurchaseOrder.PurchaseOrder", "kahua_PurchaseOrder.PurchaseOrderItem",
        "kahua_FundingBudget.FundingBudget", "kahua_BudgetAdjustment.BudgetAdjustment",
        "kahua_ClientContract.ClientContract", "kahua_ClientContractInvoice.ClientContractInvoice",
    ],
    "field": [
        "kahua_AEC_RFI.RFI", "kahua_AEC_Sub_RFI.SubRFI", "kahua_AEC_SubGC_RFI.SubGCRFI",
        "kahua_AEC_Submittal.SubmittalItem", "kahua_AEC_SubmittalPackage.SubmittalPackage",
        "kahua_AEC_PunchList.PunchListItem", "kahua_AEC_FieldObservation.FieldObservationItem",
        "kahua_AEC_DailyReport.DailyReport",
    ],
    "communications": [
        "kahua_AEC_Communications.CommunicationsMessage", "kahua_AEC_Communications.CommunicationsTransmittal",
        "kahua_AEC_Communications.CommunicationsMemo", "kahua_AEC_Communications.CommunicationsLetter",
        "kahua_Meeting.Meeting", "kahua_Meeting.ActionItem",
    ],
    "documents": [
        "kahua_FileManager.File", "kahua_FileManager.DrawingLog", "kahua_FileManager.DrawingLogRevision",
        "kahua_AEC_DesignReviewSets.DesignReviewSet", "kahua_AEC_DesignReviewComments.DesignReviewComment",
    ],
    "project": [
        "kahua_Project.Project", "kahua_Location.Location",
        "kahua_CompanyManager.kahua_Company", "kahua_ProjectDirectory_Companies.ProjectDirectoryCompany",
        "kahua_ProjectDirectory_Contacts.ProjectDirectoryContact",
    ],
    "risk": [
        "kahua_Issue.Issue", "kahua_RiskRegister.RiskRegister", "kahua_ComplianceTracking.ComplianceTracking",
    ],
}

# Tools: Discovery / Query / Report Generation

@function_tool
async def discover_environment(project_id: int = 0, categories: Optional[List[str]] = None, scope: Optional[str] = "Any") -> dict:
    """
    Discover what data exists in the Kahua environment. Returns entity counts by category.
    
    ALWAYS call this first when the user asks broad questions like:
    - "What do I have?"
    - "Show me my data"
    - "What entities have records?"
    - "What can you report on?"
    
    Args:
        project_id: Project to scan. Use 0 with scope="Any" for organization-wide (default).
        categories: Optional filter. Options: "cost", "field", "communications", "documents", "project", "risk".
                    If not specified, scans all categories.
        scope: Query scope. "Any" queries across ALL projects (default). "DomainPartition" for specific project only.
    
    Returns:
        Dict with entity counts organized by category, plus recommendations for reports.
    """
    cats_to_scan = categories if categories else list(ENTITY_CATEGORIES.keys())
    results = {"project_id": project_id, "scope": scope, "categories": {}, "summary": {}, "recommendations": []}
    total_records = 0
    entities_with_data = []
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        for cat in cats_to_scan:
            if cat not in ENTITY_CATEGORIES:
                continue
            results["categories"][cat] = {}
            for entity_def in ENTITY_CATEGORIES[cat]:
                query_url = QUERY_URL_TEMPLATE.format(project_id=project_id)
                # Proper Kahua query format with Partition scope
                qpayload: Dict[str, Any] = {
                    "PropertyName": "Query", 
                    "EntityDef": entity_def
                }
                # Add partition scope for cross-project queries
                if scope:
                    qpayload["Partition"] = {"Scope": scope}
                try:
                    resp = await client.post(query_url, headers=HEADERS_JSON(), json=qpayload)
                    if resp.status_code < 400:
                        body = resp.json()
                        # Get count from response (v2 format has "count" field)
                        count = body.get("count", 0)
                        if count == 0 and isinstance(body, dict):
                            for key in ("entities", "results", "items"):
                                if isinstance(body.get(key), list):
                                    count = len(body[key])
                                    break
                            # Also check nested sets
                            for s in body.get("sets", []):
                                if isinstance(s.get("entities"), list):
                                    count = max(count, len(s["entities"]))
                        results["categories"][cat][entity_def] = count
                        total_records += count
                        if count > 0:
                            entities_with_data.append({"entity": entity_def, "count": count, "category": cat})
                except Exception as e:
                    results["categories"][cat][entity_def] = f"error: {str(e)}"
    
    # Build summary
    results["summary"] = {
        "total_records": total_records,
        "entities_with_data": len(entities_with_data),
        "top_entities": sorted(entities_with_data, key=lambda x: x["count"], reverse=True)[:10]
    }
    
    # Generate smart recommendations based on what data exists
    recs = []
    top_ents = {e["entity"] for e in results["summary"]["top_entities"]}
    
    if any("RFI" in e for e in top_ents):
        recs.append({"report": "RFI Status Report", "reason": "RFI data found - can analyze response times, open/closed status, by discipline"})
    if any("PunchList" in e for e in top_ents):
        recs.append({"report": "Punch List Report", "reason": "Punch list data found - can show closure rates, by location/trade, priority breakdown"})
    if any("Contract" in e for e in top_ents):
        recs.append({"report": "Cost & Contracts Report", "reason": "Contract data found - can analyze commitments, change orders, billing status"})
    if any("Invoice" in e for e in top_ents):
        recs.append({"report": "Financial Summary Report", "reason": "Invoice data found - can show billing progress, cashflow, payment status"})
    if any("Submittal" in e for e in top_ents):
        recs.append({"report": "Submittal Log Report", "reason": "Submittal data found - can track approvals, review cycles, outstanding items"})
    if any("DailyReport" in e for e in top_ents):
        recs.append({"report": "Progress Report", "reason": "Daily reports found - can summarize work completed, manpower, weather impacts"})
    if any("FieldObservation" in e for e in top_ents):
        recs.append({"report": "Field Issues Report", "reason": "Field observations found - can document issues, photos, corrective actions"})
    
    if not recs:
        recs.append({"report": "Data Inventory Report", "reason": "Limited data found - can create a summary of available records and next steps"})
    
    results["recommendations"] = recs
    return results


@function_tool
async def find_project(search_term: str) -> dict:
    """
    Find a project by name or partial match. ALWAYS use this when a user mentions a project by name.
    
    Args:
        search_term: Project name or partial name to search for (case-insensitive)
    
    Returns:
        Dict with matching projects including their IDs, names, and key details.
    """
    query_url = QUERY_URL_TEMPLATE.format(project_id=0)
    qpayload = {"PropertyName": "Query", "EntityDef": "kahua_Project.Project"}
    
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.post(query_url, headers=HEADERS_JSON(), json=qpayload)
        if resp.status_code >= 400:
            return {"status": "error", "message": "Failed to query projects"}
        body = resp.json()
    
    # Extract projects from response
    projects = []
    for key in ("entities", "results", "items"):
        if isinstance(body.get(key), list):
            projects = body[key]
            break
    for s in body.get("sets", []):
        if isinstance(s.get("entities"), list) and s["entities"]:
            projects = s["entities"]
            break
    
    # Search for matches (case-insensitive, partial match)
    search_lower = search_term.lower()
    matches = []
    for proj in projects:
        name = proj.get("Name", proj.get("name", ""))
        if search_lower in name.lower():
            matches.append({
                "id": proj.get("Id", proj.get("id", proj.get("ProjectId"))),
                "name": name,
                "description": proj.get("Description", proj.get("description", "")),
                "status": proj.get("Status", proj.get("status", "")),
                "phase": proj.get("Phase", proj.get("phase", "")),
            })
    
    if not matches:
        # Return all projects if no match found
        return {
            "status": "no_match",
            "search_term": search_term,
            "message": f"No project found matching '{search_term}'",
            "all_projects": [{"id": p.get("Id", p.get("id")), "name": p.get("Name", p.get("name", ""))} for p in projects[:20]]
        }
    
    return {
        "status": "ok",
        "search_term": search_term,
        "matches": matches,
        "best_match": matches[0] if len(matches) == 1 else None,
        "message": f"Found {len(matches)} project(s) matching '{search_term}'" + (f" - using ID {matches[0]['id']}" if len(matches) == 1 else "")
    }


@function_tool
async def get_entity_schema(entity_def: str, project_id: int = 0) -> dict:
    """
    Get the field schema for an entity type by sampling a record.
    Use this to understand what fields/attributes are available before building a report.
    
    Args:
        entity_def: The entity type to inspect (e.g., "kahua_AEC_RFI.RFI" or alias like "rfi")
        project_id: Project context. Use 0 for root (default).
    
    Returns:
        Dict with field names, sample values, and data types.
    """
    ent = resolve_entity_def(entity_def)
    query_url = QUERY_URL_TEMPLATE.format(project_id=project_id)
    qpayload = {"PropertyName": "Query", "EntityDef": ent}
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(query_url, headers=HEADERS_JSON(), json=qpayload)
        if resp.status_code >= 400:
            return {"status": "error", "message": f"Failed to query {ent}"}
        body = resp.json()
    
    # Extract a sample entity
    sample = None
    if isinstance(body, dict):
        for key in ("entities", "results", "items"):
            if isinstance(body.get(key), list) and body[key]:
                sample = body[key][0]
                break
        if not sample:
            for s in body.get("sets", []):
                if isinstance(s.get("entities"), list) and s["entities"]:
                    sample = s["entities"][0]
                    break
    
    if not sample:
        return {"status": "ok", "entity_def": ent, "fields": [], "message": "No records found to sample schema"}
    
    # Build field info
    fields = []
    for key, value in sample.items():
        field_info = {
            "name": key,
            "type": type(value).__name__,
            "sample": str(value)[:100] if value is not None else None
        }
        fields.append(field_info)
    
    return {
        "status": "ok",
        "entity_def": ent,
        "record_count": len(body.get("entities", body.get("results", body.get("items", [])))),
        "fields": sorted(fields, key=lambda x: x["name"]),
    }


@function_tool
async def query_entities(
    entity_def: str, 
    project_id: int = 0, 
    limit: int = 50,
    skip: int = 0,
    conditions_json: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_direction: Optional[str] = "Ascending",
    fields: Optional[str] = None,
    scope: Optional[str] = None,
    entity_ids: Optional[str] = None
) -> dict:
    """
    Run a powerful server-side query for entities with filtering, sorting, and field selection.
    
    Args:
        entity_def: Entity type. Alias ("rfi", "contract") or full ("kahua_AEC_RFI.RFI").
        project_id: Project ID. Use 0 for root/domain queries.
        limit: Max results (default 50). Use higher for reports needing full data.
        skip: Number of records to skip (for paging).
        conditions_json: JSON string for filtering. Example:
            '[{"path": "Status", "type": "EqualTo", "value": "Open"}]'
            '[{"path": "DueDate", "type": "LessThan", "value": "2026-01-01"}]'
            Multiple conditions with AND:
            '[{"all_of": [{"path": "Status", "type": "EqualTo", "value": "Open"}, {"path": "Priority", "type": "EqualTo", "value": "High"}]}]'
            Types: EqualTo, NotEqualTo, Contains, StartsWith, EndsWith, GreaterThan, 
                   LessThan, GreaterThanOrEqualTo, LessThanOrEqualTo, HasValue, HasNoValue, In
        sort_by: Attribute path to sort by (e.g., "CreatedDateTime", "Number", "Name").
        sort_direction: "Ascending" or "Descending".
        fields: Comma-separated field names to return (reduces payload). E.g., "Number,Name,Status,DueDate"
        scope: Query scope. "Any" for all records in domain, "Domain" for root partition only.
        entity_ids: Comma-separated entity IDs to query directly (fastest method if IDs known).
    
    Returns:
        Dict with "status", "entity_def", "count", and "entities" list.
    
    Examples:
        - All open RFIs: query_entities("rfi", conditions_json='[{"path":"Status","type":"EqualTo","value":"Open"}]')
        - Recent contracts sorted: query_entities("contract", sort_by="CreatedDateTime", sort_direction="Descending")
        - Specific fields only: query_entities("punch list", fields="Number,Location,Status,Priority")
        - By ID: query_entities("contract", entity_ids="6209560,6209573")
    """
    ent = resolve_entity_def(entity_def)
    query_url = QUERY_URL_TEMPLATE.format(project_id=project_id)
    
    # Build query payload
    qpayload: Dict[str, Any] = {
        "PropertyName": "Query", 
        "EntityDef": ent,
        "Take": str(limit),
    }
    
    if skip > 0:
        qpayload["Skip"] = str(skip)
    
    # Entity range (query by specific IDs)
    if entity_ids:
        qpayload["EntityRange"] = entity_ids
    
    # Scope for cross-partition queries
    if scope:
        qpayload["Partition"] = {"Scope": scope}
    
    # Conditions/Filters
    if conditions_json:
        try:
            conditions = json.loads(conditions_json)
            kahua_conditions = []
            for cond in conditions:
                if "all_of" in cond:
                    # Multiple conditions with AND
                    children = [
                        {"PropertyName": "Data", "Path": c["path"], "Type": c["type"], "Value": c.get("value", "")}
                        for c in cond["all_of"]
                    ]
                    kahua_conditions.append({"PropertyName": "AllOf", "_children": children})
                elif "any_of" in cond:
                    # Multiple conditions with OR
                    children = [
                        {"PropertyName": "Data", "Path": c["path"], "Type": c["type"], "Value": c.get("value", "")}
                        for c in cond["any_of"]
                    ]
                    kahua_conditions.append({"PropertyName": "AnyOf", "_children": children})
                else:
                    # Single condition
                    kahua_conditions.append({
                        "PropertyName": "Data",
                        "Path": cond["path"],
                        "Type": cond["type"],
                        "Value": cond.get("value", "")
                    })
            if kahua_conditions:
                qpayload["Condition"] = kahua_conditions
        except json.JSONDecodeError as e:
            return {"status": "error", "message": f"Invalid conditions_json: {e}"}
    
    # Sorting
    if sort_by:
        qpayload["Sorts"] = [{
            "PropertyName": "Data",
            "Path": sort_by,
            "Direction": sort_direction or "Ascending"
        }]
    
    # Scalar explicits (specific fields only)
    if fields:
        field_list = [f.strip() for f in fields.split(",") if f.strip()]
        qpayload["ImplicitsDisabled"] = "True"
        qpayload["ScalarExplicits"] = [
            {"PropertyName": "Scalar", "Path": f} for f in field_list
        ]
    
    # Log the actual query for debugging
    log.info(f"Kahua Query: POST {query_url} with payload: {json.dumps(qpayload)}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(query_url, headers=HEADERS_JSON(), json=qpayload)
        ctype = resp.headers.get("content-type", "")
        body = resp.json() if "application/json" in (ctype or "") else {"text": resp.text}
    
    if resp.status_code >= 400:
        return {"status": "error", "upstream_status": resp.status_code, "upstream_body": body, "query_sent": qpayload}
    
    # Extract entities from response
    entities = []
    count = 0
    if isinstance(body, dict):
        count = body.get("count", 0)
        for k in ("entities", "results", "items"):
            if isinstance(body.get(k), list):
                entities = body[k]
                break
    
    return {
        "status": "ok", 
        "entity_def": ent, 
        "project_id": project_id,
        "count": count or len(entities),
        "returned": len(entities),
        "skipped": skip,
        "entities": entities,
        "query_sent": qpayload  # Include actual query for transparency
    }


@function_tool
async def generate_report(
    title: str,
    markdown_content: str,
    subtitle: Optional[str] = None,
    author: Optional[str] = None,
    logo_path: Optional[str] = None,
    charts_json: Optional[str] = None,
    images_json: Optional[str] = None,
    header_color: Optional[str] = None,
    accent_color: Optional[str] = None
) -> dict:
    """
    Generate a professional Word document report with analytics, charts, and photos.
    
    Args:
        title: The main title of the report (required)
        markdown_content: The body content in markdown format. Supports:
            - Headers (# ## ###)
            - Tables (| col1 | col2 |)
            - Lists (- item or 1. item)
            - Bold/italic (**bold** *italic*)
            - Blockquotes (> quote for callouts/notes)
            - Chart placeholders: CHART_0, CHART_1, etc. (in double curly braces)
            - Image placeholders: IMAGE_0, IMAGE_1, etc. (in double curly braces)
              You can add a caption after: IMAGE_0 - Photo of damaged beam
        subtitle: Optional subtitle (e.g., project name, report period)
        author: Optional author name ("Prepared by: X")
        logo_path: Optional path to company logo image file
        charts_json: JSON string array of chart specs. Each chart needs:
            - chart_type: "bar", "horizontal_bar", "line", "pie", "stacked_bar"
            - title: Chart title
            - data: Object with "labels" and "values" arrays
            - y_label: Optional axis label
        images_json: JSON string array of image file paths for photos.
            Order corresponds to IMAGE_0, IMAGE_1, etc. placeholders.
            Example: '["C:/photos/site1.jpg", "C:/photos/damage.png"]'
        header_color: Header background color (hex, default "#1a365d")
        accent_color: Accent color for highlights (hex, default "#3182ce")
    
    Returns:
        Dict with "status", "filename", "download_url", and "message".
    """
    try:
        # Parse charts JSON if provided
        charts = None
        if charts_json:
            try:
                charts = json.loads(charts_json)
            except json.JSONDecodeError as e:
                return {
                    "status": "error",
                    "message": f"Invalid charts_json: {str(e)}"
                }
        
        # Parse images JSON if provided
        images = None
        if images_json:
            try:
                images = json.loads(images_json)
            except json.JSONDecodeError as e:
                return {
                    "status": "error",
                    "message": f"Invalid images_json: {str(e)}"
                }
        
        # Run synchronous report generation in thread pool
        import asyncio
        loop = asyncio.get_event_loop()
        
        def _generate():
            return create_report(
                title=title,
                markdown_content=markdown_content,
                charts=charts,
                images=images,
                logo_path=logo_path,
                subtitle=subtitle,
                author=author,
                header_color=header_color or "#1a365d",
                accent_color=accent_color or "#3182ce"
            )
        
        result = await loop.run_in_executor(None, _generate)
        filename = result["filename"]
        
        # Construct URLs for download/preview
        base_url = os.getenv("REPORT_BASE_URL", "http://localhost:8000")
        download_url = f"{base_url}/reports/{filename}"
        
        return {
            "status": "ok",
            "filename": filename,
            "download_url": download_url,
            "message": f"Your report is ready! Click here to view or download: {download_url}"
        }
    except Exception as e:
        log.exception("Report generation failed")
        return {
            "status": "error",
            "message": f"Failed to generate report: {str(e)}"
        }


class ProjectItem(BaseModel):
    name: str = Field(..., description="Project Name")
    description: Optional[str] = None
    id: Optional[int] = None

SUPER_AGENT_INSTRUCTIONS = """You are an expert Construction Project Analyst for Kahua. You create professional, data-driven reports that help teams make better decisions.

## CORE PRINCIPLE: DISCOVER, DON'T ASSUME

You have access to real data. Never guess what exists—always check first.

## CRITICAL: PROJECT NAME RESOLUTION

**When a user mentions ANY project by name, you MUST call `find_project()` FIRST.**

Examples:
- "Do the NovaScotia project" → `find_project("NovaScotia")` → get ID → then query
- "Check Scotiabank Arena" → `find_project("Scotiabank")` → get ID → then query  
- "What's in Project Alpha?" → `find_project("Alpha")` → get ID → then query

**NEVER assume a project ID.** Project IDs are large numbers like 9610179, not sequential like 1, 2, 3.

### When to Use Each Tool

| User Says | You Do |
|-----------|--------|
| Project by name ("NovaScotia project") | `find_project("NovaScotia")` first |
| "What do I have?" / vague questions | `discover_environment()` |
| "Show me the RFIs" (specific entity) | `query_entities("rfi")` |
| "Pick a random project" | `query_entities("project")` then pick one |

### Discovery-First Workflow

1. **RESOLVE**: If project name mentioned → `find_project()` 
2. **DISCOVER**: What data exists? → `discover_environment(project_id=X)`
3. **FETCH**: Get actual records → `query_entities()`
4. **ANALYZE**: Calculate metrics, find patterns
5. **REPORT**: Generate document → `generate_report()`

## STOP ASKING PERMISSION

You are an expert. Act like one.

**NEVER SAY:**
- ❌ "Would you like me to..."
- ❌ "Should I proceed with..."
- ❌ "I can generate that report. Want me to?"
- ❌ "Let me know if you'd like me to..."

**INSTEAD:**
- ✅ Just do it
- ✅ Present results directly
- ✅ If truly ambiguous (multiple matches), ask ONE clarifying question then proceed

**Example - WRONG:**
> "I found 3 contracts. Would you like me to create a report?"

**Example - RIGHT:**
> "I found 3 contracts totaling $2.4M. Here's the breakdown: [table]. The largest is with ABC Corp at $1.2M. [Download Report](link)"

## TOOLS

### find_project(search_term)
**REQUIRED** when user mentions a project by name. Returns matching project(s) with IDs.

### discover_environment(project_id=0, categories=None)
Scan for what data exists. Use project_id from find_project, or 0 for org-wide.
Categories: "cost", "field", "communications", "documents", "project", "risk"

### get_entity_schema(entity_def, project_id=0)  
Sample a record to see available fields.

### query_entities(entity_def, project_id, limit, skip, conditions_json, sort_by, sort_direction, fields, scope, entity_ids)
**Powerful query tool with filtering, sorting, and field selection.**

Basic usage:
- `query_entities("rfi")` - get all RFIs
- `query_entities("contract", project_id=9610179)` - contracts for specific project

**Filtering (conditions_json):**
```json
// Single condition
'[{"path": "Status", "type": "EqualTo", "value": "Open"}]'

// Multiple conditions (AND)
'[{"all_of": [{"path": "Status", "type": "EqualTo", "value": "Open"}, {"path": "Priority", "type": "EqualTo", "value": "High"}]}]'

// Date filtering
'[{"path": "DueDate", "type": "LessThan", "value": "2026-01-01"}]'
```

Condition types: EqualTo, NotEqualTo, Contains, StartsWith, EndsWith, GreaterThan, LessThan, GreaterThanOrEqualTo, LessThanOrEqualTo, HasValue, HasNoValue, In

**Sorting:**
- `sort_by="CreatedDateTime", sort_direction="Descending"` - newest first
- `sort_by="Number", sort_direction="Ascending"` - by number

**Field selection (reduces payload):**
- `fields="Number,Name,Status,DueDate"` - only return these fields

**Scope:**
- `scope="Any"` - query across all projects in domain

**By ID (fastest):**
- `entity_ids="6209560,6209573"` - get specific records directly

### generate_report(title, markdown_content, ...)
Create professional Word documents with charts and images.

## ENTITY ALIASES

- contract → kahua_Contract.Contract
- rfi → kahua_AEC_RFI.RFI  
- submittal → kahua_AEC_Submittal.SubmittalItem
- punch list → kahua_AEC_PunchList.PunchListItem
- invoice → kahua_AEC_Invoice.Invoice
- change order → kahua_AEC_ChangeOrder.ChangeOrder
- daily report → kahua_AEC_DailyReport.DailyReport
- field observation → kahua_AEC_FieldObservation.FieldObservationItem

Other entities exist—use `discover_environment` to find them.

## REPORT GENERATION

### Markdown Format
- Headers: # ## ###
- Tables: | Col1 | Col2 |
- Charts: {{CHART_0}}, {{CHART_1}} (provide charts_json)
- Images: {{IMAGE_0}}, {{IMAGE_1}} (provide images_json)

### Always Include
1. Executive Summary (2-3 sentences)
2. Data Tables
3. Charts (when meaningful)
4. Recommendations

## CONSTRUCTION EXPERTISE

Apply domain knowledge:
- **RFIs**: Response times, open/closed, by discipline
- **Submittals**: Approval rates, review cycles
- **Punch Lists**: Closure progress, by location/trade
- **Contracts**: Commitment values, change order impact

### Risk Indicators
- High open RFI count → coordination risk
- Slow RFI response → schedule impact
- Change order growth → budget risk
- Low punch list closure → delay risk

## REMEMBER

1. **Project names → find_project() FIRST** - never guess IDs
2. **Never fabricate data** - only report what you queried
3. **Act immediately** - don't ask permission
4. **Use conversation context** - don't re-query existing data
5. **Provide insights** - explain what the data means
"""

super_agent = Agent(
    name="Kahua Construction Analyst",
    handoff_description="Expert construction project analyst specializing in data-driven reports, analytics, and professional documentation.",
    model=OpenAIChatCompletionsModel(model='gpt-5-chat', openai_client=azure_client),
    instructions=SUPER_AGENT_INSTRUCTIONS,
    tools=[find_project, discover_environment, get_entity_schema, query_entities, generate_report],
)

def get_super_agent() -> Agent:
    return super_agent


