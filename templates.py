"""
Report Template Storage System
Manages reusable, customizable report templates for consistent report generation.
"""

import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict, field
from contextlib import contextmanager

# Database location
DB_PATH = Path(__file__).parent / "templates.db"


@dataclass
class ChartTemplate:
    """Template for a chart within a report."""
    chart_type: str  # "bar", "horizontal_bar", "line", "pie", "stacked_bar"
    title: str
    data_source: str  # Query description or entity def (e.g., "rfi", "contract")
    group_by: str  # Field to group by (e.g., "Status", "AssignedTo")
    value_field: Optional[str] = None  # Field to aggregate (count if None)
    aggregation: str = "count"  # "count", "sum", "avg"
    colors: Optional[List[str]] = None
    conditions: Optional[List[Dict[str, Any]]] = None  # Pre-filters
    

@dataclass
class SectionTemplate:
    """Template for a section within a report."""
    title: str
    section_type: str  # "summary", "table", "chart", "metrics", "text"
    content: Optional[str] = None  # Markdown content or query description
    entity_def: Optional[str] = None  # For data sections
    fields: Optional[List[str]] = None  # Fields to include in tables
    conditions: Optional[List[Dict[str, Any]]] = None  # Filters
    chart: Optional[ChartTemplate] = None  # For chart sections
    order: int = 0


@dataclass  
class ReportTemplate:
    """Complete report template definition."""
    id: str
    name: str
    description: str
    category: str  # "cost", "field", "executive", "custom"
    created_at: str
    updated_at: str
    created_by: Optional[str] = None
    
    # Report structure
    title_template: str = ""  # Can include {project_name}, {date}, etc.
    subtitle_template: Optional[str] = None
    
    # Sections define the report structure
    sections: List[SectionTemplate] = field(default_factory=list)
    
    # Default parameters user can override
    default_params: Dict[str, Any] = field(default_factory=dict)
    
    # Styling
    header_color: str = "#1a365d"
    accent_color: str = "#3182ce"
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    is_public: bool = False  # Shared with organization
    version: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        d = asdict(self)
        return d
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReportTemplate":
        """Create from dictionary."""
        # Reconstruct nested objects
        sections = []
        for s in data.get("sections", []):
            chart = None
            if s.get("chart"):
                chart = ChartTemplate(**s["chart"])
            sections.append(SectionTemplate(
                title=s["title"],
                section_type=s["section_type"],
                content=s.get("content"),
                entity_def=s.get("entity_def"),
                fields=s.get("fields"),
                conditions=s.get("conditions"),
                chart=chart,
                order=s.get("order", 0)
            ))
        
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            category=data["category"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            created_by=data.get("created_by"),
            title_template=data.get("title_template", ""),
            subtitle_template=data.get("subtitle_template"),
            sections=sections,
            default_params=data.get("default_params", {}),
            header_color=data.get("header_color", "#1a365d"),
            accent_color=data.get("accent_color", "#3182ce"),
            tags=data.get("tags", []),
            is_public=data.get("is_public", False),
            version=data.get("version", 1)
        )


class TemplateStore:
    """SQLite-based template storage with full CRUD operations."""
    
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DB_PATH
        self._init_db()
    
    @contextmanager
    def _get_conn(self):
        """Get database connection with context manager."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()
    
    def _init_db(self):
        """Initialize database schema."""
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS templates (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    category TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    created_by TEXT,
                    data JSON NOT NULL,
                    is_public INTEGER DEFAULT 0,
                    version INTEGER DEFAULT 1
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_templates_category ON templates(category)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_templates_public ON templates(is_public)
            """)
            
            # Saved queries table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS saved_queries (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    query_text TEXT NOT NULL,
                    entity_def TEXT,
                    conditions JSON,
                    created_at TEXT NOT NULL,
                    created_by TEXT,
                    use_count INTEGER DEFAULT 0
                )
            """)
    
    # Template CRUD operations
    
    def create_template(self, template: ReportTemplate) -> ReportTemplate:
        """Create a new template."""
        now = datetime.utcnow().isoformat()
        if not template.id:
            template.id = str(uuid.uuid4())
        template.created_at = now
        template.updated_at = now
        
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO templates (id, name, description, category, created_at, updated_at, created_by, data, is_public, version)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                template.id, template.name, template.description, template.category,
                template.created_at, template.updated_at, template.created_by,
                json.dumps(template.to_dict()), 1 if template.is_public else 0, template.version
            ))
        return template
    
    def get_template(self, template_id: str) -> Optional[ReportTemplate]:
        """Get a template by ID."""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT data FROM templates WHERE id = ?", (template_id,)
            ).fetchone()
            if row:
                return ReportTemplate.from_dict(json.loads(row["data"]))
        return None
    
    def update_template(self, template: ReportTemplate) -> ReportTemplate:
        """Update an existing template."""
        template.updated_at = datetime.utcnow().isoformat()
        template.version += 1
        
        with self._get_conn() as conn:
            conn.execute("""
                UPDATE templates 
                SET name = ?, description = ?, category = ?, updated_at = ?, 
                    data = ?, is_public = ?, version = ?
                WHERE id = ?
            """, (
                template.name, template.description, template.category,
                template.updated_at, json.dumps(template.to_dict()),
                1 if template.is_public else 0, template.version, template.id
            ))
        return template
    
    def delete_template(self, template_id: str) -> bool:
        """Delete a template."""
        with self._get_conn() as conn:
            cursor = conn.execute("DELETE FROM templates WHERE id = ?", (template_id,))
            return cursor.rowcount > 0
    
    def list_templates(
        self, 
        category: Optional[str] = None,
        search: Optional[str] = None,
        include_public: bool = True
    ) -> List[ReportTemplate]:
        """List templates with optional filtering."""
        query = "SELECT data FROM templates WHERE 1=1"
        params = []
        
        if category:
            query += " AND category = ?"
            params.append(category)
        
        if search:
            query += " AND (name LIKE ? OR description LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%"])
        
        if not include_public:
            query += " AND is_public = 0"
        
        query += " ORDER BY updated_at DESC"
        
        with self._get_conn() as conn:
            rows = conn.execute(query, params).fetchall()
            return [ReportTemplate.from_dict(json.loads(r["data"])) for r in rows]
    
    # Saved queries
    
    def save_query(
        self, 
        name: str, 
        query_text: str,
        description: Optional[str] = None,
        entity_def: Optional[str] = None,
        conditions: Optional[List[Dict]] = None,
        created_by: Optional[str] = None
    ) -> str:
        """Save a query for quick reuse."""
        query_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO saved_queries (id, name, description, query_text, entity_def, conditions, created_at, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                query_id, name, description, query_text, entity_def,
                json.dumps(conditions) if conditions else None, now, created_by
            ))
        return query_id
    
    def get_saved_queries(self, search: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all saved queries."""
        query = "SELECT * FROM saved_queries"
        params = []
        
        if search:
            query += " WHERE name LIKE ? OR description LIKE ?"
            params.extend([f"%{search}%", f"%{search}%"])
        
        query += " ORDER BY use_count DESC, created_at DESC"
        
        with self._get_conn() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]
    
    def increment_query_usage(self, query_id: str):
        """Track query usage for popularity sorting."""
        with self._get_conn() as conn:
            conn.execute(
                "UPDATE saved_queries SET use_count = use_count + 1 WHERE id = ?",
                (query_id,)
            )
    
    def delete_saved_query(self, query_id: str) -> bool:
        """Delete a saved query."""
        with self._get_conn() as conn:
            cursor = conn.execute("DELETE FROM saved_queries WHERE id = ?", (query_id,))
            return cursor.rowcount > 0


# Pre-built templates for common construction reports
def get_builtin_templates() -> List[ReportTemplate]:
    """Return built-in starter templates."""
    now = datetime.utcnow().isoformat()
    
    return [
        ReportTemplate(
            id="builtin-rfi-status",
            name="RFI Status Report",
            description="Comprehensive RFI analysis with status breakdown, response times, and discipline distribution.",
            category="field",
            created_at=now,
            updated_at=now,
            title_template="{project_name} - RFI Status Report",
            subtitle_template="Generated {date}",
            sections=[
                SectionTemplate(
                    title="Executive Summary",
                    section_type="summary",
                    content="Overview of RFI performance and key metrics.",
                    order=0
                ),
                SectionTemplate(
                    title="Status Distribution",
                    section_type="chart",
                    entity_def="rfi",
                    chart=ChartTemplate(
                        chart_type="pie",
                        title="RFIs by Status",
                        data_source="rfi",
                        group_by="Status"
                    ),
                    order=1
                ),
                SectionTemplate(
                    title="RFI Log",
                    section_type="table",
                    entity_def="rfi",
                    fields=["Number", "Subject", "Status", "AssignedTo", "DueDate", "DaysOpen"],
                    order=2
                ),
                SectionTemplate(
                    title="Response Time Analysis",
                    section_type="chart",
                    entity_def="rfi",
                    chart=ChartTemplate(
                        chart_type="horizontal_bar",
                        title="Average Response Time by Discipline",
                        data_source="rfi",
                        group_by="Discipline",
                        value_field="ResponseDays",
                        aggregation="avg"
                    ),
                    order=3
                )
            ],
            tags=["rfi", "field", "status"],
            is_public=True
        ),
        
        ReportTemplate(
            id="builtin-contract-summary",
            name="Contract Summary Report",
            description="Financial overview of contracts, commitments, and change order impact.",
            category="cost",
            created_at=now,
            updated_at=now,
            title_template="{project_name} - Contract Summary",
            subtitle_template="As of {date}",
            sections=[
                SectionTemplate(
                    title="Financial Overview",
                    section_type="metrics",
                    content="Key financial metrics and totals.",
                    order=0
                ),
                SectionTemplate(
                    title="Commitment by Vendor",
                    section_type="chart",
                    entity_def="contract",
                    chart=ChartTemplate(
                        chart_type="horizontal_bar",
                        title="Contract Values by Vendor",
                        data_source="contract",
                        group_by="VendorName",
                        value_field="ContractValue",
                        aggregation="sum"
                    ),
                    order=1
                ),
                SectionTemplate(
                    title="Contract Register",
                    section_type="table",
                    entity_def="contract",
                    fields=["Number", "Name", "VendorName", "OriginalValue", "ChangeOrders", "CurrentValue", "Status"],
                    order=2
                ),
                SectionTemplate(
                    title="Change Order Trend",
                    section_type="chart",
                    entity_def="contract",
                    chart=ChartTemplate(
                        chart_type="line",
                        title="Cumulative Change Orders Over Time",
                        data_source="change_order",
                        group_by="Month",
                        value_field="Amount",
                        aggregation="sum"
                    ),
                    order=3
                )
            ],
            tags=["contract", "cost", "financial"],
            is_public=True
        ),
        
        ReportTemplate(
            id="builtin-punch-list",
            name="Punch List Closeout Report",
            description="Track punch list completion progress by location, trade, and priority.",
            category="field",
            created_at=now,
            updated_at=now,
            title_template="{project_name} - Punch List Report",
            subtitle_template="Closeout Status as of {date}",
            sections=[
                SectionTemplate(
                    title="Completion Summary",
                    section_type="metrics",
                    content="Overall punch list completion percentage and counts.",
                    order=0
                ),
                SectionTemplate(
                    title="Status Overview",
                    section_type="chart",
                    entity_def="punch list",
                    chart=ChartTemplate(
                        chart_type="pie",
                        title="Punch List Items by Status",
                        data_source="punch list",
                        group_by="Status"
                    ),
                    order=1
                ),
                SectionTemplate(
                    title="By Location",
                    section_type="chart",
                    entity_def="punch list",
                    chart=ChartTemplate(
                        chart_type="horizontal_bar",
                        title="Open Items by Location",
                        data_source="punch list",
                        group_by="Location",
                        conditions=[{"path": "Status", "type": "NotEqualTo", "value": "Closed"}]
                    ),
                    order=2
                ),
                SectionTemplate(
                    title="Outstanding Items",
                    section_type="table",
                    entity_def="punch list",
                    fields=["Number", "Description", "Location", "Trade", "Priority", "Status", "DueDate"],
                    conditions=[{"path": "Status", "type": "NotEqualTo", "value": "Closed"}],
                    order=3
                )
            ],
            tags=["punch", "closeout", "field"],
            is_public=True
        ),
        
        ReportTemplate(
            id="builtin-executive-summary",
            name="Executive Project Summary",
            description="High-level project overview for leadership with key metrics across all areas.",
            category="executive",
            created_at=now,
            updated_at=now,
            title_template="{project_name} - Executive Summary",
            subtitle_template="Monthly Report - {date}",
            sections=[
                SectionTemplate(
                    title="Project Health Dashboard",
                    section_type="metrics",
                    content="Key performance indicators across schedule, cost, and quality.",
                    order=0
                ),
                SectionTemplate(
                    title="Open Issues Summary",
                    section_type="table",
                    content="Critical open items requiring attention.",
                    order=1
                ),
                SectionTemplate(
                    title="Financial Status",
                    section_type="chart",
                    entity_def="contract",
                    chart=ChartTemplate(
                        chart_type="bar",
                        title="Budget vs Actual by Category",
                        data_source="contract",
                        group_by="Category"
                    ),
                    order=2
                ),
                SectionTemplate(
                    title="Risk Items",
                    section_type="text",
                    content="Top risks and mitigation strategies.",
                    order=3
                ),
                SectionTemplate(
                    title="Next Steps",
                    section_type="text",
                    content="Action items and upcoming milestones.",
                    order=4
                )
            ],
            tags=["executive", "summary", "dashboard"],
            is_public=True
        )
    ]


def init_builtin_templates(store: TemplateStore):
    """Initialize the database with built-in templates if not present."""
    existing = store.list_templates()
    existing_ids = {t.id for t in existing}
    
    for template in get_builtin_templates():
        if template.id not in existing_ids:
            store.create_template(template)


# Global store instance
_store: Optional[TemplateStore] = None

def get_template_store() -> TemplateStore:
    """Get or create the global template store."""
    global _store
    if _store is None:
        _store = TemplateStore()
        init_builtin_templates(_store)
    return _store
