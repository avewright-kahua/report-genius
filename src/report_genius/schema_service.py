"""
Centralized Schema Service

Single source of truth for entity schemas, field metadata, and mappings.
Fetches from Kahua API and caches results. Provides schema context to LLM.

This replaces the scattered hardcoded dictionaries:
- ENTITY_ALIASES
- ENTITY_DISPLAY_NAMES  
- LABEL_NORMALIZATIONS
- CHILD_ENTITY_PATHS
"""

import os
import json
import logging
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import lru_cache

import httpx

log = logging.getLogger("schema_service")

# ============== Configuration ==============

KAHUA_QUERY_URL = "https://demo01service.kahua.com/v2/domains/Summit/projects/{project_id}/query?returnDefaultAttributes=true"
CACHE_DIR = Path(__file__).parent.parent.parent / "data" / "schema_cache"
CACHE_TTL_HOURS = 24


def _get_kahua_auth() -> str:
    """Get Kahua API auth header."""
    auth = os.getenv("KAHUA_BASIC_AUTH", "")
    if not auth:
        raise RuntimeError("KAHUA_BASIC_AUTH not set")
    return auth if auth.strip().lower().startswith("basic ") else f"Basic {auth}"


# ============== Data Models ==============

@dataclass
class FieldInfo:
    """Information about an entity field."""
    path: str                    # e.g., "Status.Name", "Amount"
    name: str                    # e.g., "Status", "Amount"
    label: str                   # Human-readable: "Status", "Amount"
    data_type: str               # "string", "number", "date", "boolean", "object", "array"
    format_hint: str             # "text", "currency", "date", "number", "boolean", "rich_text"
    is_reference: bool = False   # True if this is a reference to another entity
    reference_entity: str = ""   # Entity def of referenced entity
    sample_value: Any = None     # Example value from real data
    

@dataclass
class EntitySchema:
    """Complete schema for a Kahua entity type."""
    entity_def: str              # e.g., "kahua_AEC_ChangeOrder.ChangeOrder"
    display_name: str            # e.g., "Change Order"
    description: str = ""
    fields: List[FieldInfo] = field(default_factory=list)
    child_collections: Dict[str, str] = field(default_factory=dict)  # path -> child entity_def
    fetched_at: Optional[datetime] = None
    sample_count: int = 0        # How many samples were used to build this
    
    def get_field(self, path: str) -> Optional[FieldInfo]:
        """Get a field by path (case-insensitive)."""
        path_lower = path.lower()
        for f in self.fields:
            if f.path.lower() == path_lower:
                return f
        return None
    
    def get_fields_by_format(self, format_hint: str) -> List[FieldInfo]:
        """Get all fields with a specific format hint."""
        return [f for f in self.fields if f.format_hint == format_hint]
    
    def to_llm_context(self) -> str:
        """Format schema for LLM context injection."""
        lines = [
            f"Entity: {self.display_name} ({self.entity_def})",
            f"Fields ({len(self.fields)}):",
        ]
        
        # Group by format
        by_format = {}
        for f in self.fields:
            by_format.setdefault(f.format_hint, []).append(f)
        
        for fmt, fields in sorted(by_format.items()):
            lines.append(f"\n  {fmt.upper()} fields:")
            for f in fields[:15]:  # Limit per category
                sample = f" (e.g., {f.sample_value})" if f.sample_value else ""
                lines.append(f"    - {f.path}: {f.label}{sample}")
        
        if self.child_collections:
            lines.append(f"\n  Child collections:")
            for path, child_def in self.child_collections.items():
                lines.append(f"    - {path} -> {child_def}")
        
        return "\n".join(lines)


# ============== Schema Service ==============

class SchemaService:
    """
    Centralized service for entity schema management.
    
    Usage:
        service = SchemaService()
        schema = await service.get_schema("kahua_AEC_ChangeOrder.ChangeOrder")
        
        # Or resolve from natural language
        schema = await service.resolve_entity("change order")
    """
    
    # Known entity aliases - bootstrap, but LLM can expand
    KNOWN_ALIASES = {
        # Change Order variants
        "change order": "kahua_AEC_ChangeOrder.ChangeOrder",
        "change orders": "kahua_AEC_ChangeOrder.ChangeOrder",
        "co": "kahua_AEC_ChangeOrder.ChangeOrder",
        "expense change order": "kahua_AEC_ChangeOrder.ChangeOrder",
        
        # RFI variants
        "rfi": "kahua_AEC_RFI.RFI",
        "rfis": "kahua_AEC_RFI.RFI",
        "request for information": "kahua_AEC_RFI.RFI",
        
        # Contract variants
        "contract": "kahua_Contract.Contract",
        "contracts": "kahua_Contract.Contract",
        "expense contract": "kahua_Contract.Contract",
        
        # Invoice variants
        "invoice": "kahua_ContractInvoice.ContractInvoice",
        "invoices": "kahua_ContractInvoice.ContractInvoice",
        
        # Submittal variants
        "submittal": "kahua_AEC_Submittal.Submittal",
        "submittals": "kahua_AEC_Submittal.Submittal",
        
        # Punch List variants
        "punch list": "kahua_AEC_PunchList.PunchListItem",
        "punchlist": "kahua_AEC_PunchList.PunchListItem",
        "punch item": "kahua_AEC_PunchList.PunchListItem",
        
        # Daily Report variants
        "daily report": "kahua_AEC_DailyReport.DailyReport",
        "daily": "kahua_AEC_DailyReport.DailyReport",
        "field report": "kahua_AEC_DailyReport.DailyReport",
        
        # Project
        "project": "kahua_Project.Project",
        "projects": "kahua_Project.Project",
        
        # Meeting
        "meeting": "kahua_Meeting.Meeting",
        "meetings": "kahua_Meeting.Meeting",
    }
    
    # Display names for known entities
    DISPLAY_NAMES = {
        "kahua_AEC_ChangeOrder.ChangeOrder": "Change Order",
        "kahua_AEC_RFI.RFI": "RFI",
        "kahua_Contract.Contract": "Contract",
        "kahua_ContractInvoice.ContractInvoice": "Invoice",
        "kahua_AEC_Submittal.Submittal": "Submittal",
        "kahua_AEC_PunchList.PunchListItem": "Punch List Item",
        "kahua_AEC_DailyReport.DailyReport": "Daily Report",
        "kahua_Project.Project": "Project",
        "kahua_Meeting.Meeting": "Meeting",
        "kahua_ContractChangeRequest.ContractChangeRequest": "Change Request",
    }
    
    def __init__(self):
        self._cache: Dict[str, EntitySchema] = {}
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
    def resolve_entity_def(self, name_or_def: str) -> str:
        """
        Resolve a natural language name or alias to entity_def.
        
        Examples:
            "change order" -> "kahua_AEC_ChangeOrder.ChangeOrder"
            "kahua_AEC_RFI.RFI" -> "kahua_AEC_RFI.RFI" (passthrough)
        """
        if not name_or_def:
            return ""
        
        # Already a full entity def?
        if "." in name_or_def and name_or_def.startswith("kahua_"):
            return name_or_def
        
        # Lookup alias
        key = name_or_def.strip().lower()
        return self.KNOWN_ALIASES.get(key, name_or_def)
    
    def get_display_name(self, entity_def: str) -> str:
        """Get human-readable name for an entity type."""
        if entity_def in self.DISPLAY_NAMES:
            return self.DISPLAY_NAMES[entity_def]
        # Extract from entity_def: "kahua_AEC_ChangeOrder.ChangeOrder" -> "Change Order"
        if "." in entity_def:
            name = entity_def.split(".")[-1]
            # Insert spaces before capitals: "ChangeOrder" -> "Change Order"
            import re
            return re.sub(r'([a-z])([A-Z])', r'\1 \2', name)
        return entity_def
    
    async def get_schema(
        self, 
        entity_def: str, 
        force_refresh: bool = False
    ) -> Optional[EntitySchema]:
        """
        Get schema for an entity type, fetching from Kahua if needed.
        
        Args:
            entity_def: The entity definition or alias
            force_refresh: If True, bypass cache
            
        Returns:
            EntitySchema or None if not found
        """
        # Resolve alias
        entity_def = self.resolve_entity_def(entity_def)
        if not entity_def:
            return None
        
        # Check memory cache
        if not force_refresh and entity_def in self._cache:
            schema = self._cache[entity_def]
            if schema.fetched_at and datetime.now() - schema.fetched_at < timedelta(hours=CACHE_TTL_HOURS):
                return schema
        
        # Check disk cache
        cache_path = CACHE_DIR / f"{entity_def.replace('.', '_')}.json"
        if not force_refresh and cache_path.exists():
            try:
                with open(cache_path, 'r') as f:
                    data = json.load(f)
                schema = self._dict_to_schema(data)
                if schema.fetched_at and datetime.now() - schema.fetched_at < timedelta(hours=CACHE_TTL_HOURS):
                    self._cache[entity_def] = schema
                    return schema
            except Exception as e:
                log.warning(f"Failed to load cached schema: {e}")
        
        # Fetch from Kahua
        schema = await self._fetch_schema_from_kahua(entity_def)
        if schema:
            self._cache[entity_def] = schema
            # Save to disk cache
            try:
                with open(cache_path, 'w') as f:
                    json.dump(self._schema_to_dict(schema), f, indent=2, default=str)
            except Exception as e:
                log.warning(f"Failed to cache schema: {e}")
        
        return schema
    
    async def _fetch_schema_from_kahua(
        self, 
        entity_def: str, 
        sample_count: int = 10
    ) -> Optional[EntitySchema]:
        """Fetch schema by sampling records from Kahua API."""
        try:
            query_url = KAHUA_QUERY_URL.format(project_id=0)
            headers = {
                "Content-Type": "application/json",
                "Authorization": _get_kahua_auth()
            }
            payload = {
                "PropertyName": "Query",
                "EntityDef": entity_def,
                "Take": str(sample_count),
                "Partition": {"Scope": "Any"}
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(query_url, headers=headers, json=payload)
                if resp.status_code >= 400:
                    log.error(f"Kahua query failed: {resp.status_code}")
                    return None
                body = resp.json()
            
            # Extract samples
            samples = []
            for key in ("entities", "results", "items"):
                if isinstance(body.get(key), list) and body[key]:
                    samples = body[key]
                    break
            for s in body.get("sets", []):
                if isinstance(s.get("entities"), list) and s["entities"]:
                    samples = s["entities"]
                    break
            
            if not samples:
                log.warning(f"No samples found for {entity_def}")
                return EntitySchema(
                    entity_def=entity_def,
                    display_name=self.get_display_name(entity_def),
                    fetched_at=datetime.now()
                )
            
            # Merge samples to get complete field coverage
            merged = self._merge_samples(samples)
            
            # Extract fields
            fields = self._extract_fields(merged)
            
            # Detect child collections
            children = self._detect_children(merged)
            
            return EntitySchema(
                entity_def=entity_def,
                display_name=self.get_display_name(entity_def),
                fields=fields,
                child_collections=children,
                fetched_at=datetime.now(),
                sample_count=len(samples)
            )
            
        except Exception as e:
            log.error(f"Failed to fetch schema for {entity_def}: {e}")
            return None
    
    def _merge_samples(self, samples: List[Dict]) -> Dict:
        """Merge multiple samples to get complete field coverage."""
        merged = {}
        for sample in samples:
            for key, value in sample.items():
                if key not in merged:
                    merged[key] = value
                elif merged[key] is None and value is not None:
                    merged[key] = value
                elif isinstance(merged[key], dict) and isinstance(value, dict):
                    for k, v in value.items():
                        if k not in merged[key] or merged[key][k] is None:
                            merged[key][k] = v
        return merged
    
    def _extract_fields(self, merged: Dict, prefix: str = "", depth: int = 0) -> List[FieldInfo]:
        """Extract field definitions from merged sample data."""
        fields = []
        
        # Skip system/internal fields
        skip_fields = {
            '_links', '_embedded', 'Links', 'Embedded', 'EntityDef',
            'PartitionScope', 'IsLegacy', 'Hash', 'Marker',
            'RowVersion', 'RecordId', 'UniqueId', 'hubPath'
        }
        
        if depth > 2:
            return fields
        
        for key, value in merged.items():
            if key in skip_fields or key.startswith('_'):
                continue
            
            full_path = f"{prefix}{key}" if prefix else key
            
            if isinstance(value, dict) and value:
                # Reference field - add display fields
                for display_field in ['ShortLabel', 'Name', 'Number', 'Label', 'Title']:
                    if display_field in value:
                        fields.append(FieldInfo(
                            path=f"{full_path}.{display_field}",
                            name=key,
                            label=self._make_label(key),
                            data_type="reference",
                            format_hint="text",
                            is_reference=True,
                            sample_value=value.get(display_field)
                        ))
                        break
                else:
                    # Recurse into nested object
                    nested = self._extract_fields(value, f"{full_path}.", depth + 1)
                    fields.extend(nested)
                    
            elif isinstance(value, list):
                # Skip collections (handled separately as children)
                continue
            else:
                # Simple field
                data_type = self._infer_data_type(value)
                format_hint = self._infer_format_hint(key, value)
                
                fields.append(FieldInfo(
                    path=full_path,
                    name=key,
                    label=self._make_label(key),
                    data_type=data_type,
                    format_hint=format_hint,
                    sample_value=str(value)[:100] if value is not None else None
                ))
        
        return sorted(fields, key=lambda f: f.path)
    
    def _detect_children(self, merged: Dict) -> Dict[str, str]:
        """Detect child entity collections."""
        children = {}
        for key, value in merged.items():
            if isinstance(value, list) and value and isinstance(value[0], dict):
                # This is likely a child collection
                # Try to infer entity def from content
                child_sample = value[0]
                child_def = child_sample.get('EntityDef', '')
                if child_def:
                    children[key] = child_def
                else:
                    children[key] = f"<unknown collection: {key}>"
        return children
    
    def _infer_data_type(self, value: Any) -> str:
        """Infer JSON data type from value."""
        if value is None:
            return "string"
        if isinstance(value, bool):
            return "boolean"
        if isinstance(value, int):
            return "integer"
        if isinstance(value, float):
            return "number"
        if isinstance(value, dict):
            return "object"
        if isinstance(value, list):
            return "array"
        return "string"
    
    def _infer_format_hint(self, key: str, value: Any) -> str:
        """Infer format hint from field name and value."""
        key_lower = key.lower()
        
        # Currency indicators
        if any(x in key_lower for x in ['amount', 'cost', 'price', 'value', 'total', 'fee', 'budget', 'sum']):
            return "currency"
        
        # Date indicators
        if any(x in key_lower for x in ['date', 'datetime', 'time', 'created', 'modified', 'due', 'start', 'end']):
            return "date"
        
        # Boolean indicators
        if key_lower.startswith(('is', 'has', 'can', 'should', 'allow', 'enable')):
            return "boolean"
        if isinstance(value, bool):
            return "boolean"
        
        # Number indicators
        if any(x in key_lower for x in ['count', 'qty', 'quantity', 'days', 'hours', 'percent']):
            if key_lower != 'number':  # "Number" is usually an ID
                return "number"
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return "number"
        
        # Rich text indicators
        if any(x in key_lower for x in ['description', 'notes', 'comment', 'body', 'content', 'question', 'answer', 'scope']):
            return "rich_text"
        
        # Check value for date pattern
        if isinstance(value, str) and 'T' in value and len(value) > 15:
            return "date"
        
        return "text"
    
    def _make_label(self, key: str) -> str:
        """Convert field name to human-readable label."""
        import re
        result = re.sub(r'([a-z])([A-Z])', r'\1 \2', key)
        result = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1 \2', result)
        return result
    
    def _schema_to_dict(self, schema: EntitySchema) -> Dict:
        """Convert schema to JSON-serializable dict."""
        return {
            "entity_def": schema.entity_def,
            "display_name": schema.display_name,
            "description": schema.description,
            "fields": [
                {
                    "path": f.path,
                    "name": f.name,
                    "label": f.label,
                    "data_type": f.data_type,
                    "format_hint": f.format_hint,
                    "is_reference": f.is_reference,
                    "reference_entity": f.reference_entity,
                    "sample_value": f.sample_value,
                }
                for f in schema.fields
            ],
            "child_collections": schema.child_collections,
            "fetched_at": schema.fetched_at.isoformat() if schema.fetched_at else None,
            "sample_count": schema.sample_count,
        }
    
    def _dict_to_schema(self, data: Dict) -> EntitySchema:
        """Convert dict back to EntitySchema."""
        fields = [
            FieldInfo(**f) for f in data.get("fields", [])
        ]
        fetched_at = None
        if data.get("fetched_at"):
            fetched_at = datetime.fromisoformat(data["fetched_at"])
        
        return EntitySchema(
            entity_def=data["entity_def"],
            display_name=data["display_name"],
            description=data.get("description", ""),
            fields=fields,
            child_collections=data.get("child_collections", {}),
            fetched_at=fetched_at,
            sample_count=data.get("sample_count", 0),
        )
    
    def list_known_entities(self) -> List[Dict[str, str]]:
        """List all known entity types."""
        seen = set()
        result = []
        for alias, entity_def in self.KNOWN_ALIASES.items():
            if entity_def not in seen:
                seen.add(entity_def)
                result.append({
                    "entity_def": entity_def,
                    "display_name": self.get_display_name(entity_def),
                    "aliases": [a for a, e in self.KNOWN_ALIASES.items() if e == entity_def]
                })
        return result


# ============== Global Instance ==============

_schema_service: Optional[SchemaService] = None

def get_schema_service() -> SchemaService:
    """Get the global schema service instance."""
    global _schema_service
    if _schema_service is None:
        _schema_service = SchemaService()
    return _schema_service


# ============== Convenience Functions ==============

async def get_entity_schema(entity_def: str) -> Optional[EntitySchema]:
    """Get schema for an entity type."""
    return await get_schema_service().get_schema(entity_def)


def resolve_entity(name_or_def: str) -> str:
    """Resolve alias to entity_def."""
    return get_schema_service().resolve_entity_def(name_or_def)


def get_display_name(entity_def: str) -> str:
    """Get display name for entity."""
    return get_schema_service().get_display_name(entity_def)
