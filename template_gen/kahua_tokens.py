"""
Kahua Portable View Token Reference

Authoritative implementation of Kahua token syntax based on official documentation.
All token builders in this module conform to the Kahua Portable View specification.

Reference: docs/page_2.md (Creating Portable View Templates)
Reference: docs/KAHUA_QUICK_REFERENCE.md
Reference: ss_examples/kahua_syntax_reference.md

Token Types:
- Attribute tokens: [Attribute], [Boolean], [Currency], [Date], [Number], [RichText]
- List tokens: [AttributeList]
- Table tokens: [StartTable], [EndTable]
- List output tokens: [StartList], [EndList], [StartContentTemplate], [EndContentTemplate]
- Conditional tokens: [IF], [THEN], [ENDTHEN], [ELSE], [ENDELSE], [ENDIF]
- System tokens: [ProjectName], [ProjectNumber], [CompanyLogo], [ReportModifiedTimeStamp], etc.
- Signature tokens: [Signature], [DocuSign]
- Media tokens: [Image], [Media]
"""

from __future__ import annotations

from enum import Enum
from typing import Optional, List, Dict, Any, Literal


# =============================================================================
# Token Type Enums (from Kahua docs)
# =============================================================================

class TokenSource(str, Enum):
    """Source parameter values for Kahua tokens."""
    ATTRIBUTE = "Attribute"     # Current entity (default)
    PROJECT = "Project"         # Current project context
    LITERAL = "Literal"         # Literal/constant value
    CHRONOLOGY = "Chronology"   # Entity chronology (tables only)
    STEP_HISTORY = "StepHistory"  # Workflow step history (tables only)
    COLLECTION = "Collection"   # Entity from a collection at index
    CURRENT = "Current"         # Current date/time (Date tokens)


class ConditionOperator(str, Enum):
    """Operators for conditional expressions in Kahua tokens."""
    EQUALS = "Equals"
    DOES_NOT_EQUAL = "DoesNotEqual"
    CONTAINS = "Contains"
    DOES_NOT_CONTAIN = "DoesNotContain"
    IN = "In"  # Value is in comma-separated list
    IS_GREATER_THAN = "IsGreaterThan"
    IS_GREATER_THAN_OR_EQUAL_TO = "IsGreaterThanOrEqualTo"
    IS_LESS_THAN = "IsLessThan"
    IS_LESS_THAN_OR_EQUAL_TO = "IsLessThanOrEqualTo"
    IS_EMPTY = "IsEmpty"
    IS_NOT_EMPTY = "IsNotEmpty"
    IS_NULL = "IsNull"
    IS_NOT_NULL = "IsNotNull"
    IS_TRUE = "IsTrue"
    IS_FALSE = "IsFalse"
    CONTAINED_IN = "ContainedIn"
    NOT_CONTAINED_IN = "NotContainedIn"


class DateFormat(str, Enum):
    """Standard .NET date format specifiers for Kahua Date tokens."""
    SHORT_DATE = "d"           # 1/28/2026
    LONG_DATE = "D"            # Tuesday, January 28, 2026
    SHORT_TIME = "t"           # 5:30 PM
    LONG_TIME = "T"            # 5:30:00 PM
    FULL_SHORT = "f"           # Tuesday, January 28, 2026 5:30 PM
    FULL_LONG = "F"            # Tuesday, January 28, 2026 5:30:00 PM
    GENERAL_SHORT = "g"        # 1/28/2026 5:30 PM
    GENERAL_LONG = "G"         # 1/28/2026 5:30:00 PM
    MONTH_DAY = "M"            # January 28
    YEAR_MONTH = "Y"           # January 2026
    SORTABLE = "s"             # 2026-01-28T17:30:00
    RFC1123 = "R"              # Tue, 28 Jan 2026 17:30:00 GMT


class NumberFormat(str, Enum):
    """Standard .NET number format specifiers for Kahua Number tokens."""
    INTEGER = "N0"             # 1,234 (integer with commas)
    ONE_DECIMAL = "N1"         # 1,234.5
    TWO_DECIMALS = "N2"        # 1,234.56
    FIXED_0 = "F0"             # 1234 (no commas)
    FIXED_1 = "F1"             # 1234.5
    FIXED_2 = "F2"             # 1234.56
    PERCENT_0 = "P0"           # 45%
    PERCENT_1 = "P1"           # 45.5%
    PERCENT_2 = "P2"           # 45.50%


class CurrencyFormat(str, Enum):
    """Format specifiers for Kahua Currency tokens."""
    DEFAULT = "C2"             # $1,234.56 (standard)
    NO_DECIMALS = "C0"         # $1,235
    WORDS_MIXED = "WordsMixedCase"  # Three Hundred Dollars And Zero Cents
    WORDS_UPPER = "WordsUpperCase"  # THREE HUNDRED DOLLARS AND ZERO CENTS
    WORDS_LOWER = "WordsLowerCase"  # three hundred dollars and zero cents


class CurrencyType(str, Enum):
    """Currency type parameter for multi-currency support."""
    DOCUMENT = "Document"      # Document currency (default)
    PROJECT = "Project"        # Project currency
    DOMAIN = "Domain"          # Domain currency


# =============================================================================
# Path Conversion Utilities
# =============================================================================

def to_kahua_path(path: str, entity_prefix: Optional[str] = None) -> str:
    """
    Convert a template field path to Kahua attribute path format.
    
    Kahua paths use PascalCase and dot notation.
    Example: "status.name" -> "Status.Name"
    Example: "csi_code" -> "CSICode" (with proper alias handling)
    
    Args:
        path: Field path in template format
        entity_prefix: Optional entity prefix (e.g., "RFI", "Contract")
    
    Returns:
        Kahua-compatible attribute path
    """
    if not path:
        return path
    
    # Already a Kahua placeholder? Return as-is
    if path.startswith("[") and path.endswith("]"):
        return path
    
    parts = path.split(".")
    pascal_parts = []
    
    for part in parts:
        # Handle snake_case to PascalCase
        if "_" in part:
            segments = part.split("_")
            # Special handling for known acronyms
            converted = []
            for seg in segments:
                if seg.upper() in ("CSI", "RFI", "QR", "ID", "DB", "DSA", "BP"):
                    converted.append(seg.upper())
                elif seg:
                    converted.append(seg.capitalize())
            pascal_parts.append("".join(converted))
        else:
            # Capitalize first letter, preserve rest
            if part:
                pascal_parts.append(part[0].upper() + part[1:] if len(part) > 1 else part.upper())
    
    result = ".".join(pascal_parts)
    
    # Add entity prefix if provided and not already present
    if entity_prefix and not result.startswith(f"{entity_prefix}."):
        return f"{entity_prefix}.{result}"
    
    return result


# =============================================================================
# Attribute Token Builders
# =============================================================================

def build_attribute_token(
    path: str,
    source: TokenSource = TokenSource.ATTRIBUTE,
    prefix: Optional[str] = None,
    visible_when: Optional[ConditionOperator] = None,
    visible_when_path: Optional[str] = None,
    value: Optional[str] = None,
    visible_value: Optional[str] = None,
    default_value: Optional[str] = None,
    prepend_text: Optional[str] = None,
    append_text: Optional[str] = None,
) -> str:
    """
    Build a Kahua [Attribute(...)] token.
    
    Basic: [Attribute(FieldName)]
    Full: [Attribute(Source=Attribute,Path=Field,VisibleWhen=IsNotEmpty,...)]
    
    Args:
        path: Attribute path (e.g., "Number", "Status.Name")
        source: Token source (Attribute, Project, etc.)
        prefix: Optional entity prefix
        visible_when: Conditional visibility operator
        visible_when_path: Path for visibility condition (defaults to path)
        value: Value for comparison operators
        visible_value: Value to show if condition is true
        default_value: Value to show if condition is false
        prepend_text: Text to prepend to value
        append_text: Text to append to value
    
    Returns:
        Formatted Kahua attribute token string
    """
    kahua_path = to_kahua_path(path, prefix)
    
    # Simple form: [Attribute(Path)]
    if source == TokenSource.ATTRIBUTE and not any([
        visible_when, visible_value, default_value, prepend_text, append_text
    ]):
        return f"[Attribute({kahua_path})]"
    
    # Parameterized form
    params = []
    if source != TokenSource.ATTRIBUTE:
        params.append(f"Source={source.value}")
    params.append(f"Path={kahua_path}")
    
    if visible_when:
        params.append(f"VisibleWhen={visible_when.value}")
        if visible_when_path:
            params.append(f"VisibleWhenPath={to_kahua_path(visible_when_path, prefix)}")
        if value is not None:
            params.append(f'Value="{value}"')
    
    if visible_value is not None:
        params.append(f'VisibleValue="{visible_value}"')
    if default_value is not None:
        params.append(f'DefaultValue="{default_value}"')
    if prepend_text:
        params.append(f'PrependText="{prepend_text}"')
    if append_text:
        params.append(f'AppendText="{append_text}"')
    
    return f"[Attribute({','.join(params)})]"


def build_boolean_token(
    path: str,
    source: TokenSource = TokenSource.ATTRIBUTE,
    prefix: Optional[str] = None,
    true_value: str = "Yes",
    false_value: str = "No",
    empty_value: Optional[str] = None,
) -> str:
    """
    Build a Kahua [Boolean(...)] token.
    
    Example: [Boolean(Source=Attribute,Path=IsComplete,TrueValue="Yes",FalseValue="No")]
    
    For checkbox display, use:
        true_value="☒", false_value="☐"
    """
    kahua_path = to_kahua_path(path, prefix)
    
    params = [f"Source={source.value}", f"Path={kahua_path}"]
    params.append(f'TrueValue="{true_value}"')
    params.append(f'FalseValue="{false_value}"')
    
    if empty_value is not None:
        params.append(f'EmptyValue="{empty_value}"')
    
    return f"[Boolean({','.join(params)})]"


def build_currency_token(
    path: str,
    source: TokenSource = TokenSource.ATTRIBUTE,
    prefix: Optional[str] = None,
    format: CurrencyFormat = CurrencyFormat.DEFAULT,
    currency_type: CurrencyType = CurrencyType.DOCUMENT,
) -> str:
    """
    Build a Kahua [Currency(...)] token.
    
    Example: [Currency(Source=Attribute,Path=Amount,Format="C2")]
    
    For word output: Format="WordsMixedCase" -> "Three Hundred Dollars And Zero Cents"
    """
    kahua_path = to_kahua_path(path, prefix)
    
    params = [f"Source={source.value}", f"Path={kahua_path}"]
    
    # Only add Format if not default
    if format != CurrencyFormat.DEFAULT or format.value.startswith("Words"):
        params.append(f'Format="{format.value}"')
    
    # Only add CurrencyType if not Document (default)
    if currency_type != CurrencyType.DOCUMENT:
        params.append(f"CurrencyType={currency_type.value}")
    
    return f"[Currency({','.join(params)})]"


def build_date_token(
    path: str,
    source: TokenSource = TokenSource.ATTRIBUTE,
    prefix: Optional[str] = None,
    format: DateFormat = DateFormat.SHORT_DATE,
) -> str:
    """
    Build a Kahua [Date(...)] token.
    
    Example: [Date(Source=Attribute,Path=DueDate,Format="d")]
    
    Common formats:
        "d" = Short date (1/28/2026)
        "D" = Long date (Tuesday, January 28, 2026)
        "g" = General short (1/28/2026 5:30 PM)
    """
    kahua_path = to_kahua_path(path, prefix)
    
    params = [f"Source={source.value}", f"Path={kahua_path}"]
    params.append(f'Format="{format.value}"')
    
    return f"[Date({','.join(params)})]"


def build_number_token(
    path: str,
    source: TokenSource = TokenSource.ATTRIBUTE,
    prefix: Optional[str] = None,
    format: NumberFormat = NumberFormat.INTEGER,
) -> str:
    """
    Build a Kahua [Number(...)] token.
    
    Example: [Number(Source=Attribute,Path=Quantity,Format="N0")]
    
    Common formats:
        "N0" = Integer with commas (1,234)
        "F2" = Fixed 2 decimals (1234.56)
        "P1" = Percent with 1 decimal (45.5%)
    """
    kahua_path = to_kahua_path(path, prefix)
    
    params = [f"Source={source.value}", f"Path={kahua_path}"]
    params.append(f'Format="{format.value}"')
    
    return f"[Number({','.join(params)})]"


def build_rich_text_token(
    path: str,
    source: TokenSource = TokenSource.ATTRIBUTE,
    prefix: Optional[str] = None,
    text_format: Literal["HTML", "RTF"] = "HTML",
) -> str:
    """
    Build a Kahua [RichText(...)] token.
    
    Example: [RichText(Source=Attribute,Path=Description,TextFormat="HTML")]
    
    Use for rich text content. Default is HTML format.
    """
    kahua_path = to_kahua_path(path, prefix)
    
    params = [f"Source={source.value}", f"Path={kahua_path}"]
    if text_format != "HTML":
        params.append(f'TextFormat="{text_format}"')
    
    return f"[RichText({','.join(params)})]"


# =============================================================================
# List Token Builder
# =============================================================================

def build_attribute_list_token(
    path: str,
    attribute: str,
    delimiter: str = ", ",
    prefix: Optional[str] = None,
) -> str:
    """
    Build a Kahua [AttributeList(...)] token.
    
    Example: [AttributeList(Path=Companies,Delimiter=", ",Attribute=Company.ShortLabel)]
    
    Special delimiter "NEWLINE" inserts line breaks between items.
    """
    kahua_path = to_kahua_path(path, prefix)
    attr_path = to_kahua_path(attribute)
    
    return f'[AttributeList(Path={kahua_path},Delimiter="{delimiter}",Attribute={attr_path})]'


# =============================================================================
# Table Token Builders
# =============================================================================

def build_start_table_token(
    name: str,
    path: str,
    source: TokenSource = TokenSource.ATTRIBUTE,
    prefix: Optional[str] = None,
    rows_in_header: int = 1,
    show_empty_table: bool = False,
    sort_path: Optional[str] = None,
    sort_direction: str = "Ascending",
    where_path: Optional[str] = None,
    where_operator: Optional[ConditionOperator] = None,
    where_value: Optional[str] = None,
) -> str:
    """
    Build a Kahua [StartTable(...)] token.
    
    Example: [StartTable(Name=ItemsTable,Source=Attribute,Path=Items,RowsInHeader=1)]
    
    Args:
        name: Unique table name
        path: Path to collection (e.g., "Items", "Comments")
        source: Token source
        prefix: Entity prefix
        rows_in_header: Number of header rows (default 1)
        show_empty_table: Show table even if empty
        sort_path: Path for sorting
        sort_direction: "Ascending" or "Descending"
        where_path: Filter condition path
        where_operator: Filter operator
        where_value: Filter value
    """
    kahua_path = to_kahua_path(path, prefix)
    
    params = [f"Name={name}", f"Source={source.value}", f"Path={kahua_path}"]
    
    if rows_in_header != 1:
        params.append(f"RowsInHeader={rows_in_header}")
    
    if show_empty_table:
        params.append('ShowEmptyTable="True"')
    
    # Add Where clause if specified
    if where_path and where_operator:
        params.append(f"Where.Path={to_kahua_path(where_path)}")
        params.append(f"Where.Operator={where_operator.value}")
        if where_value is not None:
            params.append(f'Where.Value="{where_value}"')
    
    return f"[StartTable({','.join(params)})]"


def build_end_table_token() -> str:
    """Build [EndTable] closing token."""
    return "[EndTable]"


# =============================================================================
# List Output Token Builders
# =============================================================================

def build_start_list_token(
    name: str,
    path: str,
    source: TokenSource = TokenSource.ATTRIBUTE,
    prefix: Optional[str] = None,
    sort_path: Optional[str] = None,
    sort_direction: str = "Ascending",
) -> str:
    """
    Build a Kahua [StartList(...)] token for repeating content.
    
    Example: [StartList(Name=Items,Source=Attribute,Path=Meeting.MeetingItems)]
    """
    kahua_path = to_kahua_path(path, prefix)
    
    params = [f"Name={name}", f"Source={source.value}", f"Path={kahua_path}"]
    
    if sort_path:
        sort = f"{to_kahua_path(sort_path)},{sort_direction}"
        params.append(f"Sort={sort}")
    
    return f"[StartList({','.join(params)})]"


def build_start_content_template_token() -> str:
    """Build [StartContentTemplate] token for list item content."""
    return "[StartContentTemplate]"


def build_end_content_template_token() -> str:
    """Build [EndContentTemplate] token."""
    return "[EndContentTemplate]"


def build_end_list_token() -> str:
    """Build [EndList] closing token."""
    return "[EndList]"


# =============================================================================
# Conditional Token Builders
# =============================================================================

def build_if_token(
    path: str,
    operator: ConditionOperator = ConditionOperator.IS_NOT_EMPTY,
    value: Optional[str] = None,
    source: TokenSource = TokenSource.ATTRIBUTE,
    prefix: Optional[str] = None,
) -> str:
    """
    Build a Kahua [IF(...)] conditional token.
    
    Example: [IF(Source=Attribute,Path=Status,Operator=IsNotEmpty)]
    Example: [IF(Source=Attribute,Path=Status,Operator=Equals,Value="Approved")]
    """
    kahua_path = to_kahua_path(path, prefix)
    
    params = [f"Source={source.value}", f"Path={kahua_path}", f"Operator={operator.value}"]
    
    if value is not None and operator not in [
        ConditionOperator.IS_EMPTY, ConditionOperator.IS_NOT_EMPTY,
        ConditionOperator.IS_NULL, ConditionOperator.IS_NOT_NULL,
        ConditionOperator.IS_TRUE, ConditionOperator.IS_FALSE
    ]:
        params.append(f'Value="{value}"')
    
    return f"[IF({','.join(params)})]"


def build_then_token() -> str:
    """Build [THEN] token."""
    return "[THEN]"


def build_end_then_token() -> str:
    """Build [ENDTHEN] token."""
    return "[ENDTHEN]"


def build_else_token() -> str:
    """Build [ELSE] token."""
    return "[ELSE]"


def build_end_else_token() -> str:
    """Build [ENDELSE] token."""
    return "[ENDELSE]"


def build_end_if_token() -> str:
    """Build [ENDIF] token."""
    return "[ENDIF]"


# =============================================================================
# System/Metadata Token Builders
# =============================================================================

def build_company_logo_token(
    width: int = 100,
    height: int = 50,
) -> str:
    """Build [CompanyLogo(...)] token."""
    return f"[CompanyLogo(Width={width},Height={height})]"


def build_project_logo_token(
    width: int = 100,
    height: int = 50,
) -> str:
    """Build [ProjectLogo(...)] token."""
    return f"[ProjectLogo(Width={width},Height={height})]"


# System tokens (no parameters)
PROJECT_NAME_TOKEN = "[ProjectName]"
PROJECT_NUMBER_TOKEN = "[ProjectNumber]"
DOMAIN_PARTITION_NAME_TOKEN = "[DomainPartitionName]"
CONTRACT_NO_TOKEN = "[ContractNo]"
REPORT_MODIFIED_TIMESTAMP_TOKEN = "[ReportModifiedTimeStamp]"
PARTITION_TIMEZONE_ABBREVIATED_TOKEN = "[PartitionTimeZoneAbbreviated]"
CURRENT_TIMEZONE_ABBREVIATED_TOKEN = "[CurrentTimeZoneAbbreviated]"
USER_NAME_TOKEN = "[UserName]"


# =============================================================================
# Line Break Reduction Token
# =============================================================================

CONDITIONAL_LINEBREAK_TOKEN = "[?]"


def add_conditional_suffix(token: str) -> str:
    """Add [?] suffix to make content conditional (show only when field has value)."""
    return f"{token}{CONDITIONAL_LINEBREAK_TOKEN}"


# =============================================================================
# Signature Token Builders
# =============================================================================

def build_signature_token(
    path: str,
    width: int = 100,
    height: int = 50,
    attribute: Optional[str] = None,
    having_path: Optional[str] = None,
    having_operator: Optional[ConditionOperator] = None,
    having_value: Optional[str] = None,
    where_path: Optional[str] = None,
    where_operator: Optional[ConditionOperator] = None,
    prefix: Optional[str] = None,
) -> str:
    """
    Build a Kahua [Signature(...)] token for eSignature display.
    
    Basic: [Signature(Path=Signature,Width=100,Height=50)]
    
    With collection search (for approval workflows):
    [Signature(Path=ApprovalResults,Attribute=Signature,
               Having.Path=ApproverRole,Having.Value="Contract Signatory",Having.Operator=Equals,
               Where.Path=ApprovalPath,Where.Operator=IsNotNull,Width=100,Height=50)]
    """
    kahua_path = to_kahua_path(path, prefix)
    
    params = [f"Path={kahua_path}"]
    
    if attribute:
        params.append(f"Attribute={to_kahua_path(attribute)}")
    
    if having_path and having_operator:
        params.append(f"Having.Path={to_kahua_path(having_path)}")
        params.append(f"Having.Operator={having_operator.value}")
        if having_value:
            params.append(f'Having.Value="{having_value}"')
    
    if where_path and where_operator:
        params.append(f"Where.Path={to_kahua_path(where_path)}")
        params.append(f"Where.Operator={where_operator.value}")
    
    params.append(f"Width={width}")
    params.append(f"Height={height}")
    
    return f"[Signature({','.join(params)})]"


# =============================================================================
# Image Token Builder
# =============================================================================

def build_image_token(
    path: str,
    width: Optional[int] = None,
    height: Optional[int] = None,
    prefix: Optional[str] = None,
) -> str:
    """
    Build a Kahua [Image(...)] token for displaying uploaded images.
    
    Example: [Image(Path=Photo,Width=200,Height=150)]
    """
    kahua_path = to_kahua_path(path, prefix)
    
    params = [f"Path={kahua_path}"]
    
    if width:
        params.append(f"Width={width}")
    if height:
        params.append(f"Height={height}")
    
    return f"[Image({','.join(params)})]"


# =============================================================================
# Media Token Builder
# =============================================================================

def build_media_token(
    path: str,
    prefix: Optional[str] = None,
) -> str:
    """
    Build a Kahua [Media(...)] token for media galleries.
    
    Injects a table containing visual media elements.
    """
    kahua_path = to_kahua_path(path, prefix)
    return f"[Media(Path={kahua_path})]"


# =============================================================================
# Entity Hyperlink Token
# =============================================================================

def build_entity_hyperlink_token(label: str) -> str:
    """
    Build a Kahua [EntityHyperLink(...)] token.
    
    Creates a clickable link to navigate to the entity in Kahua.
    """
    return f'[EntityHyperLink(Label="{label}")]'


# =============================================================================
# WorkBreakdown Token Builders
# =============================================================================

def build_work_breakdown_token(
    cost_unit_names: List[str],
    source: TokenSource = TokenSource.PROJECT,
    path: Optional[str] = None,
) -> str:
    """
    Build a Kahua [WorkBreakdown(...)] token.
    
    Outputs currency summarizing cost units at project or WBS item level.
    
    Example: [WorkBreakdown(Source=Project,CostUnitNames="BudgetApproved,BudgetChangeApproved")]
    """
    cost_units = ",".join(cost_unit_names)
    
    params = [f"Source={source.value}"]
    if path:
        params.append(f"Path={to_kahua_path(path)}")
    params.append(f'CostUnitNames="{cost_units}"')
    
    return f"[WorkBreakdown({','.join(params)})]"


# =============================================================================
# Format Helper - Determine Token Type from Field Info
# =============================================================================

def build_field_token(
    path: str,
    field_type: str = "text",
    prefix: Optional[str] = None,
    format_options: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Build the appropriate Kahua token based on field type.
    
    This is a convenience function that routes to the correct token builder.
    
    Args:
        path: Field path
        field_type: One of: text, currency, number, decimal, percent, date, datetime, boolean, rich_text, image
        prefix: Entity prefix
        format_options: Additional format options (decimals, date_format, width, height, etc.)
    
    Returns:
        Formatted Kahua token string
    """
    opts = format_options or {}
    
    match field_type.lower():
        case "currency":
            fmt = CurrencyFormat(opts.get("format", "C2")) if opts.get("format") else CurrencyFormat.DEFAULT
            return build_currency_token(path, prefix=prefix, format=fmt)
        
        case "number" | "integer":
            return build_number_token(path, prefix=prefix, format=NumberFormat.INTEGER)
        
        case "decimal":
            decimals = opts.get("decimals", 2)
            fmt = NumberFormat(f"F{decimals}") if decimals else NumberFormat.FIXED_2
            return build_number_token(path, prefix=prefix, format=fmt)
        
        case "percent":
            decimals = opts.get("decimals", 1)
            fmt = NumberFormat(f"P{decimals}") if decimals else NumberFormat.PERCENT_1
            return build_number_token(path, prefix=prefix, format=fmt)
        
        case "date":
            date_fmt = opts.get("format", "d")
            fmt = DateFormat(date_fmt) if date_fmt in [e.value for e in DateFormat] else DateFormat.SHORT_DATE
            return build_date_token(path, prefix=prefix, format=fmt)
        
        case "datetime":
            return build_date_token(path, prefix=prefix, format=DateFormat.GENERAL_SHORT)
        
        case "boolean":
            return build_boolean_token(
                path, 
                prefix=prefix,
                true_value=opts.get("true_value", "Yes"),
                false_value=opts.get("false_value", "No"),
            )
        
        case "rich_text" | "richtext":
            return build_rich_text_token(path, prefix=prefix)
        
        case "image":
            return build_image_token(
                path,
                prefix=prefix,
                width=opts.get("width"),
                height=opts.get("height"),
            )
        
        case _:
            return build_attribute_token(path, prefix=prefix)
