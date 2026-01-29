import os, json, logging, asyncio
from pathlib import Path
from typing import Optional, List, Any, Dict
import httpx
from pydantic import BaseModel, Field, ValidationError

# Report generation
from report_generator import create_report, ReportGenerator, ReportConfig, ChartSpec

try:
    from agents import Agent, Runner, function_tool, SQLiteSession
except Exception as e:
    raise RuntimeError("The 'agents' package must be importable for this script to run.") from e

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("kahua_superagent")

# Model configuration - supports both OpenAI and Anthropic on Azure
MODEL_DEPLOYMENT = os.environ.get("AZURE_DEPLOYMENT", "gpt-4o")
MODEL_PROVIDER = os.environ.get("MODEL_PROVIDER", "anthropic").lower()  # "openai" or "anthropic"

if MODEL_PROVIDER == "anthropic":
    # Use Anthropic Claude via Azure
    from anthropic_model_adapter import AnthropicChatCompletionsModel, create_azure_anthropic_client
    anthropic_client = create_azure_anthropic_client()
    model_instance = AnthropicChatCompletionsModel(model=MODEL_DEPLOYMENT, anthropic_client=anthropic_client)
    log.info(f"Using Anthropic model: {MODEL_DEPLOYMENT}")
else:
    # Use OpenAI via Azure
    from openai import AsyncAzureOpenAI
    from agents import OpenAIChatCompletionsModel
    azure_client = AsyncAzureOpenAI(
        api_key=os.environ["AZURE_KEY"],
        azure_endpoint=os.environ["AZURE_ENDPOINT"],
        api_version=os.environ["API_VERSION"],
    )
    model_instance = OpenAIChatCompletionsModel(model=MODEL_DEPLOYMENT, openai_client=azure_client)
    log.info(f"Using OpenAI model: {MODEL_DEPLOYMENT}")

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
    # Projects
    "project": "kahua_Project.Project",
    "projects": "kahua_Project.Project",
    # RFIs - all variations
    "rfi": "kahua_AEC_RFI.RFI",
    "rfis": "kahua_AEC_RFI.RFI",
    "request for information": "kahua_AEC_RFI.RFI",
    "requests for information": "kahua_AEC_RFI.RFI",
    # Submittals
    "submittal": "kahua_AEC_Submittal.Submittal",
    "submittals": "kahua_AEC_Submittal.Submittal",
    "submittal item": "kahua_AEC_Submittal.SubmittalItem",
    "submittal items": "kahua_AEC_Submittal.SubmittalItem",
    "submittal package": "kahua_AEC_SubmittalPackage.SubmittalPackage",
    # Change Orders
    "change order": "kahua_AEC_ChangeOrder.ChangeOrder",
    "change orders": "kahua_AEC_ChangeOrder.ChangeOrder",
    "co": "kahua_AEC_ChangeOrder.ChangeOrder",
    # Punch Lists
    "punchlist": "kahua_AEC_PunchList.PunchListItem",
    "punch list": "kahua_AEC_PunchList.PunchListItem",
    "punchlist item": "kahua_AEC_PunchList.PunchListItem",
    "punch list item": "kahua_AEC_PunchList.PunchListItem",
    "punch": "kahua_AEC_PunchList.PunchListItem",
    # Field Observations
    "field observation": "kahua_AEC_FieldObservation.FieldObservationItem",
    "field observations": "kahua_AEC_FieldObservation.FieldObservationItem",
    "observation": "kahua_AEC_FieldObservation.FieldObservationItem",
    # Contracts
    "contract": "kahua_Contract.Contract",
    "contracts": "kahua_Contract.Contract",
    "contract item": "kahua_Contract.ContractItem",
    "contract items": "kahua_Contract.ContractItem",
    # Invoices
    "invoice": "kahua_ContractInvoice.ContractInvoice",
    "invoices": "kahua_ContractInvoice.ContractInvoice",
    # Daily Reports
    "daily report": "kahua_AEC_DailyReport.DailyReport",
    "daily reports": "kahua_AEC_DailyReport.DailyReport",
    "daily": "kahua_AEC_DailyReport.DailyReport",
    # Meetings
    "meeting": "kahua_Meeting.Meeting",
    "meetings": "kahua_Meeting.Meeting",
    "action item": "kahua_Meeting.ActionItem",
    "action items": "kahua_Meeting.ActionItem",
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

# Tools: Query / Report Generation

@function_tool
async def count_entities(entity_def: str, project_id: int = 0, scope: Optional[str] = "Any") -> dict:
    """
    FAST count of a single entity type. Use this for simple "how many X?" questions.
    
    - "How many projects do I have?" -> count_entities("project")
    - "How many RFIs?" -> count_entities("rfi")
    - "How many contracts?" -> count_entities("contract")
    
    Args:
        entity_def: Entity type - alias ("project", "rfi", "contract") or full name.
        project_id: Project context. Use 0 for domain-wide (default).
        scope: "Any" for all records across projects (default), "DomainPartition" for specific project.
    
    Returns:
        Dict with count and entity info.
    """
    ent = resolve_entity_def(entity_def)
    query_url = QUERY_URL_TEMPLATE.format(project_id=project_id)
    qpayload: Dict[str, Any] = {
        "PropertyName": "Query",
        "EntityDef": ent,
        "Take": "1"  # Only need count, not data
    }
    if scope:
        qpayload["Partition"] = {"Scope": scope}
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(query_url, headers=HEADERS_JSON(), json=qpayload)
        if resp.status_code >= 400:
            return {"status": "error", "message": f"Failed to query {ent}", "code": resp.status_code}
        body = resp.json()
    
    count = body.get("count", 0)
    if count == 0 and isinstance(body, dict):
        for key in ("entities", "results", "items"):
            if isinstance(body.get(key), list):
                # If we got a list, the count header might have the real total
                count = body.get("count", len(body[key]))
                break
        for s in body.get("sets", []):
            if isinstance(s.get("entities"), list):
                count = max(count, body.get("count", len(s["entities"])))
    
    return {
        "status": "ok",
        "entity_def": ent,
        "count": count,
        "project_id": project_id,
        "scope": scope
    }


@function_tool
async def list_available_apps() -> dict:
    """
    Instantly list what Kahua apps/entities the agent can work with. NO API CALLS - immediate response.
    
    Use this when the user asks:
    - "What can you do?" / "What can you report on?"
    - "What apps do you support?"
    - "What data can you access?"
    
    Returns categories and entity types the agent knows how to query.
    To get actual counts, use count_entities() for specific types.
    """
    # Build a user-friendly summary from ENTITY_CATEGORIES
    apps = {
        "cost": {
            "description": "Financial & cost management",
            "entities": ["Contracts", "Contract Items", "Change Orders", "Invoices", "Purchase Orders", "Budgets", "Client Contracts"]
        },
        "field": {
            "description": "Field operations & coordination", 
            "entities": ["RFIs", "Submittals", "Submittal Packages", "Punch Lists", "Field Observations", "Daily Reports"]
        },
        "communications": {
            "description": "Project communications",
            "entities": ["Messages", "Transmittals", "Memos", "Letters", "Meetings", "Action Items"]
        },
        "documents": {
            "description": "Document management",
            "entities": ["Files", "Drawing Logs", "Design Review Sets", "Design Review Comments"]
        },
        "project": {
            "description": "Project & directory info",
            "entities": ["Projects", "Locations", "Companies", "Contacts"]
        },
        "risk": {
            "description": "Risk & compliance",
            "entities": ["Issues", "Risk Register", "Compliance Tracking"]
        }
    }
    
    return {
        "status": "ok",
        "message": "Here's what I can access. Ask about specific items to get counts or data.",
        "categories": apps,
        "tip": "Try: 'How many RFIs do I have?' or 'Show me open punch list items'"
    }


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
        entity_def: The entity type to inspect (e.g., "kahua_Contract.Contract" or alias like "rfi")
        project_id: Project context. Use 0 for root (default).
    
    Returns:
        Dict with field names, sample values, and data types.
    """
    ent = resolve_entity_def(entity_def)
    query_url = QUERY_URL_TEMPLATE.format(project_id=project_id)
    
    async def try_query(scope: str = None) -> tuple:
        """Execute query with optional scope, return (body, sample)."""
        qpayload = {"PropertyName": "Query", "EntityDef": ent, "Take": "1"}
        if scope:
            qpayload["Partition"] = {"Scope": scope}
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(query_url, headers=HEADERS_JSON(), json=qpayload)
            if resp.status_code >= 400:
                return None, None
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
        return body, sample
    
    # Default to scope="Any" when querying from root (project_id=0) to search all partitions
    default_scope = "Any" if project_id == 0 else None
    body, sample = await try_query(scope=default_scope)
    
    if body is None:
        return {"status": "error", "message": f"Failed to query {ent}"}
    
    if not sample:
        return {"status": "ok", "entity_def": ent, "fields": [], "message": "No records found to sample schema (tried default and 'Any' scope)"}
    
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
        "fields": sorted(fields, key=lambda x: x["name"]),
        "message": f"Sampled schema from {ent}"
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
    
    # CRITICAL FIX: If querying from root (project_id=0), default to Any scope for cross-partition results
    # Without this, queries only search the root partition which may have 0 or few records
    if project_id == 0 and not scope:
        scope = "Any"
        log.info(f"Auto-setting scope='Any' for domain-wide query (project_id=0)")
    
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


# Template-aware report generation
from templates import get_template_store

@function_tool
async def list_report_templates(category: Optional[str] = None, search: Optional[str] = None) -> dict:
    """
    List available report templates that can be used to generate consistent, repeatable reports.
    
    Args:
        category: Optional filter by category. Options: "cost", "field", "executive", "custom"
        search: Optional search term to filter templates by name or description
    
    Returns:
        Dict with list of templates including their IDs, names, descriptions, and categories.
    """
    try:
        store = get_template_store()
        templates = store.list_templates(category=category, search=search)
        
        return {
            "status": "ok",
            "count": len(templates),
            "templates": [
                {
                    "id": t.id,
                    "name": t.name,
                    "description": t.description,
                    "category": t.category,
                    "tags": t.tags,
                    "sections": [{"title": s.title, "type": s.section_type} for s in t.sections]
                }
                for t in templates
            ]
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@function_tool
async def generate_report_from_template(
    template_id: str,
    project_id: int = 0,
    project_name: Optional[str] = None,
    custom_title: Optional[str] = None,
    date_range_start: Optional[str] = None,
    date_range_end: Optional[str] = None,
    additional_filters_json: Optional[str] = None
) -> dict:
    """
    Generate a report using a saved template. Templates provide consistent structure and formatting.
    
    Args:
        template_id: The ID of the template to use (get from list_report_templates)
        project_id: Project ID to pull data from. Use 0 for org-wide.
        project_name: Project name to include in title (optional)
        custom_title: Override the template's title (optional)
        date_range_start: Filter data from this date (YYYY-MM-DD format)
        date_range_end: Filter data to this date (YYYY-MM-DD format)
        additional_filters_json: Extra conditions as JSON string
    
    Returns:
        Dict with report download URL and metadata.
    """
    try:
        from datetime import datetime
        
        store = get_template_store()
        template = store.get_template(template_id)
        
        if not template:
            return {"status": "error", "message": f"Template '{template_id}' not found"}
        
        # Build title from template
        title = custom_title or template.title_template
        if project_name:
            title = title.replace("{project_name}", project_name)
        title = title.replace("{date}", datetime.now().strftime("%B %d, %Y"))
        
        subtitle = template.subtitle_template
        if subtitle:
            subtitle = subtitle.replace("{date}", datetime.now().strftime("%B %d, %Y"))
            if project_name:
                subtitle = subtitle.replace("{project_name}", project_name)
        
        # Build markdown content from sections
        markdown_parts = []
        charts = []
        chart_idx = 0
        
        for section in sorted(template.sections, key=lambda s: s.order):
            if section.section_type == "summary":
                markdown_parts.append(f"## {section.title}\n\n{section.content or 'Summary of key findings.'}\n")
            
            elif section.section_type == "text":
                markdown_parts.append(f"## {section.title}\n\n{section.content or ''}\n")
            
            elif section.section_type == "metrics":
                markdown_parts.append(f"## {section.title}\n\n{section.content or 'Key metrics displayed here.'}\n")
            
            elif section.section_type == "table" and section.entity_def:
                # Query data for this section
                ent = resolve_entity_def(section.entity_def)
                conditions = []
                if section.conditions:
                    conditions.extend(section.conditions)
                if additional_filters_json:
                    try:
                        conditions.extend(json.loads(additional_filters_json))
                    except:
                        pass
                
                # Date range filters
                if date_range_start:
                    conditions.append({"path": "CreatedDateTime", "type": "GreaterThanOrEqualTo", "value": date_range_start})
                if date_range_end:
                    conditions.append({"path": "CreatedDateTime", "type": "LessThanOrEqualTo", "value": date_range_end})
                
                query_url = QUERY_URL_TEMPLATE.format(project_id=project_id)
                qpayload: Dict[str, Any] = {"PropertyName": "Query", "EntityDef": ent, "Take": "100"}
                
                # CRITICAL: Add partition scope for domain-wide queries
                if project_id == 0:
                    qpayload["Partition"] = {"Scope": "Any"}
                
                if conditions:
                    qpayload["Condition"] = [
                        {"PropertyName": "Data", "Path": c["path"], "Type": c["type"], "Value": c.get("value", "")}
                        for c in conditions
                    ]
                
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.post(query_url, headers=HEADERS_JSON(), json=qpayload)
                    body = resp.json() if resp.status_code < 400 else {}
                
                # Extract entities - handle multiple response formats
                entities = []
                for key in ("entities", "results", "items"):
                    if isinstance(body.get(key), list):
                        entities = body[key]
                        break
                # Also check nested sets structure (Kahua API format)
                if not entities and "sets" in body:
                    for s in body.get("sets", []):
                        if isinstance(s.get("entities"), list):
                            entities = s["entities"]
                            break
                
                if entities:
                    fields = section.fields or list(entities[0].keys())[:6]
                    # Build markdown table
                    header = "| " + " | ".join(fields) + " |"
                    separator = "| " + " | ".join(["---"] * len(fields)) + " |"
                    rows = []
                    for ent in entities[:50]:  # Limit rows
                        row = "| " + " | ".join(str(ent.get(f, ""))[:40] for f in fields) + " |"
                        rows.append(row)
                    
                    markdown_parts.append(f"## {section.title}\n\n{header}\n{separator}\n" + "\n".join(rows) + "\n")
                else:
                    markdown_parts.append(f"## {section.title}\n\n*No data found for this section.*\n")
            
            elif section.section_type == "chart" and section.chart:
                chart_spec = section.chart
                # Query and aggregate data for chart
                ent = resolve_entity_def(chart_spec.data_source)
                
                query_url = QUERY_URL_TEMPLATE.format(project_id=project_id)
                qpayload: Dict[str, Any] = {"PropertyName": "Query", "EntityDef": ent, "Take": "500"}
                
                # CRITICAL: Add partition scope for domain-wide queries
                if project_id == 0:
                    qpayload["Partition"] = {"Scope": "Any"}
                
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.post(query_url, headers=HEADERS_JSON(), json=qpayload)
                    body = resp.json() if resp.status_code < 400 else {}
                
                # Extract entities - handle multiple response formats
                entities = []
                for key in ("entities", "results", "items"):
                    if isinstance(body.get(key), list):
                        entities = body[key]
                        break
                # Also check nested sets structure (Kahua API format)
                if not entities and "sets" in body:
                    for s in body.get("sets", []):
                        if isinstance(s.get("entities"), list):
                            entities = s["entities"]
                            break
                
                if entities:
                    # Aggregate by group_by field
                    counts = {}
                    for ent_item in entities:
                        group_val = str(ent_item.get(chart_spec.group_by, "Unknown") or "Unknown")
                        if chart_spec.aggregation == "count":
                            counts[group_val] = counts.get(group_val, 0) + 1
                        elif chart_spec.aggregation == "sum" and chart_spec.value_field:
                            val = ent_item.get(chart_spec.value_field, 0)
                            try:
                                val = float(val) if val else 0
                            except:
                                val = 0
                            counts[group_val] = counts.get(group_val, 0) + val
                    
                    labels = list(counts.keys())
                    values = list(counts.values())
                    
                    charts.append({
                        "chart_type": chart_spec.chart_type,
                        "title": chart_spec.title,
                        "data": {"labels": labels, "values": values}
                    })
                    
                    markdown_parts.append(f"## {section.title}\n\n{{{{CHART_{chart_idx}}}}}\n")
                    chart_idx += 1
                else:
                    markdown_parts.append(f"## {section.title}\n\n*No data available for chart.*\n")
        
        markdown_content = "\n".join(markdown_parts)
        
        # Generate the report
        import asyncio
        loop = asyncio.get_event_loop()
        
        def _generate():
            return create_report(
                title=title,
                markdown_content=markdown_content,
                charts=charts if charts else None,
                subtitle=subtitle,
                header_color=template.header_color,
                accent_color=template.accent_color
            )
        
        result = await loop.run_in_executor(None, _generate)
        filename = result["filename"]
        
        base_url = os.getenv("REPORT_BASE_URL", "http://localhost:8000")
        download_url = f"{base_url}/reports/{filename}"
        
        return {
            "status": "ok",
            "template_used": template.name,
            "filename": filename,
            "download_url": download_url,
            "sections_generated": len(template.sections),
            "charts_generated": len(charts),
            "message": f"Report generated using '{template.name}' template. [Download Report]({download_url})"
        }
        
    except Exception as e:
        log.exception("Template report generation failed")
        return {"status": "error", "message": f"Failed to generate report: {str(e)}"}


class ProjectItem(BaseModel):
    name: str = Field(..., description="Project Name")
    description: Optional[str] = None
    id: Optional[int] = None

SUPER_AGENT_INSTRUCTIONS = """
You are an expert Construction Project Analyst for Kahua. You create professional, data-driven reports that help teams make better decisions.
  
## CORE PRINCIPLE: DISCOVER, DON'T ASSUME

You have access to real data. Never guess what exists—always check first.

## VERIFICATION RULES - NEVER REPORT WRONG DATA

**Before reporting "0 records" or "no data found":**
1. Include the query_sent in your response so user can verify what was actually queried
2. NEVER report 0 as a final answer for common entities (RFI, Contract, Submittal, PunchList) without trying scope="Any"

**Zero-result sanity check:**
If any query returns 0 for a common entity type in what appears to be an active environment, this is likely a scope issue. 
Before reporting to user:
1. Retry with scope="Any" 
2. If still 0, explicitly state: "I found 0 records using this query: [show query]. This may indicate the data is stored under a different entity definition or project partition."

**Response patterns for zero results:**
- ❌ WRONG: "There are no RFIs in your environment."
- ✅ RIGHT: "My initial query returned 0 RFIs. Let me verify with a broader search..." [then run verification]
- ✅ RIGHT: "I found 0 RFIs matching that criteria. Query used: [show query]. Would you like me to check with different parameters?"

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
| "What can you do?" / "What apps?" | `list_available_apps()` |
| "How many X?" (count question) | `count_entities("rfi")` |
| "Show me the RFIs" (specific entity) | `query_entities("rfi")` |
| "Pick a random project" | `query_entities("project")` then pick one |

### Workflow

1. **RESOLVE**: If project name mentioned → `find_project()` 
2. **FETCH**: Get actual records → `query_entities()` or `count_entities()`
3. **ANALYZE**: Calculate metrics, find patterns
4. **REPORT**: Generate document → `generate_report()`

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

### list_available_apps() ⚡ INSTANT
**Use when user asks "What can you do?" or "What apps do you support?"**
Returns categories and entity types - no API calls needed.

### count_entities(entity_def, project_id=0, scope="Any") ⚡ FAST
**USE THIS for simple count questions** - single API call!
- "How many projects?" → `count_entities("project")`
- "How many RFIs?" → `count_entities("rfi")`
- "Count of contracts" → `count_entities("contract")`

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

Other entities exist—use `list_available_apps()` to see all supported types.

## FILE & IMAGE HANDLING

### Browse Kahua Files
Use `browse_kahua_files()` to explore documents and images stored in Kahua:
- `browse_kahua_files(file_type="image")` - Find photos and images
- `browse_kahua_files(search="foundation")` - Search by filename
- `download_kahua_file(file_id)` - Download for use in reports

### User Uploads
When users want to include their own files:
- `upload_local_file(path)` - Register a local file for use in templates
- Users can also upload via the web UI at `/upload`

### Using Images in Reports
Images can be embedded in portable view templates via the IMAGE section type.
Downloaded/uploaded files are stored locally and can be referenced by path.

## REPORT GENERATION

### Three Approaches

**1. Markdown Portable Views (PREFERRED - Preview First!)**
For single-entity reports (one contract, one RFI, etc.):

1. Use `list_md_templates()` to see available `.md` templates
2. **ALWAYS** call `preview_md_portable_view()` first - this returns rendered markdown
3. **DISPLAY** the markdown preview in chat and ask user: "Does this look good?"
4. **ONLY AFTER** user approval, call `finalize_md_portable_view()` to create the DOCX

This ensures users see exactly what they'll get before downloading.

**2. JSON-based Portable View Templates (For complex layouts)**
Use `list_portable_templates()` to see available templates, then `render_portable_template()`.
These templates can be:
- Created from uploaded examples (PDF, images) with `create_template_from_image()`
- Generated from descriptions with `create_template_from_description()`
- Refined iteratively with `refine_portable_template()`
- Quickly built with `create_quick_template()`

**3. Custom Reports (Ad-hoc multi-entity reports)**
Use `generate_report()` with custom markdown content for reports spanning multiple entities.

### CRITICAL: Portable View Workflow

When user asks for a "portable view" or "portable" for a single entity:

```
1. Query the entity data
2. preview_md_portable_view(template_id, entity_data_json)
   → Returns rendered markdown
3. DISPLAY the markdown in chat
4. ASK: "Here's a preview. Does this look good, or would you like changes?"
5. WAIT for user approval
6. finalize_md_portable_view(preview_id)
   → Returns download URL
```

**DO NOT** skip the preview step. Users must see what they're getting.

Built-in templates:
- **RFI Status Report** (field) - Status breakdown, response times, discipline analysis
- **Contract Summary Report** (cost) - Financial overview, vendor breakdown, change orders
- **Punch List Closeout Report** (field) - Completion progress by location/trade
- **Executive Project Summary** (executive) - High-level KPIs and dashboard

**3. Custom Reports (Ad-hoc)**
Use `generate_report()` with custom markdown content for one-off reports.

### Markdown Format (for custom reports)
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
4. **Use templates when available** - for consistent, professional reports
5. **Use conversation context** - don't re-query existing data
6. **Provide insights** - explain what the data means

## OUTPUT FORMATTING BEST PRACTICES

### Make Data Scannable
- Lead with the **key number** or insight
- Use markdown tables for lists >3 items
- Bold important values: **$2.4M**, **15 open**, **3 days overdue**
- Include status indicators: ✅ Complete, ⚠️ At Risk, ❌ Blocked

### Structured Responses
For queries returning data:
1. **Summary line** - "Found 12 RFIs across 3 projects"
2. **Key metrics** - highlight the most important numbers
3. **Data table** - sortable columns with status
4. **Insight/recommendation** - what should they do next?

Example format:
```
## RFI Status Overview

Found **12 RFIs** - 8 open, 4 closed

| # | Subject | Status | Days Open | Ball In Court |
|---|---------|--------|-----------|---------------|
| 001 | Foundation spec | ⚠️ Pending | **14** | Architect |
| 002 | Steel grade | ✅ Closed | 3 | - |

**⚡ Action needed:** RFI-001 is 14 days old with no response. Consider escalation.
```

### Status Icons
- ✅ Complete/Approved/Closed
- ⚠️ Warning/Pending/At Risk  
- ❌ Rejected/Blocked/Overdue
- 🔄 In Progress/Under Review
- ⏱️ Waiting/On Hold
"""

# Import portable template tools
try:
    from pv_template_tools import PV_TEMPLATE_TOOLS
    pv_tools_available = True
except ImportError:
    PV_TEMPLATE_TOOLS = []
    pv_tools_available = False
    log.warning("Portable View template tools not available")

# Combine all tools
all_tools = [find_project, count_entities, get_entity_schema, query_entities, generate_report, list_report_templates, generate_report_from_template]
if pv_tools_available:
    all_tools.extend(PV_TEMPLATE_TOOLS)

super_agent = Agent(
    name="Kahua Construction Analyst",
    handoff_description="Expert construction project analyst specializing in data-driven reports, analytics, and professional documentation.",
    model=model_instance,
    instructions=SUPER_AGENT_INSTRUCTIONS,
    tools=all_tools,
)

def get_super_agent() -> Agent:
    return super_agent
