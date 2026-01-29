"""
Schema Introspector - Extracts and classifies fields from Pydantic models.

This module provides semantic understanding of entity schemas by analyzing
field names, types, and patterns to classify them into meaningful categories
that inform template generation.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import (
    Any,
    Dict,
    ForwardRef,
    List,
    Optional,
    Set,
    Type,
    Union,
    get_args,
    get_origin,
)

from pydantic import BaseModel


class FieldCategory(str, Enum):
    """Semantic categories for entity fields."""
    
    IDENTITY = "identity"           # Number, ID, Name, Subject - goes in header
    STATUS = "status"               # Status, State, Workflow - key metadata
    FINANCIAL = "financial"         # Currency amounts, costs, values
    DATE = "date"                   # Dates and timestamps
    CONTACT = "contact"             # People, companies, assignments
    TEXT_BLOCK = "text_block"       # Long-form text (scope, notes, description)
    TEXT_SHORT = "text_short"       # Short text fields
    BOOLEAN = "boolean"             # Yes/no flags
    NUMERIC = "numeric"             # Non-financial numbers
    COLLECTION = "collection"       # Lists of child entities
    NESTED = "nested"               # Single nested object
    REFERENCE = "reference"         # References to other entities
    LOOKUP = "lookup"               # Lookup/enum values
    UNKNOWN = "unknown"             # Unclassified


@dataclass
class FieldInfo:
    """Metadata about a single field in an entity schema."""
    
    name: str                       # Python field name (snake_case)
    path: str                       # API path (PascalCase via alias)
    label: str                      # Human-readable label
    python_type: Any                # Original Python type annotation
    category: FieldCategory         # Semantic classification
    is_optional: bool               # Whether field can be None
    is_list: bool                   # Whether field is a collection
    child_type: Optional[str]       # For collections/nested, the child model name
    child_fields: List[FieldInfo] = field(default_factory=list)  # Nested field metadata
    format_hint: Optional[str] = None  # Suggested format (currency, date, etc.)
    

@dataclass  
class EntitySchema:
    """Complete schema information for an entity type."""
    
    name: str                       # Model class name
    entity_def: str                 # Kahua entity definition path
    fields: List[FieldInfo]         # All fields with metadata
    
    def by_category(self, category: FieldCategory) -> List[FieldInfo]:
        """Get all fields matching a category."""
        return [f for f in self.fields if f.category == category]
    
    def identity_fields(self) -> List[FieldInfo]:
        return self.by_category(FieldCategory.IDENTITY)
    
    def financial_fields(self) -> List[FieldInfo]:
        return self.by_category(FieldCategory.FINANCIAL)
    
    def date_fields(self) -> List[FieldInfo]:
        return self.by_category(FieldCategory.DATE)
    
    def contact_fields(self) -> List[FieldInfo]:
        return self.by_category(FieldCategory.CONTACT)
    
    def text_blocks(self) -> List[FieldInfo]:
        return self.by_category(FieldCategory.TEXT_BLOCK)
    
    def collections(self) -> List[FieldInfo]:
        return self.by_category(FieldCategory.COLLECTION)


# Pattern matching for field classification
IDENTITY_PATTERNS = {
    r"^number$", r"^id$", r"^name$", r"^subject$", r"^title$",
    r"^reference$", r"_number$", r"_id$"
}

STATUS_PATTERNS = {
    r"^status", r"^state$", r"^workflow", r"^phase$", r"^priority$",
    r"_status$", r"_state$"
}

FINANCIAL_PATTERNS = {
    r"amount", r"value", r"cost", r"total", r"price", r"rate$",
    r"retainage", r"damages", r"budget", r"fee"
}

CONTACT_PATTERNS = {
    r"contact$", r"^author$", r"^creator$", r"^assigned", r"^responder",
    r"_to$", r"_by$", r"_from$", r"company$", r"representative$",
    r"coordinator$", r"reviewer", r"signer"
}

TEXT_BLOCK_PATTERNS = {
    r"^scope", r"^description$", r"^notes$", r"^question$", r"^answer$",
    r"^response", r"^comment", r"^remarks", r"^instructions", r"^provisions",
    r"^disclaimer", r"solution$", r"_text\d*$"
}

REFERENCE_PATTERNS = {
    r"reference", r"^source_", r"outward_", r"^link"
}

LOOKUP_PATTERNS = {
    r"^type$", r"_type$", r"^category$", r"^discipline$", r"^reason$",
    r"^root_cause$", r"lookup\d*$"
}


def _to_pascal(name: str) -> str:
    """Convert snake_case to PascalCase."""
    parts = name.split("_")
    return "".join(part[:1].upper() + part[1:] for part in parts if part)


def _to_label(name: str) -> str:
    """Convert snake_case to human-readable label."""
    # Handle special cases
    name = re.sub(r"_(\d+)$", r" \1", name)  # custom_text1 -> custom text 1
    name = name.replace("_", " ")
    # Title case but preserve acronyms
    words = name.split()
    result = []
    for word in words:
        if word.upper() in {"ID", "RFI", "CSI", "URL", "DB"}:
            result.append(word.upper())
        else:
            result.append(word.capitalize())
    return " ".join(result)


def _matches_pattern(name: str, patterns: Set[str]) -> bool:
    """Check if field name matches any pattern."""
    name_lower = name.lower()
    return any(re.search(p, name_lower) for p in patterns)


def _get_inner_type(type_hint: Any) -> tuple[Any, bool]:
    """Extract inner type from Optional/List wrappers.
    
    Returns:
        Tuple of (inner_type, is_list)
    """
    origin = get_origin(type_hint)
    
    # Handle Optional[X] which is Union[X, None]
    if origin is Union:
        args = get_args(type_hint)
        non_none = [a for a in args if a is not type(None)]
        if len(non_none) == 1:
            return _get_inner_type(non_none[0])
        return type_hint, False
    
    # Handle List[X]
    if origin is list:
        args = get_args(type_hint)
        if args:
            return args[0], True
        return Any, True
    
    return type_hint, False


def _classify_field(
    name: str,
    type_hint: Any,
    is_list: bool,
    inner_type: Any,
) -> tuple[FieldCategory, Optional[str]]:
    """Classify a field based on name and type.
    
    Returns:
        Tuple of (category, format_hint)
    """
    name_lower = name.lower()
    
    # Collections are always COLLECTION
    if is_list:
        # Check if it's a list of primitives vs objects
        if inner_type in (str, int, float, bool):
            return FieldCategory.TEXT_SHORT, None
        return FieldCategory.COLLECTION, None
    
    # Check type-based classifications first
    if inner_type in (date, datetime):
        return FieldCategory.DATE, "date" if inner_type is date else "datetime"
    
    if inner_type is Decimal:
        # Decimal is usually financial
        if _matches_pattern(name, FINANCIAL_PATTERNS):
            return FieldCategory.FINANCIAL, "currency"
        return FieldCategory.NUMERIC, "decimal"
    
    if inner_type in (int, float):
        if _matches_pattern(name, FINANCIAL_PATTERNS):
            return FieldCategory.FINANCIAL, "currency"
        return FieldCategory.NUMERIC, None
    
    if inner_type is bool:
        return FieldCategory.BOOLEAN, None
    
    # Check if it's a nested model
    if isinstance(inner_type, type) and issubclass(inner_type, BaseModel):
        if _matches_pattern(name, CONTACT_PATTERNS):
            return FieldCategory.CONTACT, None
        return FieldCategory.NESTED, None
    
    # ForwardRef means nested model defined later
    if isinstance(inner_type, (ForwardRef, str)):
        type_name = inner_type.__forward_arg__ if isinstance(inner_type, ForwardRef) else inner_type
        if "contact" in type_name.lower() or "company" in type_name.lower():
            return FieldCategory.CONTACT, None
        return FieldCategory.NESTED, None
    
    # String fields - classify by name patterns
    if inner_type is str or inner_type is Any:
        if _matches_pattern(name, IDENTITY_PATTERNS):
            return FieldCategory.IDENTITY, None
        if _matches_pattern(name, STATUS_PATTERNS):
            return FieldCategory.STATUS, None
        if _matches_pattern(name, TEXT_BLOCK_PATTERNS):
            return FieldCategory.TEXT_BLOCK, None
        if _matches_pattern(name, REFERENCE_PATTERNS):
            return FieldCategory.REFERENCE, None
        if _matches_pattern(name, LOOKUP_PATTERNS):
            return FieldCategory.LOOKUP, None
        if _matches_pattern(name, CONTACT_PATTERNS):
            return FieldCategory.CONTACT, None
        return FieldCategory.TEXT_SHORT, None
    
    return FieldCategory.UNKNOWN, None


def _get_type_name(type_hint: Any) -> Optional[str]:
    """Get the name of a type for nested/collection types."""
    if isinstance(type_hint, type):
        return type_hint.__name__
    if isinstance(type_hint, ForwardRef):
        return type_hint.__forward_arg__
    if isinstance(type_hint, str):
        return type_hint
    return None


def introspect_model(
    model: Type[BaseModel],
    entity_def: Optional[str] = None,
    _visited: Optional[Set[str]] = None,
) -> EntitySchema:
    """Extract complete schema information from a Pydantic model.
    
    Args:
        model: The Pydantic model class to introspect
        entity_def: Optional Kahua entity definition path
        _visited: Internal set to prevent infinite recursion
    
    Returns:
        EntitySchema with all field metadata
    """
    import typing
    
    if _visited is None:
        _visited = set()
    
    model_name = model.__name__
    if model_name in _visited:
        # Prevent infinite recursion for self-referential models
        return EntitySchema(name=model_name, entity_def=entity_def or "", fields=[])
    
    _visited.add(model_name)
    
    fields: List[FieldInfo] = []
    
    # Get field definitions from Pydantic
    model_fields = model.__fields__ if hasattr(model, "__fields__") else model.model_fields
    
    # Use get_type_hints for accurate type annotations (Pydantic v2 can lose them)
    try:
        type_hints = typing.get_type_hints(model)
    except Exception:
        type_hints = {}
    
    for field_name, field_def in model_fields.items():
        # Get type annotation - prefer get_type_hints() for accuracy
        if field_name in type_hints:
            type_hint = type_hints[field_name]
        elif hasattr(field_def, "annotation") and field_def.annotation is not type(None):
            # Pydantic v2 fallback
            type_hint = field_def.annotation
        elif hasattr(field_def, "outer_type_"):
            # Pydantic v1
            type_hint = field_def.outer_type_
        else:
            type_hint = Any
        
        # Get alias
        alias = getattr(field_def, "alias", None)
        
        # Determine API path (use alias if set, otherwise convert to PascalCase)
        path = alias if alias else _to_pascal(field_name)
        
        # Extract inner type and check if list
        inner_type, is_list = _get_inner_type(type_hint)
        
        # Check if optional (original type was Optional[X])
        is_optional = get_origin(type_hint) is Union and type(None) in get_args(type_hint)
        
        # Classify the field
        category, format_hint = _classify_field(field_name, type_hint, is_list, inner_type)
        
        # Get child type name for nested/collection
        child_type = _get_type_name(inner_type)
        
        # Recursively introspect nested models
        child_fields: List[FieldInfo] = []
        if category in (FieldCategory.COLLECTION, FieldCategory.NESTED):
            if isinstance(inner_type, type) and issubclass(inner_type, BaseModel):
                child_schema = introspect_model(inner_type, _visited=_visited)
                child_fields = child_schema.fields
        
        field_info = FieldInfo(
            name=field_name,
            path=path,
            label=_to_label(field_name),
            python_type=type_hint,
            category=category,
            is_optional=is_optional,
            is_list=is_list,
            child_type=child_type,
            child_fields=child_fields,
            format_hint=format_hint,
        )
        fields.append(field_info)
    
    _visited.discard(model_name)
    
    return EntitySchema(
        name=model_name,
        entity_def=entity_def or f"kahua.{model_name}",
        fields=fields,
    )


def get_schema_summary(schema: EntitySchema) -> Dict[str, Any]:
    """Generate a summary of schema for agent consumption.
    
    Returns a structured dict that can be included in prompts.
    """
    summary = {
        "entity": schema.name,
        "entity_def": schema.entity_def,
        "field_counts": {},
        "fields_by_category": {},
    }
    
    for category in FieldCategory:
        fields = schema.by_category(category)
        if fields:
            summary["field_counts"][category.value] = len(fields)
            summary["fields_by_category"][category.value] = [
                {
                    "name": f.name,
                    "path": f.path,
                    "label": f.label,
                    "format": f.format_hint,
                    "child_type": f.child_type,
                }
                for f in fields
            ]
    
    return summary


# Convenience function to introspect all known models
def get_available_schemas() -> Dict[str, EntitySchema]:
    """Load and introspect all known entity models."""
    schemas = {}
    
    try:
        from models.expense_contract_model import ExpenseContractModel
        schemas["ExpenseContract"] = introspect_model(
            ExpenseContractModel,
            entity_def="kahua.expensecontract"
        )
    except ImportError:
        pass
    
    try:
        from models.RFI_model import RFIModel
        schemas["RFI"] = introspect_model(
            RFIModel,
            entity_def="kahua.rfi"
        )
    except ImportError:
        pass
    
    try:
        from models.submittal_model import SubmittalModel
        schemas["Submittal"] = introspect_model(
            SubmittalModel,
            entity_def="kahua.submittal"
        )
    except ImportError:
        pass
    
    try:
        from models.expense_change_order_model import ExpenseChangeOrderModel
        schemas["ExpenseChangeOrder"] = introspect_model(
            ExpenseChangeOrderModel,
            entity_def="kahua.expensechangeorder"
        )
    except ImportError:
        pass
    
    try:
        from models.field_observation_model import FieldObservationModel
        schemas["FieldObservation"] = introspect_model(
            FieldObservationModel,
            entity_def="kahua.fieldobservationitem"
        )
    except ImportError:
        pass
    
    try:
        from models.invoice_model import InvoiceModel
        schemas["Invoice"] = introspect_model(
            InvoiceModel,
            entity_def="kahua.invoice"
        )
    except ImportError:
        pass
    
    return schemas


if __name__ == "__main__":
    # Demo: introspect available models and print summary
    import json
    
    schemas = get_available_schemas()
    
    for name, schema in schemas.items():
        print(f"\n{'='*60}")
        print(f"Entity: {schema.name} ({schema.entity_def})")
        print(f"{'='*60}")
        
        summary = get_schema_summary(schema)
        
        print(f"\nField counts by category:")
        for cat, count in summary["field_counts"].items():
            print(f"  {cat}: {count}")
        
        print(f"\nIdentity fields: {[f.path for f in schema.identity_fields()]}")
        print(f"Financial fields: {[f.path for f in schema.financial_fields()]}")
        print(f"Date fields: {[f.path for f in schema.date_fields()]}")
        print(f"Contact fields: {[f.path for f in schema.contact_fields()]}")
        print(f"Text blocks: {[f.path for f in schema.text_blocks()]}")
        print(f"Collections: {[f.path for f in schema.collections()]}")
