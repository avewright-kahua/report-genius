Portable View Template Rendering - Architecture Summary
Overview
Portable Views in Kahua generate PDF documents from Word templates (.docx) by binding entity data to tokenized placeholders. The system uses Aspose.Words for document manipulation.

High-Level Rendering Flow
Key Components
Component	Responsibility
WordTemplateProcessor	Orchestrates the entire rendering; loads template, coordinates parsing/binding, outputs PDF
DocumentTemplateParser	Parses Word document, identifies tokens, builds DocumentTemplateTree
DocumentTemplateBinder	Binds entity data to tokens, replaces placeholders in document
DocumentTemplateTree	Hierarchical representation of document structure (root → container nodes → token nodes)
TemplateBindingFactory	Factory that resolves the correct TemplateTokenBinder for each token type
PortableViewTokenResolver	Resolves available tokens for a portable view based on entity defs and data sources
Document Tree Structure
Node Types:

ContainerNode - Base for repeating content (tables, lists)
TableNode - Word table bound to a collection (supports grouping, sorting)
ListNode - Repeating content with templates for content/header/empty states
AttributeNode - Single attribute binding
ImageNode, LogoNode, SignatureNode - Image bindings
CultureStringNode - Localized text
MetadataNode - System metadata (partition path, user, timestamps)
LiteralNode - Static formatted values (dates, currency literals)
ConditionalContainerNode, IfNode, ThenNode, ElseNode - Conditional rendering
Token Format
Tokens are bracket-delimited with optional parameters:

Core Token Types:

Token	Purpose
[Attribute(Path=X.Y)]	Bind entity attribute value
[StartTable(Path=Items)]...[EndTable]	Repeat table rows for collection
[StartList(Path=Items)]...[EndList]	Repeat content block for collection
[Currency(Path=Amount)]	Formatted currency value
[Date(Path=DueDate)]	Formatted date value
[CompanyLogo], [ProjectLogo]	Insert logo images
[Image(Path=Photo)]	Insert entity image
[Signature(Path=Sig)]	Insert signature image
[Culture(Key=Label.Name)]	Localized string
[DomainLabel], [UserName], [CurrentTime]	Metadata values
[TemplateTable(Name=X, Path=Y)]	Insert reusable table template part
[If(...)][Then]...[Else]...[EndIf]	Conditional sections
Container Parameters:

Path - Attribute path for data binding
Sort - Sort expression (e.g., Name:asc,Date:desc)
GroupBy, GroupTotal - Grouping/subtotals for tables
RowsInHeader - Header rows to preserve in table
Binding Process Detail
1. Container Resolution (Tables/Lists):

2. Attribute Resolution:

3. Text Replacement:
Main Document:
[TemplateTable(Name=LineItems, Path=Invoice.Lines)]

Template Part Document (LineItems):
[StartTable(Path=?)]
| Item | Qty | Price |
[EndTable]
Uses Aspose.Words.Range.Replace() with regex patterns and IReplacingCallback implementations for complex replacements (images, RTF, etc.).

Template Parts (Reusable Sub-Documents)
Template parts allow reusable table/list definitions stored separately:

The parser substitutes the template part inline and rebinds the Path parameter.

Example Token Resolution Flow
For [Attribute(Path=Issue.Number)]:

Parser creates AttributeNode with token
TemplateBindingFactory returns null (attribute binding handled later)
During binding, BinderHelper.ResolveContainerAttribute() navigates Issue.Number path on entity
Value retrieved and formatted
_templateDocument.Range.Replace() swaps token with value
Key Files Reference
File	Purpose
WordTemplateProcessor.cs	Main orchestrator for Word-based templates
DocumentTemplateParser.cs	Token parsing, tree building
DocumentTemplateBinder.cs	Data binding to parsed tree
DocumentTemplateTree.cs	Tree structure container
ContainerNode.cs, TableNode.cs, ListNode.cs	Container node types
AttributeNode.cs, ImageNode.cs, etc.	Token node types
TemplateBindingFactory.cs	Binder resolution factory
TextReplacementEvaluator.cs	Aspose.Words replacement callback
PortableViewTokenResolver.cs	Discovers available tokens for entity defs
This architecture allows Word templates to remain editable by non-developers while supporting complex data binding including nested collections, conditional content, images, and localization.