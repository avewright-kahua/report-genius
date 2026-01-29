# Overview

This document provides instructions for creating Kahua portable view document templates using Microsoft Word. These templates can be uploaded to application configurations for use in producing PDF output for applications, providing a simple means of customizing Kahua output.

# Background

Kahua portable view templates use a simple token replacement scheme whereby the given template document is specified for use as the document template, along with information concerning the entity that is to be used as the source of documentation information. The portable view processor takes this information and scans the template for these tokens, replacing the tokens with the appropriate content from the entity, or from application culture-specific resources.

# Token Pattern

All portable view tokens, utilize one of the following patterns:


**Simple Token**
`[TokenName(attributePath)]`

**Parameterized Token**
`[TokenName(parameter<sub>1</sub>=value<sub>1</sub>,parameter<sub>2</sub>=value<sub>2</sub>,parameter<sub>n</sub>=value<sub>n</sub>)\]`

**XML Token**
`@[<TokenXmlElement></TokenXmlElement>]`


## Simple and Parameterized Tokens
All simple and parameterized tokens are contained within square brackets `[]`.
Immediately following the opening bracket, the token type is identified.

Following the token type can be optional parameters (a parameterized token), which are contained within parenthesis and follow the pattern:

Parameter=value

If multiple parameters are utilized, parameter/value pairs are separated by commas.

If a comma is intended to be used as part of a parameter value, then the parameter value must be enclosed within double quotes. For example `[token(parameter1="hello,howareyou")]`

If a token does not contain a parameter=value content, it is considered a simple token and content within the parenthesis is assumed to designate an attribute path.


## XML Tokens
XML tokens are contained within `@[]` and must be valid XML matching a supported token definition.  Note that not all of the token types that comprise the word template portable view definitions currently support the use of XML tokens; see the description of the individual token types to determine if an XML token definition is supported.  This variation of token definition is used to define complex behaviors and is intended to be fully compatible to the Hub directive notation used in Kahua Hub app defs so as to provide a more consistent experience configuring Kahua over the various platform features.


# Token Types

The following token types are supported by portable view templates:

<table>
<thead>
<tr class="header">
<th><strong>Token Type</strong></th>
<th><strong>Description</strong></th>
<th><strong>Token Example</strong></th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>Culture Tokens</td>
<td>Culture tokens provide the ability to utilize the culture strings defined in apps for output in portable views, utilize the language of the current session for resolving the culture-specific token values. This provides some measure of internationalizing word templates.</td>
<td>[CultureTokenName]</td>
</tr>
<tr class="even">
  <td><p><u>Attribute Tokens</u></p>
<p>Attribute</p>
<p>Boolean</p>
<p>Currency</p>
<p>Date</p>
<p>Number</p>
<p>RichText<p>
</td>
<td><p>Attribute tokens provide the ability to output a specific attribute from the current entity. Generically the Attribute token can be used, however there are type specific tokens that provide the ability to utilize type specific formatting and behaviors when outputting the data.</p>
<p>There are also a variety of conditional and resolution capabilities that can be used over any of these attribute token types.</p></td>
<td>[Attribute(...)]<br />
[Boolean(...)]<br />
[Currency(...)]<br />
[Date(...)]<br />
[Number(...)]<br/>
[RichText(...)]<br/>
</tr>
<tr class="odd">
<td>Attribute List Token</td>
<td>The attribute list token provides the ability to output a list of entities as a delimited string, outputting specific attributes of each entity in the list.</td>
<td>[AttributeList(...)]</td>
</tr>
 <tr class="odd">
   <td>WorkBreakdown Token</td>
   <td>The WorkBreakdown token will provide a currency output summarizing a set of specified cost units at the project or ambient work breakdown item level</td>
   <td>[WorkBreakdown(...)]</td>
</tr>
 <tr class="odd">
   <td>WorkBreakdownSegmentValue Token</td>
   <td>The WorkBreakdownSegmentValue token will provide text output showing the value of the requested wbs segment value from the wbs code for the given work breakdown item</td>
   <td>[WorkBreakdownSegmentValue(...)]</td>
</tr>
<tr class="odd">
<td>Image Token</td>
<td>The Image token provides the ability to output an image via an uploaded file stored at a given attribute path on an entity.</td>
<td>[Image(...)]</td>
</tr>
   
<tr class="even">
  <td><p><u>Literal Tokens</u></p>
    <p>Currency</p>
<p>Date</p>
<p>Number</p></td>
<td>Literal tokens provide the ability to output fixed literal data for specific data types, including things such as currency symbols, formatting, and computed offsets (with dates).</td>
<td>[Currency(...)]<br />
[Date(...)]<br />
[Number(...)]</td>
</tr>
<tr class="odd">
<td>eSignature Token</td>
<td>The eSignature token provides the ability to output the content of a Kahua eSignature image and text and control the layout and content in the document.</td>
<td>[Signature(...)]</td>
</tr>
<tr class="even">
<td>Docusign Signature Control Tokens</td>
<td>The Docusign signature control tokens provide the ability to define the location within portable view templates where Docusign will display the tags for attaching signature, initial, and date information when the portable view document is used in a Docusign workflow.</td>
<td>[Signature(...)]<br />
[DocuSign(...)]</td>
</tr>
<tr class="odd">
<td>Logo Token</td>
<td>The Logo token provides the ability to output the current company and/or project logo in effect for the current app and project.</td>
<td>[CompanyLogo(...)]</td>
</tr>
<tr class="even">
<td>Domain Metadata Tokens</td>
<td>Domain metadata tokens provide the ability to output specific information about the current domain.</td>
<td>[DomainPartitionPath]</td>
</tr>
<tr class="odd">
<td>Partition Metadata Tokens</td>
<td>Partition metadata tokens provide the ability to output specific information about the current partition or project.</td>
<td>[PartitionTimeZoneLong]</td>
</tr>
<tr class="odd">
<td>Project Metadata Tokens</td>
<td>Project metadata tokens provide the ability to output specific information about the current project. The available project metadata tokens are dynamic as it is tied to the type of project extension in use for a domain, such as with portfolio manager.</td>
<td>[ProjectNumber]</td>
</tr>
<tr class="even">
<td>Time Zone Tokens</td>
<td>Time zone tokens provide the ability to output specific date/time and time zone information in a document.</td>
<td>[CurrentTimeZoneAbbreviated]</td>
</tr>
<tr class="odd">
<td>User Token</td>
<td>The user token provides the ability to output the current user within a document.</td>
<td>[UserName]</td>
</tr>
<tr class="even">
<td>Time Stamp Token</td>
<td>The time stamp token provides the ability to output the current system timestamp within a document.</td>
<td>[ReportModifiedTimeStamp]</td>
</tr>
<tr class="odd">
<td>Media Token</td>
<td>The Media token will inject a table containing the visual media elements stored in the media attribute specified.</td>
<td>[Media(...)]</td>
</tr>
<tr class="even">
<td>Table Output Tokens</td>
<td>Table output tokens provide the ability to output a list of entities with their designated attributes within a Word table. These tables can also optionally include summation and grouping of data rows in the table based upon a set of grouping attributes.  Table output tokens support both the parameterized token definition and XML token definition, enhanced features are available when using the XML token definition not available in the parameterized token definition</td>
<td><p>[StartTable(...)]</p>
<p>[EndTable]</p>
 <p>@[&lt;StartTable&gt;] @[&lt/StartTable&gt;] @[&lt;EndTable/&gt;]</p></td>
</tr>
<tr class="odd">
<td>List Output Tokens</td>
<td>List output tokens provide the ability to output a list of entities with their designated attributes within repeating sections of content.</td>
<td>[StartList(...)]<br />
[EndList]</td>
</tr>
<tr class="even">
<td>Conditional Tokens</td>
<td>Conditional tokens allow for IF/THEN/ELSE logic to be defined within a template for control of conditional output based upon entity attribute data conditions.</td>
<td>[IF(...)]<br />
[THEN]<br />
[ENDTHEN]<br />
[ELSE]<br />
[ENDELSE]<br />
[ENDIF]</td>
</tr>
<tr class="odd">
<td>Entity Hyperlink Token</td>
<td>The Entity Hyperlink token inserts a hyperlink with the given label that when clicked in the rendered document will execute navigation to the app and document in Kahua.</td>
<td>[EntityHyperLink(Label=label)]</td>
</tr>

<tr class="odd">
<td>Line Break Reduction Token</td>
<td>The line break reduction token will remove the newline from the generated document, if possible.</td>
<td>[?]</td>
</tr>
</tbody>
</table>

# Token Source (Parameter)
Many of the token types support an optional parameter called Source.
The Source parameter is used to designate the source of the entity data the token will operate over.  The following table defines the possible values and uses of the Source parameter:

<table>
  <thead>
    <tr class="header">
      <th><strong>Source</strong></th>
      <th><strong>Description</strong></th>
      <th><strong>Usage</strong></th>
    </tr>
  </thead>
  <tbody>
    <tr class="odd">
      <td>None<br/><br />Attribute</td>
      <td>Designates the token will operate against the current entity, this is the default if not specified.</td>
      <td>Attribute, Boolean, Currency, Date, Number, AttributeList, Signature, StartTable, StartList, and IF tokens</td>
    </tr>
    <tr class="even">
      <td>Project</td>
      <td>Designates the token will operate against the current project the current entity is contained within.  Note that this Source option allows for the replacement of the <a name="#Project-Metadata-Tokens">Project Metadata Tokens</a> with the equivalent expression using the various tokens that support this source.</td>
      <td>Attribute, Boolean, Currency, Date, Number, AttributeList, Signature, StartTable, StartList, and IF tokens</td>
    </tr>
    <tr class="odd">
      <td>Literal</td>
      <td>Designates the token is rendering a literal value, this is an implicit source used with the various literal tokens Boolean, Currency, Date, and Number</td>
      <td>Literal Boolean, Currency, Date, and Number tokens</td>
    </tr>
    <tr class="even">
      <td>Chronology</td>
      <td>Only valid as Source parameter on StartTable tokens, this designates the content of the table to contain the chronology entries for the given entity.</td>
      <td>Table tokens only</td>
    </tr>
    <tr class="odd">
      <td>StepHistory</td>
      <td>Only valid as Source parameter on StartTable tokens, this designates the content of the table to contain the workflow step history for the given entity.</td>
      <td>Table tokens only</td>
    </tr>
    <tr class="even">
      <td>Collection
      (2026.1 Release)
      </td>
      <td>
        <p>
        Indicates that the token will try to resolve an entity at a given index located within an entity collection.<br/>
        The entity collection is designated by the Collection.Path argument which is the path to the collection on the current entity.<br/>
        The Collection.Index argument indicates which entity in the collection is used.  The Index value can be First, Last, or a number within the size of the collection.  This is a 1's based index.  In the event that an Index outside the bounds of the collection is given, no output is generated for the token. <br/>The Collection.Sort argument is optional sort criteria that will sort the collection by the given criteria and then apply the Index to find the requested entity.
      <br/>Example: 
        </p>
        <p>
      [Attribute(Source=Collection,Collection.Path=ApprovalResults,Collection.Index=2,Path=ApproverRole)]<br/><br />
       The attribute token above reaches into the ApprovalResults collection on the current entity and gets the 2nd entity in the collection and then outputs the value of the ApproverRole attribute on that entity.
        </p>
      </td>
      <td>All attribute tokens (Attribute,Date,Boolean,Currency,Number,RichText,AttributeList,Signature)</td>
    </tr>
  </tbody>
</table>


# Token Conditional Parameters
Many of the portable view tokens provide optional parameters to control for conditional output of the token content or of the set of data the token will operate over, in the case of the table and list tokens.  The capabilities of the token conditional features have been enhanced over time, so this document section covers the general differences and capabilities of the conditional features which are shared over multiple token types.  The descriptions of the individual token conditional behaviors will refer back to this section.

## Legacy Conditionals
The Legacy conditionals refer to conditional usages in portable view tokens that rely upon the use of the simple, single conditional expressions and are employed on the IF, StartTable, StartList, and attribute family of tokens as follows:

- \[IF(Path=\<path>,Operator=\<operator>,Value=\<value>...)]
- \[StartTable(Path=\<path>,Where.Path=\<path>,Where.Operator=\<operator>,Where.Value=\<value>...)]
- \[StartList(Path=\<path>,Where.Path=\<path>,Where.Operator=\<operator>,Where.Value=\<value>...)]
- \[Attribute(Path=\<path>,VisibleWhen=\<operator>,Value=\<value>,VisibleWhenPath=\<path>...)]
- \[Attribute(Path=\<path>,Where.Path=\<path>,Where.Operator=\<operator>,Where.Value=\<path>...)]
- \[Attribute(Path=\<path>,Where.Path=\<path>,Where.Operator=\<operator>,Where.Value=\<path>,Having.Path=\<path>,Having.Operator=\<operator>,Having.Value=\<value>)]

See the individual token sections for their descriptions.  All of the above conditional usage patterns only support a single condition, and the condition is evaluated to true if the expression resolves where the value of the attribute in *Path* with the operator applied in *Operator* compared to the value in *Value* (if applicable to the operator) is true.  

The set of operators supported for these legacy conditions are described below:

### Operators
Various tokens support the use of an Operator parameter which designates
an operation to perform for a comparison. The following operators are
supported:

| **Operator**           | **Description**                                                                  |
| ---------------------- | -------------------------------------------------------------------------------- |
| Equals                 | Values compared are equal.                                                       |
| DoesNotEqual           | Values compared are not equal.                                                   |
| Contains               | Value compared contains the comparison value.                                    |
| DoesNotContain         | Value compared does not contain the comparison value.                            |
| In                     | Value compared is in the list of comma separated values. For example: "a,b,c,d". |
| IsGreaterThan          | Value compared is greater than comparison value.                                 |
| IsGreaterThanOrEqualTo | Value compared is greater than or equal to comparison value.                     |
| IsLessThan             | Value compared is less than comparison value.                                    |
| IsLessThanOrEqualTo    | Value compared is less then or equal to comparison value.                        |
| IsEmpty                | Value compared is empty.                                                         |
| IsNotEmpty             | Value compared is not empty.                                                     |
| IsNull                 | Value compared is null.                                                          |
| IsNotNull              | Value compared is not null.                                                      |
| IsTrue                 | Value compared is true.                                                          |
| IsFalse                | Value compared is false.                                                         |
| ContainedIn            | List of comma separated values are compared to the comparison value and if any of the values contains the comparison value, the condition is TRUE, otherwise FALSE. For example IF(Path=Test,Operator=ContainedIn,Value=a,b,c,d) - if Test contains a, b, c, or d, the condition is TRUE.
| NotContainedIn         | List of comma separated values are compared to the comparison value and if any of the values contains the comparison value, the condition is FALSE, otherwise TRUE. For example IF(Path=Test,Operator=NotContainedIn,Value=a,b,c,d) - if Test does not contain a, b, c, or d, the condition is TRUE.



## Hub Conditionals

Hub Conditionals refer to a newer set of conditional expressions that are used in the Kahua Hub "language" for app building and provide a means of using conditional expressions that are consistent with those used in other app building and report writing development, so reflect an effort to make the various features of Kahua operate in a consistent manner.

The guide referenced here ([Conditionals](/Partners/kBuilder/Guides/Conditionals)) provides a description of all of the various hub conditional features, please consult the Conditionals guide for details on Hub conditionals.

All of the aforementioned tokens in the Legacy Conditionals section also support the use of Hub Conditionals through the use of different parameters in the token definitions.  Hub Conditionals allow the specification of complex and multiple conditional statements in a single expression, thereby allowing complex conditions to be used in portable view output determination.

- \[IF(Conditions=@(*\<hub conditionals>*),...)]
- \[StartTable(Path=\<path>,Where.Conditions=@(*\<hub conditionals>*),...)]
- \[StartList(Path=\<path>,Where.Conditions=@(*\<hub conditionals>*),...)]
- \[Attribute(Path=\<path>,VisibleWhen.Conditions=@(*\<hub conditionals>*),...)]
- \[Attribute(Path=\<path>,Where.Conditions=@(*\<hub conditions>*),...]
- \[Attribute(Path=\<path>,Where.Conditions=@(*\<hub conditions>*),Having.Conditions=@(*\<hub conditions>*),...)]

All portable view tokens that support Hub Conditionals use the parameter format Conditions=@(*\<hub conditional expression>*) where the *\<hub conditional expression>* is an XML formatted string containing the hub conditional expression to be evaluated.  If the condition is evaluated to true, the token output is generated, if evaluated to false, the token output is suppressed.

The following example below demonstrates an IF token that will evaluate an entity and compare its ContractType attribute value to "Commercial" and its CostItemsTotalTotalValue to $1M, outputing the IF condition content if the document is a Commercial contract greater than $1M, otherwise outputing the content in the ELSE condition content.

---
\[IF(Source=Attribute,Conditions=@(
     \<AllOf>
           \<Data Path="ContractType" Type="EqualTo" Value="Commercial"/>
           \<Data Path="CostItemsTotalTotalValue" Type="GreaterThan" Value="1000000" />
      \</AllOf>))]
\[THEN]
word content for Commercial contract > $1M 
\[ENDTHEN]
\[ELSE]
word content for Commercial contract <= $1M
\[ENDELSE]
\[ENDIF]

> Note that in the @(...) expression, no paragraph breaks are permitted.
{.is-info}


---

# Token Descriptions and Usages

## Culture Tokens

Culture tokens retrieve the value of a culture resource identified by the token name from the current application and culture, outputting the culture-specific string resolved for the culture token. This is the same way that culture tokens are used in the Kahua user interface.

### Usage

All culture tokens are specified using the format \[tokenname\].

### Examples

Application culture resource named MeetingSubject:

App Def:
```XML
<Culture Code="en">
<Labels>
<Label Key=MeetingSubject>Meeting Subject:</Label>
```

Template Content:

`[MeetingSubject]`

Template Output:

`Meeting Subject:`

## Attribute Tokens

Attribute tokens will display the value of the referenced attribute. There is both a generic attribute token, as well as strongly typed
attribute tokens, all of which support the same set of parameters.

### Usage

  - \[Attribute(...)\] is the generic attribute token.

  - \[Boolean(...)\] will output the attribute as a Boolean value.

  - \[Currency(...)\] will output the attribute as a currency value.

  - \[Date(...)\] will output the attribute as a date/time value.

  - \[Number(...)\] will output the attribute as a numeric, non-currency value.
  
  - \[RichText(...)\] will output the attribute as rich text content, if the underlying content is some form of rich text.
  
All the tokens above accept the following parameters:

| **Parameter**             | **Description**                                                                                                                                             |
| ------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Source=\<source\>         | See the prior section titled Token Source (Parameter).  For the purposes of the attribute tokens, the value Attribute indicates the token operates on the current entity, the value Project indicates the token operates on the project the current entity is contained within.                 |
| Path=\<attribute path\>   | this is the path to the attribute on the entity.                                                                                                            |
| VisibleWhen=\<condition\> | this is a condition used in conjunction with the Value parameter, if the condition requires a value comparison, such as Equals.                             |
| VisibleWhenPath=\<attribute path\>   | optional path to obtain the value used for evaluating the VisibleWhen condition.  If not specified, the Path is used. | 
| Value=\<value\>           | the value to use with the VisibleWhen condition.                                                                                                           |
| VisibleWhen.Conditions=@(*\<hub conditionals>*)  | optional conditional expression using Hub Conditions.  See the [Hub Conditionals](/Partners/kBuilder/Guides/PortableView/CreatingPortableViewTemplates#hub-conditionals) section above. | 
| VisibleValue=\<value\>    | a value that can optionally be substituted for the attribute value if the VisibleWhen condition evaluates to true.                                          |
| DefaultValue=\<value\>    | a default value that can be optionally substituted for the attribute value if the VisibleWhen condition evaluates to false.                                 |
| LeftTruncate=\<length\>   | the length to truncate from the left of the attribute value. If longer than the current attribute length in characters, then all characters are truncated.  |
| RightTruncate=\<length\>  | the length to truncate from the right of the attribute value. If longer than the current attribute length in characters, then all characters are truncated. |
| PrependText=\<text\>      | text to prepend to the left of the attribute value.                                                                                                         |
| AppendText=\<text\>       | text to append to the right of the attribute value.                                                                                                         |
| Where Parameters          | See the following discussion on where and resolve parameters                                                                                                |
| Resolve Parameters        | See the following discussion on where and resolve parameters                                                                                                |

#### Boolean Token Parameters
The \[Boolean()\] token utilizes the following parameters to control its output:

| **Parameter**       | **Description**                                                 |
| ------------------- | --------------------------------------------------------------- |
| TrueValue=\<text\>  | the text to output for a true Boolean attribute value.          |
| FalseValue=\<text\> | the text to output for a false Boolean attribute value.         |
| EmptyValue=\<text\> | the text to output for a null or empty Boolean attribute value. |

Note that for Boolean type tokens, a frequent requirement is to output checkbox-like content in the portable content, such as:

Option 1: ☒
Option 2: ☐
Option 3: ☐

This type of content can be achieved by using special characters from the various "Symbol" type fonts available in Word and employing these as the TrueValue, FalseValue arguments to the boolean token.  

For example:

[Boolean(Source=Attribute,Path=Contract.DisciplineArchitectural,TrueValue=☒,FalseValue=☐)] Architectural

Would yield the output:
☒ Architectural - for a True value.



#### Date/Number Token Shared Parameters
The \[Date()\] and \[Number()\] tokens both support the
use of a Format parameter:

| **Parameter**     | **Description**                                         |
| ----------------- | ------------------------------------------------------- |
| Format=\<format\> | the .NET format specifier for the underlying data type. |

#### Currency Token Parameters

For Currency attributes the system will the ambient culture currency format based upon the document currency or specified currency type (see below). The Format parameter can optionally utilize a special format specifier that will substitute the currency value with the equivalent words to express the currency amount. For example, if the currency value is $300.00, the following special formats would output the following content:

| **Format=?** | **Output for $300.00**               |
| -------------- | ------------------------------------ |
| WordsMixedCase | Three Hundred Dollars And Zero Cents |
| WordsUpperCase | THREE HUNDRED DOLLARS AND ZERO CENTS |
| WordsLowerCase | three hundred dollars and zero cents |

The \[Currency()\] token also supports the designation of the currency type to use for output of the currency symbol and amount based upon the project settings for exchange rates.  The following parameters can be optionally used to employ multi-currency aware output of currency data:

<table>
<thead>
<tr class="header">
<th><strong>Parameter</strong></th>
<th><strong>Description</strong></th>
</tr>    
</thead>
<tbody>
<tr class="odd">
<td>CurrencyType=&lt;currencytype&gt;</td>
<td>&lt;currencytype&gt; may be one of the following values:       

- Document	The currency symbol and amount are output in the document currency as set on the document, or cost item, if supported by the app.  This is the default if not specified.
- Project	The currency symbol and amount are output in the project currency.
- Domain		The currency symbol and amount are output in the domain currency.
      
Note that if no CurrencyType parameter is specified, this defaults to the Document currency type.  Also note that some cost apps support the designation of a currency type at the item level, so this allows for the use of different currency types per item in a cost app (such as a funding budget).  For example, the budget may be in USD at the document level, but item 1 is in CAD, item 2 in USD, and item 3 in GPB.  If the PV uses the default \[Currency()\] token behavior without specifying a CurrencyType in the items output, this will output the item values in their respective currency as a set of each item.  If the requirement were to normalize this to say the project currency, the PV designer would want to designate the CurrencyType=Project for the item currency tokens to get a normalized output to a single project currency.
</td>
</tr>    
</tbody>
</table>

> Note that the Currency token does not support the use of the standard .Net Format specifiers for currency.  The output rules for the resolved currency type will always be utilized.
{.is-info}

#### RichText Token Parameters
The RichText token is provided for optional backward capability with various legacy rich text content formats supported by Kahua.
By default, any text type attribute in Kahua can potentially contain rich text content and is assumed to provide HTML formatted rich text content, if present.  Some older implementations could provide a strict Wordpad RTF content for rich text which is of a much more limited set of layout abilities and content and can be incompatible with HTML format rich text.  If an app provide rich text content, in most cases the use of the \[Attribute(...)\] token is adequate to correctly render rich text output within the document.  However in rare cases where older, legacy information was captured, the RichText token can be used to provide fallback to legacy RTF.

<table>
<thead>
<tr class="header">
<th><strong>Parameter</strong></th>
<th><strong>Description</strong></th>
</tr>    
</thead>
<tbody>
<tr class="odd">
<td>TextFormat=&lt;format&gt;</td>
<td>&lt;format&gt; may be one of the following values:       

- RTF	The rich text content is WordPad RTF formatted.
- HTML	The rich text content is HTML formatted.  This is the default.
- Default/Undefined		Same as HTML.

Note that if no TextFormat parameter is specified, this defaults to the HTML text format.
</td>
</tr>    
</tbody>
</table>



#### Where and Resolve Operations

An advanced feature of the attribute tokens (this is also supported by the Signature token) is the use of Where or Resolve operations to conditionally find and display data in a portable view.

The Where feature is a set of parameters that act as a simple Boolean condition that if it evaluates to true, the data resolved in the Path parameter will be output in the document. If the value resolves to false, nothing is output.

The Resolve feature uses the same Where parameters, but also adds in Having parameters and a subsidiary attribute parameter which allows for a correlated search of child entities in a structure to resolve conditions matching in the Having and Where conditions. If both conditions evaluate to true, then a match is found, and the given Attribute content is output. This can be used to output data from a collection matching collection rows to specific values, such as a list of signatures by specific roles.

Note that the Where and Resolve features both support the use of single condition legacy expressions as well as multi-condition Hub Conditionals through the use of the appropriate parameters.


| **Parameter**                | **Description**                                                                                                                                                         |
| ---------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Where.Path=\<path\>          | The path to the attribute to use in the Where comparison.                                                                                                               |
| Where.Operator=\<operator\>  | The operator to use when comparing the Where.Path value to the Where.Value value. If a non-value comparison is used (such as IsNotNull), no Where.Value is required.    |
| Where.Value=\<value\>        | The value to compare the Where.Path value against, if the Where.Operator requires a comparison value.                                                                   |
| Where.Conditions=@(*\<hub conditionals>*)  | Optional Hub Conditional expression that can be used for complex conditions.  See the [Hub Conditionals](/Partners/kBuilder/Guides/PortableView/CreatingPortableViewTemplates#hub-conditionals) section above. | 

| Having.Path=\<path\>         | The path to the attribute to use in the Having comparison, this is relative to the path in the Path parameter.                                                          |
| Having.Operator=\<operator\> | The operator to use when comparing the Having.Path value to the Having.Value value. If a non-value comparison is used (such as IsNotNull), no Having.Value is required. |
| Having.Value=\<value\>       | The value to compare the Having.Path value against, if the Having.Operator requires a comparison value.                                                                 |
| Having.Conditions=@(*\<hub conditionals>*)  | Optional Hub Conditional expression that can be used for complex conditions.  See the [Hub Conditionals](/Partners/kBuilder/Guides/PortableView/CreatingPortableViewTemplates#hub-conditionals) section above. | 
| Attribute=\<attributepath\>  | The path to the attribute output for the token results, if the Having and Where comparisons evaluate to true.                                                           |

For example, the following token will output the Signature attribute image from a collection called ApprovalResults where the ApprovalRole is "Contract Signatory" and there is a non-null ApprovalPath.

```
[Signature(Path=ApprovalResults,Attribute=Signature,
Having.Path=ApproverRole,Having.Value="Contract Signatory",Having.Operator=Equals,
Where.Path=ApprovalPath,Where.Operator=IsNotNull,Width=100,Height=50)]`
```

To break this down, here is what is happening:

<table>
<thead>
<tr class="header">
<th><strong>Parameter</strong></th>
<th><strong>Description</strong></th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>Path=ApprovalResults</td>
<td>This tells the token to read from the ApprovalResults attribute on the main document entity (e.g. the contract).  This is the collection of approvals captured so far.</td>
</tr>
<tr class="even">
<td><p>Having.Path=ApproverRole</p>
<p>Having.Value="Contract Signatory"</p>
<p>Having.Operator=Equals</p></td>
<td>The Having.* parameters are used together to search the collection of entities in the ApprovalResults collection for a given attribute name with a given attribute value, and using the given comparison operator.  In this case, we are searching ApprovalResults and reading the ApproverRole attribute (Path) to find where the Value is "Contract Signatory" (one of our roles) and in this case we are using the Equals operator == so find an entity in ApprovalResults where the ApproverRole="Contract Signatory".</td>
</tr>
<tr class="odd">
<td><p>Where.Path=ApprovalPath</p>
<p>Where.Operator=IsNotNull</p></td>
<td>The Where.* parameters have the same set of arguments as the Having (Path, Value, Operator).  In the example shown above, we are simply looking at the ApprovalPath attribute and verifying it is not null.  This also supports a more complex use case where if there were nested entities under the Having path above, you could use this to find an entity that has a child entity with a given attribute value.  We don't need that for this situation, so this is the simplest way to define the Where.<br />
</td>
</tr>
<tr class="even">
<td>Attribute=Signature</td>
<td>The Attribute parameter tells the token that if the Having and Where clauses resolve an entity from the ApprovalResults, output the given attribute name.  In this example, if we find an entity in the ApprovalResults where ApproverRole="Contract Signatory" AND the ApprovalPath is not null, then we will output the Signature attribute which would be the signature stamp entity with the signature image and other information.</td>
</tr>
</tbody>
</table>

This allows for searching of a collection for a child entity Having the given path with value that matches by the operator AND where the child entity has another path with value matching by the operator.

A simpler example would be the use of the Where feature to conditionally output an attribute based upon a condition on a different attribute, as follows:

`[Attribute(Path=PurchaseOrderItem.ShortLabel,Where.Path=InvoiceItemOrigin,Where.Operator=Equals,Where.Value="POITEM"]`

`[Attribute(Path=PurchaseOrderChangeOrderItem.ShortLabel,Where.Path=InvoiceItemOrigin,Where.Operator=Equals,Where.Value="POCOITEM"]`

In the example above, the Where.Path is comparing the value of the InvoiceItemOrigin attribute to see if it is equal to either "POITEM" or "POCOITEM". If it is "POITEM", it outputs the value in the attribute for the path PurchaseOrderItem.ShortLabel (the description of the PO Item). Otherwise if the InvoiceItemOrigin attribute value is "POCOITEM", it will output the value in the attribute for the path
PurchaseOrderChangeOrderItem.ShortLabel.

The main difference in usage between the Where feature and the Resolve feature (Having and Where) is that the Where feature is comparing attribute values on the same entity, whereas in the Resolve usage this is searching child entities in an attribute on a parent entity and finding a child entity matching conditions and output the value of an attribute from the collection of child entities.

### Examples

Example of a simple attribute with a VisibleWhen clause, including prepended and appended text.

Template Content:

`[Attribute(Path=Meeting.Subject,VisibleWhen=IsNotEmpty,PrependText="AA",AppendText="BB")\]`

Template Output:

`AA Planning Session BB`

Example of a Boolean attribute with true/false/empty specified

Template Content:

 **Did meeting occur?** `[Boolean(Path=Meeting.WasHeld,TrueValue="Yes",FalseValue="No",EmptyValue="IDK")\]`

Template Output:

**Did meeting occur?** Yes 

Example of a Currency attribute using different formatted outputs:

Template Content:

```
Meeting Cost: [Currency(Path=Meeting.Cost)]
Maximum Cost: [Currency(Value=500)]
Meeting Cost: [Currency(Path=Meeting.Cost,Format="WordsLowerCase")]
Meeting Cost: [Currency(Path=Meeting.Cost,Format="WordsUpperCase")]
Meeting Cost: [Currency(Path=Meeting.Cost,Format="WordsMixedCase")]
```

Template Output:

```
Meeting Cost: $300.00
Maximum Cost: $500.00
Meeting Cost: three hundred dollars and zero cents
Meeting Cost: THREE HUNDRED DOLLARS AND ZERO CENTS
Meeting Cost: Three Hundred Dollars And Zero Cents
```

## Literal Tokens

Literal tokens will output the literal typed value specified for the token. These tokens are comprised of:

```
[Number(Value=value)]  
[Currency(Value=value)]  
[Date(Offset=#,Format=format)]
```

The Number and Currency tokens will output the literal value specified in their Value parameters, using the current culture formatting rules.

The Date token will output the current date/time for the current company domain and can optionally apply a day offset as well as output the resulting date in a given format.

### Usage

| **Parameter**     | **Description**                                                                    |
| ----------------- | ---------------------------------------------------------------------------------- |
| Value=\<value\>   | Literal value to output                                                            |
| Offset=\<\#\>     | Optional offset amount in days to apply to current date.                           |
| Format=\<format\> | Optional date format                                                               |

### Examples

| **Template Content:**             | **Template Output:** |
| --------------------------------- | -------------------- |
| \[Number(Value=10)\]              | 10                   |
| \[Currency(Value=1000)\]          | $1,000.00            |
| \[Date(Source=Current)\]          | 10/23/2020 05:23 PM  |
| \[Date(Source=Current,Offset=5)\] | 10/28/2020 05:23 PM  |

## Attribute List Token

The AttributeList token retrieves the set of entities on the given Path parameter, iterating over the set of entities, and outputting the value of the attribute in the Attribute argument path from each entity, inserting the delimiter specified in the Delimiter argument.

The Delimiter parameter supports a special value "NEWLINE" which will insert a soft line break between items in the list. If the Delimiter parameter is not specified, a comma (",") will be used as the default delimiter.

### Usage

`[AttributeList(Path=attribute path,Delimiter="delimiter",Attribute=entity attribute name)]`

### Examples

Template Content:

`[AttributeList(Path=Companies.Options,Delimiter=", ",Attribute=ShortLabel)]`

Template Output:

`Option1,Option2,Option4`

Template Content:

`[AttributeList(Path=Companies.Options,Delimiter= "NEWLINE",Attribute=ShortLabel)]`

Template Output:

```
Option1
Option2
Option4
```
## WorkBreakdown Token
The WorkBreakdown token is used to output a currency value that summarizes the total amount using the specified cost units at either the project level or for the designated workbreakdown item, based upon the parameters specified.


### Usage

`[WorkBreakdown(Source=Project,CostUnitNames="BudgetApproved,BudgetChangeApproved,BudgetAdjustmentApproved")]`
`[WorkBreakdown(Source=Attribute,Path=WorkBreakdownItem,CostUnitNames="contractApproved,ChangeChangeOrderApproved")]`

| **Parameter**             | **Description**                                                                                                                                             |
| ------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Source=\<source\>         | See the prior section titled Token Source (Parameter).  For the purposes of the WorkBreakdown token, the value Attribute indicates the token operates on the current entity with respect to a referenced WorkBreakdownItem, the value Project indicates the token operates on the project summary level for WorkBreakdown, over all work breakdown items.                 |
| Path=\<attribute path\>   | this is the path to the WorkBreakdownItem attribute on the entity.  This parameter is only used if Source=Attribute |
| CostUnitNames=\<cost unit names\> | The comma separated list of cost units that are summed together for either the specified WorkBreakdownItem or at the project level to report the WorkBreakdown summarized value |


### Examples

| **Template Content:**             | **Template Output:** |
| --------------------------------- | -------------------- |
| \[WorkBreakdown(Source=Project,CostUnitNames="BudgetApproved,BudgetChangeApproved,BudgetAdjustmentApproved")\]              | $1,000,000.00   |
| \[WorkBreakdown(Source=Attribute,Path=WorkBreakdownItem,CostUnitNames="ContractApproved,ContractChangeOrderApproved")\] | $1,000.00       |

## WorkBreakdownSegmentValue Token (2026.1 release)
The WorkBreakdownSegmentValue token is used to output the text value of the requested segment value from the requested work breakdown item.  The segment can be referenced by either its ordinal location in the code or via the label assigned to the segment in work breakdown configuration.


### Usage

`[WorkBreakdownSegmentValue(Source=Attribute,Path=WorkBreakdownItem,Segment.Ordinal=1)]`
`[WorkBreakdownSegmentValue(Source=Attribute,Path=WorkBreakdownItem,Segment.Label="Cost Type")]`

| **Parameter**             | **Description**                                                                                                                                             |
| ------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Source=\<source\>         | See the prior section titled Token Source (Parameter).  For the purposes of the WorkBreakdown token, the value Attribute indicates the token operates on the current entity with respect to a referenced WorkBreakdownItem               |
| Path=\<attribute path\>   | this is the path to the WorkBreakdownItem attribute on the entity. |
| Segment.Ordinal           | The 1's based location of the segment in the work breakdown segment configuration. |
| Segment.Label             | The label assigned to the segment in the workbreakdown segment configuration, this resolves the ordinal position. |

### Examples

| **Template Content:**             | **Template Output:** |
| --------------------------------- | -------------------- |
| \[WorkBreakdownSegmentValue(Source=Attribute,Path=WorkBreakdownItem,Segment.Ordinal=1)\]          | 1A113   |
| \[WorkBreakdownSegmentValue(Source=Attribute,Path=WorkBreakdownItem,Segment.Label="Cost Type")\]  | LAB     |



## EntityHyperlink Token
The EntityHyperlink token is used to embed a navigable link within the generated document that when clicked will navigate to Kahua to the designated app and document for the current entity.  The hyperlink is displayed with an optional Label as the text and embeds the URL to the document within Kahua.  If no label parameter is specified, the label content defaults to "Open In Kahua".

### Usage
`[EntityHyperlink(Label=label)]`

### Examples
Template Content:
`[EntityHyperlink(Label="Navigate to document in Kahua")]`

Template Output:

<ins>Navigate to document in Kahua</ins>

## Image Token
The Image token is used to output the contents of an image file that is stored at a given attribute path on an entity.


### Usage

```
[Image(Source=source,Path=path,Width=value,Height=value,Top=value,Left=value,
 RelativeHorizontalPosition=value,  
 RelativeVerticalPosition=value,
 HorizontalAlignment=value,
 VerticalAlignment=value,
 WrapType=value,  
 WrapSide=value,
 BehindText=value)]`
```

<table>
<thead>
<tr class="header">
<th><strong>Parameter</strong></th>
<th><strong>Description</strong></th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>Source=&lt;source&gt;</td>
<td>See the prior section titled Token Source (Parameter).  For the purposes of the Image token, the value Attribute indicates the token operates on the current entity, the value Project indicates the token operates on the project the current entity is contained within.</td>
</tr>
<tr class="odd">
<td>Path=&lt;attribute path&gt;</td>
<td>this is the path to the image file attribute on the entity.</td>
</tr>  
<tr class="odd">
<td>Height</td>
<td>Height of image in points.</td>
</tr>
<tr class="even">
<td>Width</td>
<td>Width of image in points.</td>
</tr>
<tr class="odd">
<td>Top</td>
<td>Top position of image in points.</td>
</tr>
<tr class="even">
<td>Left</td>
<td>Left position of image in points.</td>
</tr>
<tr class="odd">
<td>Relative Horizontal Position</td>
<td><p>Enumerated value controlling the relative horizontal layout of the image regarding the given value:</p>
  <ul>
<li>Margin</li>
<li>Page</li>
<li>Default</li>
<li>Column</li>
<li>Character</li>
<li>LeftMargin</li>
<li>RightMargin</li>
<li>InsideMargin</li>
<li>OutsideMargin</li>
  </ul>
  </td>
</tr>
<tr class="even">
<td>Relative Vertical Position</td>
<td><p>Enumerated value controlling the relative vertical layout of the image regarding the given value:</p>
  <ul>
<li>TableDefault</li>
<li>Margin</li>
<li>Page</li>
<li>Paragraph</li>
<li>TextFrameDefault</li>
<li>Line</li>
<li>TopMargin</li>
<li>BottomMargin</li>
<li>InsideMargin</li>
<li>OutsideMargin</li>
  </ul>
  </td>
</tr>
<tr class="odd">
<td>Horizontal Alignment</td>
<td><p>Enumerated value controlling the horizontal alignment of the image:</p>
  <ul>
<li>Default</li>
<li>None</li>
<li>Left</li>
<li>Center</li>
<li>Right</li>
<li>Inside</li>
<li>Outside</li>
  </ul>
  </td>
</tr>
<tr class="even">
<td>Vertical Alignment</td>
<td><p>Enumerated value controlling the vertical alignment of the image:</p>
  <ul>
<li>Inline</li>
<li>Default</li>
<li>None</li>
<li>Top</li>
<li>Center</li>
<li>Bottom</li>
<li>Inside</li>
<li>Outside</li>
  </ul>
  </td>
</tr>
<tr class="odd">
<td>WrapType</td>
<td><p>Defines if the image is inline or floating. Values are:</p>
  <ul>
<li>Inline</li>
<li>TopBottom</li>
<li>Square</li>
<li>None</li>
<li>Tight</li>
<li>Through</li>
  </ul>
  </td>
</tr>
<tr class="even">
<td>WrapSide</td>
<td><p>Specifies how text is wrapped around the image. Values are:</p>
  <ul>
<li>Default</li>
<li>Both</li>
<li>Left</li>
<li>Right</li>
<li>Largest</li>
  </ul>
  </td>
</tr>
<tr class="odd">
<td>BehindText</td>
<td>Controls if the image is displayed behind text (true) or above text (false).</td>
</tr>
</tbody>
</table>

### Examples

Template Content:

The Image:  `[Image(Source=Attribute,Path=Picture,Width=150,Height=150,Top=0,Left=800)]`

Template Output:

The Image:  ![Logo Description automatically generated](/development/featuredocs/creatingportableviewtemplates/creatingportableviewtemplates_image2.png)



## CompanyLogo Token

The CompanyLogo token is used to output the ambient logo image associated with a domain/company, or project, based upon the portable
view configuration for the domain and project. The image will be displayed at the position where the token is in the document.

### Usage

```
[CompanyLogo(Width=value,Height=value,Top=value,Left=value,
 RelativeHorizontalPosition=value,  
 RelativeVerticalPosition=value,
 HorizontalAlignment=value,
 VerticalAlignment=value,
 WrapType=value,  
 WrapSide=value,
 BehindText=value)]`
```

The CompanyLogo token parameters are as follows:

<table>
<thead>
<tr class="header">
<th><strong>Parameter</strong></th>
<th><strong>Description</strong></th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>Height</td>
<td>Height of image in points.</td>
</tr>
<tr class="even">
<td>Width</td>
<td>Width of image in points.</td>
</tr>
<tr class="odd">
<td>Top</td>
<td>Top position of image in points.</td>
</tr>
<tr class="even">
<td>Left</td>
<td>Left position of image in points.</td>
</tr>
<tr class="odd">
<td>Relative Horizontal Position</td>
<td><p>Enumerated value controlling the relative horizontal layout of the image regarding the given value:</p>
  <ul>
<li>Margin</li>
<li>Page</li>
<li>Default</li>
<li>Column</li>
<li>Character</li>
<li>LeftMargin</li>
<li>RightMargin</li>
<li>InsideMargin</li>
<li>OutsideMargin</li>
  </ul>
  </td>
</tr>
<tr class="even">
<td>Relative Vertical Position</td>
<td><p>Enumerated value controlling the relative vertical layout of the image regarding the given value:</p>
  <ul>
<li>TableDefault</li>
<li>Margin</li>
<li>Page</li>
<li>Paragraph</li>
<li>TextFrameDefault</li>
<li>Line</li>
<li>TopMargin</li>
<li>BottomMargin</li>
<li>InsideMargin</li>
<li>OutsideMargin</li>
  </ul>
  </td>
</tr>
<tr class="odd">
<td>Horizontal Alignment</td>
<td><p>Enumerated value controlling the horizontal alignment of the image:</p>
  <ul>
<li>Default</li>
<li>None</li>
<li>Left</li>
<li>Center</li>
<li>Right</li>
<li>Inside</li>
<li>Outside</li>
  </ul>
  </td>
</tr>
<tr class="even">
<td>Vertical Alignment</td>
<td><p>Enumerated value controlling the vertical alignment of the image:</p>
  <ul>
<li>Inline</li>
<li>Default</li>
<li>None</li>
<li>Top</li>
<li>Center</li>
<li>Bottom</li>
<li>Inside</li>
<li>Outside</li>
  </ul>
  </td>
</tr>
<tr class="odd">
<td>WrapType</td>
<td><p>Defines if the image is inline or floating. Values are:</p>
  <ul>
<li>Inline</li>
<li>TopBottom</li>
<li>Square</li>
<li>None</li>
<li>Tight</li>
<li>Through</li>
  </ul>
  </td>
</tr>
<tr class="even">
<td>WrapSide</td>
<td><p>Specifies how text is wrapped around the image. Values are:</p>
  <ul>
<li>Default</li>
<li>Both</li>
<li>Left</li>
<li>Right</li>
<li>Largest</li>
  </ul>
  </td>
</tr>
<tr class="odd">
<td>BehindText</td>
<td>Controls if the image is displayed behind text (true) or above text (false).</td>
</tr>
</tbody>
</table>

### Example

Template Content:

`[CompanyLogo(Width=150,Height=150,Top=0,Left=800)]`

Template Output:

![Logo Description automatically generated](/development/featuredocs/creatingportableviewtemplates/creatingportableviewtemplates_image2.png)

## eSignature Token

The eSignature token is used to output the signature stamp (PIN-based) signatures captured in Kahua for recording user signatures on documents and in workflows. Note that this is separate from Docusign. A PIN eSignature will comprise of a signature image, the username and optional user title, and the timestamp of the signature. The eSignature token utilizes the same image layout parameters as that of the CompanyLogo token. Please refer to the Company Logo section for the parameters shared with that token. 

> Note that the Signature token is now supported in a Table layout.
{.is-success}


### Usage

`[Signature(Attribute=attribute path, PreSignatureTextPosition=position, PostSignatureTextPosition=position, image arguments)]`

The eSignature token parameters are as follows:

<table>
<thead>
<tr class="header">
<th><strong>Parameter</strong></th>
<th><strong>Description</strong></th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>Attribute</td>
<td>Path to attribute containing signature</td>
</tr>
<tr class="even">
<td>PreSignatureTextPosition</td>
<td><p>Enumerated value controlling the position of the text displayed prior to the signature image. Values are:</p>
<ul>
<li><p>Default. Default position is Above.</p></li>
<li><p>None. No text is displayed.</p></li>
<li><p>Above. Text displayed above image.</p></li>
<li><p>Below. Text displayed below image.</p></li>
<li><p>Left. Text displayed to left of image.</p></li>
<li><p>Right. Text displayed to right of image.</p></li>
</ul></td>
</tr>
<tr class="odd">
<td>PostSignatureTextPosition</td>
<td>Enumerated value controlling the position of the text displayed after the signature image. This is the same set of values as that defined for the PreSignatureTextPosition, however the default value for the PostSignatureTextPosition is Below..</td>
</tr>
<tr class="even">
<td>Image arguments</td>
<td>See parameters for the CompanyLogo token</td>
</tr>
</tbody>
</table>

### Examples

Template Content:

`[Signature(Attribute=SomeSignature,Width=150,Height=150,Top=0,Left=800)]`

Template Output:

![A drawing of a person Description automatically generated](/development/featuredocs/creatingportableviewtemplates/creatingportableviewtemplates_image3.png)

## DocuSign Signature Control Tokens

The DocuSign Signature Control tokens are a set of tokens that can be
used in tandem with portable views that are sent through Docusign,
providing fine-grained control of where the DocuSign markers are shown
in the Docusign user interface.

`[DocuSign(SignatureIndex=#)]`

`[DocuSign(DateIndex=#)]`

`[DocuSign(InitialIndex=#)]`

`[DocuSign(CheckboxIndex=#,FieldName="cb#",Required="true",Locked="false")]`

`[DocuSign(TextBoxIndex=#,FieldName="tb#",Required="false",Locked="false",Width=50)]`

Note that the preferred token usage for DocuSign signature tokens is
`[Docusign(...)]`, however for reverse compatibility with prior
implementations, Kahua will also recognize the use of `[Signature(...)]`
as the token as well.

### Usage

| **Parameter**      | **Description**                                                                                                                                                                       |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| SignatureIndex=\#  | Parameter indicates a signature is provided at the token location. The \# indicates the signer sequence.                                                                              |
| DateIndex=\#       | Parameter indicates a date is provided at the token location.                                                                                                                         |
| InitialIndex=\#    | Parameter indicates the signer initials are provided at the token location.                                                                                                            |
| CheckBoxIndex=\#   | Parameter indicates a checkbox for the signer sequence \# is shown at the token location.                                                                                             |
| TextBoxIndex=\#    | Parameter indicates a textbox for the signer sequence \# is shown at the token location.                                                                                              |
| FieldName="name\#" | A unique name for the checkbox or textbox; DocuSign expects the convention of "cb\#" for checkboxes and "tb\#" for textboxes. The \# matches the signer sequence.                     |
| Required="bool"    | Boolean indicates if checkbox or textbox entry is required. For checkboxes, a required entry means it must be checked. For texboxes a required entry means some text must be entered. |
| Locked="bool"      | Boolean indicates if a checkbox or textbox is locked, meaning the content cannot be changed.                                                                                          |
| Width=\<width\>    | Width of a displayed text box.                                                                                                                                                        |

Note that for the signer sequence value (the \# in the parameters
above), there must be sufficient tokens supplied in a document for the
number of DocuSign signers involved in the approval process.

### Examples

Template Content:

<table>
<tbody>
<tr class="odd">
<td><p>I agree to content in document [Attribute(ApprovalTestApp.Description)]</p>
<p>For the amount of [Attribute(ApprovalTestApp.ContractAmount)]</p>
<p><strong>Signature tokens for [Attribute(ApprovalTestApp.PersonOne.ShortLabel)]:</strong></p>
<table>
<thead>
<tr class="header">
<th>Signature:</th>
<th>[DocuSign(SignatureIndex=1)]</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>Initial:</td>
<td>[DocuSign(InitialIndex=1)]</td>
</tr>
<tr class="even">
<td>Date:</td>
<td>[DocuSign(DateIndex=1)]</td>
</tr>
<tr class="odd">
<td>Checkbox 1:</td>
<td>[DocuSign(FieldName="Signer1FirstCheckbox",CheckBoxIndex=1)]</td>
</tr>
<tr class="even">
<td>Checkbox 2:</td>
<td>[DocuSign(FieldName="Signer1SecondCheckbox",CheckBoxIndex=1)]</td>
</tr>
<tr class="odd">
<td>Textbox, default:</td>
<td>[DocuSign(FieldName="Signer1FirstTextbox",TextBoxIndex=1)]</td>
</tr>
<tr class="even">
<td>Text optional, 50 wide:</td>
<td>[DocuSign(FieldName="Signer1SecondTextbox",TextBoxIndex=1,Required="false",Width="50")]</td>
</tr>
<tr class="odd">
<td>Text required, 500 wide:</td>
<td>[DocuSign(FieldName="Signer1ThirdTextbox",TextBoxIndex=1,Required="true",Width="500")]</td>
</tr>
</tbody>
</table>
<p><strong>Signature tokens for [Attribute(ApprovalTestApp.PersonTwo.ShortLabel)]:<br />
</strong></p>
<table>
<thead>
<tr class="header">
<th>Signature:</th>
<th>[DocuSign(SignatureIndex=2)]</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>Initial:</td>
<td>[DocuSign(InitialIndex=2)]</td>
</tr>
<tr class="even">
<td>Date:</td>
<td>[DocuSign(DateIndex=2)]</td>
</tr>
<tr class="odd">
<td>Checkbox 1:</td>
<td>[DocuSign(FieldName="Signer2FirstCheckbox",CheckBoxIndex=2)]</td>
</tr>
<tr class="even">
<td>Checkbox 2:</td>
<td>[DocuSign(FieldName="Signer2SecondCheckbox",CheckBoxIndex=2)]</td>
</tr>
<tr class="odd">
<td>Textbox, default:</td>
<td>[DocuSign(FieldName="Signer2FirstTextbox",TextBoxIndex=2)]</td>
</tr>
<tr class="even">
<td>Text optional, 50 wide:</td>
<td>[DocuSign(FieldName="Signer2SecondTextbox",TextBoxIndex=2,Required="false",Width="50")]</td>
</tr>
<tr class="odd">
<td>Text required, 500 wide:</td>
<td>[DocuSign(FieldName="Signer2ThirdTextbox",TextBoxIndex=2,Required="true",Width="500")]</td>
</tr>
</tbody>
</table></td>
</tr>
</tbody>
</table>

Template Output:

<table>
<tbody>
<tr class="odd">
<td><p>DocuSign Website with token content:</p>
<p><img src="/development/featuredocs/creatingportableviewtemplates/creatingportableviewtemplates_image4.png" style="width:6.5in;height:4.84931in" /></p></td>
</tr>
</tbody>
</table>

<table>
<tbody>
<tr class="odd">
<td><p>Signed document received from DocuSign:</p>
<p><img src="/development/featuredocs/creatingportableviewtemplates/creatingportableviewtemplates_image5.png" style="width:6.5in;height:5.31319in" /></p></td>
</tr>
</tbody>
</table>

## Domain and Partition Metadata Tokens

The domain and partition metadata tokens provide the ability to output information about the current domain and/or partition that applies to the current entity.

There are several tokens available for outputting specific domain and partition metadata:

| **Token**                   | **Description**                                                                                                        |
| --------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| \[DomainLabel\]             | Indicates the name/label of the domain (e.g. My Domain).    |
| \[DomainPartitionPath\]     | Indicates the full path of the current domain partition.                                                               |
| \[DomainPartitionName\]     | Indicates the name of the current domain partition.                                                                    |
| \[DomainPartitionListName\] | Indicates the name of the list in the current domain partition                                                         |
| \[DomainPartitionPathListName\] | Indicates name of the list in the current domain partition as the full path to the partition and list. |
| \[DomainPartitionLabel\]    | Indicates the label of the domain partition.                                                                           |
| \[DomainTimeZoneLong\]      | Indicates the domain time zone using a long string (e.g. Eastern Standard Time).                                       |
| \[DomainTimeZoneShort\]     | Indicates the domain time zone using the UTC offset (e.g. Eastern Standard Time is "UTC-5" when DST is not in effect). |
| \[DomainTimeZoneAbbreviated\] | Indicates the domain time zone using the common abbreviation (e.g. EST). |
| \[PartitionTimeZoneLong\]   | Indicates the partition time zone using a long string (e.g. Eastern Standard Time).                                    |
| \[PartitionTimeZoneShort\]  | Indicates the partition time zone using the UTC offset.                                                                |
| \[PartitionTimeZoneAbbreviated\] | Indicates the partition time zone using the common abbreviation (e.g. PST). |

### Usage

To use any of the Domain and Partition Metadata tokens, specify as shown above.

### Examples

| **Template Content:**       | **Template Output:**                  |
| --------------------------- | ------------------------------------- |
| \[DomainLabel\]             | My Domain                             |
| \[DomainPartitionPath\]     | My Domain\\My Project                 |
| \[DomainPartitionName\]     | My Project                            |
| \[DomainPartitionListName\] | My List                               |
| \[DomainPartitionPathListName\] | My Domain\My Projects\My List     |
| \[DomainPartitionLabel\]    | My Project                            |
| \[DomainTimeZoneLong\]      | (UTC-5:00) Eastern Time (US & Canada) |
| \[DomainTimeZoneShort\]     | UTC-4:00                              |
| \[DomainTimeZoneAbbreviated\] | EST                                 |
| \[PartitionTimeZoneLong\]   | (UTC-5:00) Eastern Time (US & Canada) |
| \[PartitionTimeZoneShort\]  | UTC-4:00                              |
| \[PartitionTimeZoneAbbreviated\] | EST                                 |



## Time and Time Zone Tokens

The time and time zone tokens provide the ability to output information about the current time and time zone in effect in the template output.

There are several tokens available for outputting the time and time zone information:

| **Token**                      | **Description**                                                                                                         |
| ------------------------------ | ----------------------------------------------------------------------------------------------------------------------- |
| \[CurrentTimeZoneAbbreviated\] | Indicates the current time zone using the abbreviation.                                                                 |
| \[CurrentTimeZoneLong\]        | Indicates the current time zone using a long string (e.g. Eastern Standard Time).                                       |
| \[CurrentTimeZoneShort\]       | Indicates the current time zone using the UTC offset (e.g. "UTC-5" is Eastern Standard Time when DST is not in effect). |
| \[CurrentTime\]                | Outputs the current date and time using the local format.                                                               |

### Usage

To use any of the Time and Time Zone Tokens, specify as shown above.

### Examples

| **Template Content:**          | **Template Output:**                  |
| ------------------------------ | ------------------------------------- |
| \[CurrentTimeZoneAbbreviated\] | EST                                   |
| \[CurrentTimeZoneLong\]        | (UTC-5:00) Eastern Time (US & Canada) |
| \[CurrentTimeZoneShort\]       | UTC-4:00                              |
| \[CurrentTime\]                | 10/23/2020 2:57 PM                    |

## User Token

The user token inserts the current username into the template output.

### Usage

`[UserName]`

### Examples

Template Content:

`Current user is [UserName].`

Template Output:

`Current user is Fred Jones.`

## Timestamp Token

The TimeStamp token is a short-hand way to insert the current report generation time stamp into the template output in the time zone of the current domain/partition. This will be in the localized date/time format "g" followed by the domain/partition time zone abbreviation. For example: "07/12/2019 01:35 PM EST".

### Usage

`[ReportModifiedTimeStamp]`

### Example

Template Content:

`Report generation time [ReportModifiedTimeStamp]. `

Template Output:

`Report generation time 10/13/2019 03:32 PM EST.`

## Media Token

The Media Token is used to output tabular content from Media that is captured in an app. This largely consists of image information with optional captions and other metadata provided with the media.

### Usage

`[Media(Path=<attribute path>,TextFormat=<caption>,ImageSize=<size>)]`

<table>
<thead>
<tr class="header">
<th><strong>Parameter</strong></th>
<th><strong>Description</strong></th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>Path=&lt;attribute path&gt;</td>
<td>Optional path to the media attribute on the entity.  If not specified, this defaults to "Media".  If specified, this should provide the path to the Media attribute relative to the container for the token (if in a table or list, for example).</td>
</tr>
<tr class="even">
<td>TextFormat=&lt;caption&gt;</td>
<td>Optional parameter indicating an attribute path expression which will output a caption for the media item. If no value is specified, this defaults to [Caption], which is the default caption attribute for a media item.  To suppress the caption, specify a space:  TextFormat=" "</td>
</tr>
<tr class="odd">
<td>ImageSize=&lt;size&gt;</td>
<td><p>Optional parameter indicating the height of the images to use when sizing the images in the table output. The following values are recognized:</p>
<ul>
<li><p>Small. Sets the height of the image to 120 pixels.</p></li>
<li><p>Large. Sets the height of the image to 240 pixels.</p></li>
</ul>
<p>If not specified, image heights default to 180 pixels.</p></td>
</tr>
</tbody>
</table>

> To suppress image captions specify the parameter TextFormat=" ".  This replaces the default [Caption] with a space.
{.is-info}


### Examples

Template Content:

<table>
<tbody>
<tr class="odd">
<td>Media:<br />
<br />
[Media(ImageSize="small")]</td>
</tr>
</tbody>
</table>

Template Output:

![](/development/featuredocs/creatingportableviewtemplates/creatingportableviewtemplates_image6.png)

## Table Tokens

The Table tokens are used to define a Word table with fixed columns and dynamic rows that will output the rows in a repeating fashion against the collection of records the table is bound to. Tables can have zero or more repeating header rows and can also define groupings so that groups can contain summary totals for the grouped attributes. A table defined in a template will have the `[StartTable]` token preceded by a paragraph break, then the word table with the desired column layout, the desired header row layout, and the desired data row layout. It is then terminated by the `[EndTable]` token.

There are two different types of Table tokens supported.  The parameterized Table tokens are described below.  Following this is a description of the XML Table tokens which provide all of the features of the parameterized table tokens but also provide some enhanced capabilities around grouping and totaling data.

### Parameterized Table Output Tokens

#### Usage

```
[StartTable(Name=uniqueName, 
 Source=<source>, 
 Path=<path>, 
 RowsInHeader=<#>, 
 ShowEmptyHeader="<boolean>"
 Sort=attribute order[;attribute order],
 GroupMode=<groupMode>, GroupBy=<attribute>, GroupTotal=<attribute>, GroupByTotalAttribute=<attribute>,
 Where.Path=<wherepath>, Where.Operator=operator, Where.Value=<value>,
 Where.Conditions=@(<hub conditionals>))]`
```

| Table header row     |      |       |
| ---------------------|------|-------|
| [Attribute Tokens]   |      |       |

`[EndTable]`

The table token parameters are as follows:

<table>
<thead>
<tr class="header">
<th><strong>Parameter</strong></th>
<th><strong>Description</strong></th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>Name</td>
<td>The unique name for the table in the template document. Each table token definition must have a unique name.</td>
</tr>
<tr class="even">
<td>Path</td>
  <td>Path to the attribute that contains the collection of records.</br>
  The Path parameter can be omitted, or can use the period (".") path which will bind the table content to the current entity, rather than to a collection of entities in a given attribute.  This technique is recommended when using Word tables within the IF/THEN conditional tokens.  This is also recommended when defining Word tables in a document that are not going to necessarily contain any bound PV tokens.
</td>
</tr>
<tr class="odd">
<td>Source</td>
<td>Source of data for Path.  See  <a name="#Token-Source-(Parameter)">Token Source (Parameter).  Defaults to Attribute.</a></td>
</tr>
<tr class="even">
<td>RowsInHeader</td>
<td>Number of rows in the table header. If not specified this defaults to 0, assuming no header rows in the template table.</td>
</tr>
<tr class="odd">
<td>ShowEmptyTable</td>
<td>Boolean that controls if the table is displayed with just the header rows if no data is present in the table.  Default is false.</td>
</tr>
<tr class="even">
<td>Sort</td>
<td><p>Optional parameter used for specifying the sort order of data in the table. Is used, at minimum a single attribute name should be specified, with an optional space followed by the order, which is Ascending or Descending. If no order is specified, the default is Ascending. If multiple attributes are used for sorting, the attribute order pair is delimited by a semicolon.</p>
<p>For example:</p>
<p>Sort=Attribute1 Descending;Attribute2 Ascending</p></td>
</tr>
<tr class="odd">
<td>GroupMode</td>
<td><p>Group mode indicates the type of grouping to be performed. Valid values are:</p>
<ul>
<li><p>None - the default which is no grouping is applied.</p></li>
<li><p>Default or SubTotal - grouping is performed on the items in the GroupBy attribute with the individual rows output and a grouping row output following the individual rows.</p></li>
<li><p>Summary - grouping is performed on the items in the GroupBy attribute but only the grouping row is output.</p></li>
</ul></td>
</tr>
<tr class="even">
<td>GroupBy</td>
<td>Designates the path to an attribute to group the data by.</td>
</tr>
<tr class="odd">
<td>GroupByTotalAttribute</td>
<td>Designates the path to an attribute which is used to retrieve an amount from and total into an aggregated total for the group.</td>
</tr>
<tr class="even">
<td>GroupTotal</td>
<td>Designates the path to an attribute into which the aggregated group total is stored. If used and is to be shown in the document output, the group row in the table should use the attribute name specified here.</td>
</tr>
<tr class="odd">
  <td>Where.Path</td>
  <td>Designates an optional path to an attribute on the Path entities that are used for a conditional evaluation for inclusion in the table output </td>
</tr>
  <tr class="even">
  <td>Where.Operator</td>
  <td>The operator to use when comparing the Where.Path value to the Where.Value value.  If a non-value comparision is used (such as IsNotNull), no Where.Value is required.</td>
</tr>
<tr class="odd">
  <td>Where.Value</td>
  <td>The value to compare the Where.Path value against, if the Where.Operator requires a comparison value.</td>
</tr>
<tr class="even">
  <td>Where.Conditions=@(<i>hub conditionals )</td>
  <td>Optional Hub Conditional expression for use of complex conditions for determination of conditional evaluation for inclusion in the table output.  See the <a href="/Partners/kBuilder/Guides/PortableView/CreatingPortableViewTemplates#hub-conditionals">[Hub Conditionals]</a> section above.</td>
</tr>

</tbody>
</table>

If a table is to include grouping, a row must be defined in the Word table with the token `[TableGroupRowTotal]` which will designate the row for use as the output from a grouping operation.

> Note that the [StartTable] and [EndTable] tokens must be preceded by a paragraph, the Word paragraphs are used as anchoring characters when placing the generated table within the resulting document.
{.is-warning}


> Note that tables may not have nested containers within them, such as other table or list tokens.
{.is-warning}


#### Examples

The first example shows a simple table with no grouping.

Template Content:

<table>
<tbody>
<tr class="odd">
<td><p>[StartTable(Name=table1,Source=Attribute,Path=Items,RowsInHeader=1)]</p>
<table>
<thead>
<tr class="header">
<th><strong>[NumberLabel]</strong></th>
<th><strong>[DescriptionLabel]</strong></th>
<th><strong>[AmountLabel]</strong></th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>[Attribute(Number)]</td>
<td>[Attribute(Description)]</td>
<td>[Currency(Path=Amount)]</td>
</tr>
</tbody>
</table>
<p>[EndTable]</p></td>
</tr>
</tbody>
</table>

Template Output:

<table>
<tbody>
<tr class="odd">
<td><table>
<thead>
<tr class="header">
<th><strong>Number</strong></th>
<th><strong>Description</strong></th>
<th><strong>Amount</strong></th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>1</td>
<td>Item 1</td>
<td>$300.00</td>
</tr>
<tr class="even">
<td>2</td>
<td>Item 2</td>
<td>$1,500.00</td>
</tr>
<tr class="odd">
<td>3</td>
<td>Item 3</td>
<td>$250.00</td>
</tr>
</tbody>
</table></td>
</tr>
</tbody>
</table>

The second example shows a table utilizing sorting and grouping.

Template Content:

<table>
<tbody>
<tr class="odd">
<td><p>[StartTable(Name=table1,Source=Attribute,Path=ContractChangeOrder.Items,RowsInHeader=1,Sort=ItemType Ascending;Number Ascending,GroupMode=SubTotal,GroupBy=ItemType,GroupByTotalAttribute=CostCurrentTotalValue,GroupTotal=GroupTotalValue)]</p>
<table>
<thead>
<tr class="header">
<th><strong>[NumberLabel]</strong></th>
<th><strong>[DescriptionLabel]</strong></th>
<th><strong>[ActivityCodeLabel]</strong></th>
<th><strong>[AmountLabel]</strong></th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>[Attribute(Number)]</td>
<td>[Attribute(Description)]</td>
<td>[Attribute(WorkbreakdownItem.Code)]</td>
<td>[Currency(Path=CostCurrentTotalValue)]</td>
</tr>
<tr class="even">
<td>[TableGroupTotalRow]</td>
<td></td>
<td>[Attribute(ItemType)] Total</td>
<td>[Currency(Path=GroupTotalValue)]</td>
</tr>
</tbody>
</table>
<p>[EndTable]</p></td>
</tr>
</tbody>
</table>

Template Output:

<table>
<tbody>
<tr class="odd">
<td><table>
<thead>
<tr class="header">
<th><strong>Number</strong></th>
<th><strong>Description</strong></th>
<th><strong>Activity Code</strong></th>
<th><strong>Amount</strong></th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>1</td>
<td>Parts</td>
<td>301.1</td>
<td>$300.00</td>
</tr>
<tr class="even">
<td>2</td>
<td>More Parts2</td>
<td>301.2</td>
<td>$1,500.00</td>
</tr>
<tr class="odd">
<td></td>
<td></td>
<td>Parts Total</td>
<td>$1,800.00</td>
</tr>
<tr class="even">
<td>3</td>
<td>Plumbing</td>
<td>401.1</td>
<td>$500.00</td>
</tr>
<tr class="odd">
<td>4</td>
<td>Pipes</td>
<td>401.2</td>
<td>$600.00</td>
</tr>
<tr class="even">
<td></td>
<td></td>
<td>Plumbing Total</td>
<td>$1,100.00</td>
</tr>
<tr class="odd">
<td>5</td>
<td>Electrical</td>
<td>501.1</td>
<td>$700.00</td>
</tr>
<tr class="even">
<td>6</td>
<td>Wiring</td>
<td>501.2</td>
<td>$800.00</td>
</tr>
<tr class="odd">
<td></td>
<td></td>
<td>Electrical Total</td>
<td>$1,500.00</td>
</tr>
</tbody>
</table></td>
</tr>
</tbody>
</table>

Here is another example based upon the data above, but showing the behavior for the GroupMode=Summary.

Template Content:

<table>
<tbody>
<tr class="odd">
<td><p>[StartTable(Name=table1,Source=Attribute,Path=ContractChangeOrder.Items,RowsInHeader=1,Sort=ItemType Ascending;Number Ascending,GroupMode=Summary,GroupBy=ItemType,GroupByTotalAttribute=CostCurrentTotalValue,GroupTotal=CostCurrentTotalValue)]</p>
<table>
<thead>
<tr class="header">
<th><strong>[NumberLabel]</strong></th>
<th><strong>[DescriptionLabel]</strong></th>
<th><strong>[ActivityCodeLabel]</strong></th>
<th><strong>[AmountLabel]</strong></th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>[TableGroupTotalRow]</td>
<td></td>
<td>[Attribute(ItemType)] Total</td>
<td>[Currency(Path=GroupTotalValue)]</td>
</tr>
</tbody>
</table>
<p>[EndTable]</p></td>
</tr>
</tbody>
</table>

Template Output:

<table>
<tbody>
<tr class="odd">
<td><table>
<thead>
<tr class="header">
<th><strong>Number</strong></th>
<th><strong>Description</strong></th>
<th><strong>Activity Code</strong></th>
<th><strong>Amount</strong></th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td></td>
<td></td>
<td>Parts Total</td>
<td>$1,800.00</td>
</tr>
<tr class="even">
<td></td>
<td></td>
<td>Plumbing Total</td>
<td>$1,100.00</td>
</tr>
<tr class="odd">
<td></td>
<td></td>
<td>Electrical Total</td>
<td>$1,500.00</td>
</tr>
</tbody>
</table></td>
</tr>
</tbody>
</table>

### XML Table Tokens
The XML table tokens provide the same functionality as the parameterized table tokens, but add in some additional grouping and totaling features as described here.

#### Usage
```
@[<StartTable Name="uniqueName" Source="<source>" Path="<attributePath>" RowsInHeader="<#>" ShowEmptyTable="<bool>">
	<StartTable.Sorts>
		<Sort Path="path" Direction="<direction>" />
	</StartTable.Sorts>
  <StartTable.Grouping GroupMode="<groupMode>" GroupBy="<attribute>" TotalMode="<totalMode>">
  	<Grouping.Operations>
    	<Sum>
      	<Sum.Paths>
        	<Path SourcePath="<sourceAttributePath>" TargetPath="<targetAttributePath>" />
				</Sum.Paths>
      </Sum>
      <Min>
      	<Min.Paths>
        	<Path SourcePath="<sourceAttributePath>" TargetPath="<targetAttributePath>" />
				</Min.Paths>
      </Min>
      <Max>
      	<Max.Paths>
        	<Path SourcePath="<sourceAttributePath>" TargetPath="<targetAttributePath>" />
				</Max.Paths>
      </Max>
      <Average>
      	<Average.Paths>
        	<Path SourcePath="<sourceAttributePath>" TargetPath="<targetAttributePath>" />
				</Average.Paths>
      </Average
		</Grouping.Operations>
  </StartTable.Grouping>
  <StartTable.Where>
  	(<hub conditionals>)
	</StartTable.Where>
</StartTable>
```

| Table header row(s)  |      |       |
| ---------------------|------|-------|
| [Attribute Tokens]   |      |       |
| [TableGroupTotalRow] | [TargetPath] |
| [TableTotalRow]      | [TargetPath] |
`@[<EndTable />]`

The StartTable token elements are as follows:

<table>
<thead>
<tr class="header">
<th><strong>Element</strong></th>
<th><strong>Description</strong></th>
</tr>
</thead>
<tbody>
  <tr class="odd">
    <td>&lt;StartTable&gt; Elements</td>
    <td>
      <table>
				<thead>
					<tr class="header">
						<th><strong>Parameter</strong></th>
						<th><strong>Description</strong></th>
					</tr>
				</thead>
				<tr class="odd">
					<td>Name</td>
					<td>The unique name for the table in the template document. Each table token definition must have a unique name.</td>
				</tr>
				<tr class="even">
					<td>Path</td>
  				<td>Path to the attribute that contains the collection of records.</br>
  						The Path parameter can be omitted, or can use the period (".") path which will bind the table content to the current entity, rather than to a collection of entities in a given attribute.  This technique is recommended when using Word tables within the IF/THEN conditional tokens.  This is also recommended when defining Word tables in a document that are not going to necessarily contain any bound PV tokens.
				</td>
				</tr>
				<tr class="odd">
					<td>Source</td>
  				<td>Source of data for Path.  See  <a name="#Token-Source-(Parameter)">Token Source (Parameter).</a>  Defaults to Attribute.</td>
				</tr>
				<tr class="even">
					<td>RowsInHeader</td>
					<td>Number of rows in the table header. If not specified this defaults to 0, assuming no header rows in the template table.</td>
				</tr>
				<tr class="odd">
					<td>ShowEmptyHeader</td>
					<td>Boolean that controls if the table is displayed with just the header rows if no data is present in the table.  Default is false.</td>
				</tr>
      </table>
    </td>
  </tr>
  <tr class="even">
  	<td>&lt;StartTable.Sort&gt; Elements</td>
  	<td>Optional element used for defining the sort order on the contents of the table data.
      <table>
				<thead>
					<tr class="header">
						<th><strong>Parameter</strong></th>
						<th><strong>Description</strong></th>
					</tr>
				</thead>
  			<tr class="odd">
  				<td>Path</td>
  				<td>Attribute path data is sorted on</td>
  			</tr>
  			<tr class="even">
  				<td>Direction</td>
  				<td><p>Direction of sort.  Default is Ascending. If grouping is used a sort must be specified.  Valid values are:</p>
		  			<ul>
        		<li><p>Ascending</p></li>
        		<li><p>Descending</p></li>
      			</ul>
  				</td>
  			</tr>
      </table>
  	</td>
  </tr>
  <tr class="odd">
  	<td>&lt;StartTable.Grouping&gt; Elements</td>
  	<td>Optional element used to control grouping and totaling operations
      <table>
				<thead>
					<tr class="header">
						<th><strong>Parameter</strong></th>
						<th><strong>Description</strong></th>
					</tr>
				</thead>
				<tr class="odd">
					<td>GroupMode</td>
					<td><p>Group mode indicates the type of grouping to be performed. Valid values are:</p>
						<ul>
						<li><p>None - the default which is no grouping is applied.</p></li>
						<li><p>Default or SubTotal - grouping is performed on the items in the GroupBy attribute with the individual rows output and a grouping row output following the individual rows.</p></li>
						<li><p>Summary - grouping is performed on the items in the GroupBy attribute but only the grouping row is output.  Note that the summary row must be defined in the table content designated using the [TableGroupTotalRow] token.</p></li>
						</ul></td>
				</tr>
				<tr class="even">
					<td>GroupBy</td>
					<td>Designates the path to an attribute to group the data by.</td>
				</tr>
				<tr class="even">
					<td>TotalMode</td>
					<td><p>Total mode indicates that running aggregates are determined over all data in the table using the designated operations.  Valid values are:</p>
          <ul>
            <li><p>None - the default which is no total is calculated or output</p></li>
            <li><p>Summary - a total is output.  A total row must be defined in the table content designated using the [TableTotalRow] token</p></li>
            </ul></td>
				</tr>
      </table>
  	</td>
  </tr>
  <tr class="even">
  	<td>&lt;Grouping.Operations&gt; Elements</td>
  	<td>Defines the aggregating operations performed on the data in the table.
      <table>
				<thead>
					<tr class="header">
						<th><strong>Parameter</strong></th>
						<th><strong>Description</strong></th>
					</tr>
				</thead>
  			<tr class="odd">
  				<td>Operation (&lt;Sum&gt;)/(&lt;Min&gt;)/(&lt;Max&gt;)/(&lt;Average&gt;) Elements</td>
  				<td>Operation elements are the optional mathematical operations that can be performed over grouped rows.  The respective elements Sum, Min, Max, and Average define the operation performed on the referenced paths.  Define the respective operation only if the given operation is needed for the table content (e.g. Sum if a sum is required)</td>
  			</tr>
        <tr> class="even">
          <td>Operation.Paths</td>
          <td>Contains a set of Path elements that define the source attributes the operation (Sum/Min/Max/Average) is performed on</td>
        </tr>
        <tr class="odd">
          <td>&lt;Path&gt; Element</td>
          <td>Path element defines a source attribute an operation is performed against and the target manufactured attribute the result is stored in for output
            <table>
							<thead>
								<tr class="header">
									<th><strong>Parameter</strong></th>
									<th><strong>Description</strong></th>
								</tr>
							</thead>
              <tr class="odd">
                <td>SourcePath</td>
                <td>The path to the attribute to use as the source of the aggregate operation</td>
              </tr>
              <tr class="even">
                <td>TargetPath</td>
                <td>The path to the manufactured attribute the result of the aggregate operation is stored in.  This path name is what is used to output the grouped or totaled result in the group or total rows in the table</td>
              </tr>
            </table>
          </td>
        </tr>
      </table>
  </td>
  </tr>
  <tr class="odd">
  	<td>&lt;StartTable.Where&gt; Elements</td>
  	<td>Optional element used to define filtering conditions for entities included in the table.  If defined the Where element contains any Hub conditional expression.  See the <a href="/Partners/kBuilder/Guides/PortableView/CreatingPortableViewTemplates#hub-conditionals">[Hub Conditionals]</a> section above.</td>
  </tr>
</tbody>
</table>

If a table is to include grouping or totaling, rows must be defined in the Word table with the token `[TableGroupRowTotal]` for a group row, and/or a row with the token `[TableRowTotal]` for a total row.  These tokens designate that the Word Table row will contain content from group or total aggregates and these aggregated results are output by using the various attribute tokens with their path parameter set to the path given in the TargetPath for the various grouping operations defined for the table.

> Note that the @[&lt;StartTable&gt;] and @[&lt;EndTable&gt;] tokens must be preceded by a paragraph, the Word paragraphs are used as anchoring characters when placing the generated table within the resulting document.
{.is-warning}


> Note that tables may not have nested containers within them, such as other table or list tokens.
{.is-warning}


#### Examples

The following is an example that shows a table using grouping with subtotals and a grand total line that performs all 4 possible aggregate operations over a set of different attributes.

Template Content:

```
@[<StartTable Name=”ContractInvoiceItemsTable” Source=”Attribute” Path=”Items” RowsInHeader=”4”>
  <StartTable.Sorts>
    <Sort Path=”ContractItem.Number” Direction=”Ascending” />
  </StartTable.Sorts>
  <StartTable.Grouping GroupMode=”SubTotal” GroupBy=”ContractItem.Id” TotalMode=”Summary”>
   <Grouping.Operations>
    <Sum>
      <Sum.Paths>
        <Path SourcePath=”ScheduledValue” TargetPath=”SumScheduledValue” />
        <Path SourcePath=”PreviousWorkCompleted” TargetPath=”SumPreviousWorkCompleted” />
        <Path SourcePath=”WorkCompletedThisPeriod” TargetPath=”SumWorkCompletedThisPeriod” />
        <Path SourcePath=”MaterialPresentlyStored” TargetPath=”SumMaterialPresentlyStored” />
        <Path SourcePath=”TotalToDate” TargetPath=”SumTotalToDate” />
        <Path SourcePath=”BalanceToFinish” TargetPath=”SumBalanceToFinish” />
        <Path SourcePath=”TotalRetainage” TargetPath=”SumTotalRetainage” />
      </Sum.Paths>
    </Sum>
    <Min>
      <Min.Paths>
        <Path SourcePath=”ScheduledValue” TargetPath=”MinScheduledValue” />
        <Path SourcePath=”PreviousWorkCompleted” TargetPath=”MinPreviousWorkCompleted” />
        <Path SourcePath=”WorkCompletedThisPeriod” TargetPath=”MinWorkCompletedThisPeriod” />
        <Path SourcePath=”MaterialPresentlyStored” TargetPath=”MinMaterialPresentlyStored” />
        <Path SourcePath=”TotalToDate” TargetPath=”MinTotalToDate” />
        <Path SourcePath=”BalanceToFinish” TargetPath=”MinBalanceToFinish” />
        <Path SourcePath=”TotalRetainage” TargetPath=”MinTotalRetainage” />
      </Min.Paths>
    </Min>
    <Max>
      <Max.Paths>
        <Path SourcePath=”ScheduledValue” TargetPath=”MaxScheduledValue” />
        <Path SourcePath=”PreviousWorkCompleted” TargetPath=”MaxPreviousWorkCompleted” />
        <Path SourcePath=”WorkCompletedThisPeriod” TargetPath=”MaxWorkCompletedThisPeriod” />
        <Path SourcePath=”MaterialPresentlyStored” TargetPath=”MaxMaterialPresentlyStored” />
        <Path SourcePath=”TotalToDate” TargetPath=”MaxTotalToDate” />
        <Path SourcePath=”BalanceToFinish” TargetPath=”MaxBalanceToFinish” />
        <Path SourcePath=”TotalRetainage” TargetPath=”MaxTotalRetainage” />
      </Max.Paths>
    </Max>
    <Average>
      <Average.Paths>
        <Path SourcePath=”ScheduledValue” TargetPath=”AvgScheduledValue” />
        <Path SourcePath=”PreviousWorkCompleted” TargetPath=”AvgPreviousWorkCompleted” />
        <Path SourcePath=”WorkCompletedThisPeriod” TargetPath=”AvgWorkCompletedThisPeriod” />
        <Path SourcePath=”MaterialPresentlyStored” TargetPath=”AvgMaterialPresentlyStored” />
        <Path SourcePath=”TotalToDate” TargetPath=”AvgTotalToDate” />
        <Path SourcePath=”BalanceToFinish” TargetPath=”AvgBalanceToFinish” />
        <Path SourcePath=”TotalRetainage” TargetPath=”AvgTotalRetainage” />
      </Average.Paths>
    </Average>
   </Grouping.Operations>
  </StartTable.Grouping>
  <StartTable.Where>
    <Data Path=”ContractItem” Type=”HasValue” />
  </StartTable.Where>
</StartTable>]
```
![screenshot_2024-02-22_155020.png](/screenshot_2024-02-22_155020.png)

```
@[<EndTable/>]
```

Template Output:
![screenshot_2024-02-22_155603.png](/screenshot_2024-02-22_155603.png)




## List Tokens

The List tokens are used to define a repeating section of content within a document that is bound against a collection of records.

### Usage

```
[StartList(Name=name,
 Source=Attribute, 
 Path=attribute path,
 Sort=attribute order[;attribute order],
 Where.Path=<wherepath>,Where.Operator=operator,Where.Value=<value>,
 Where.Conditions=(<hub conditionals>))]

[StartContentTemplate]

Template content

[EndContentTemplate]

[StartEmptyTemplate]

Empty template content

[EndEmptyTemplate]

[StartContentHeaderTemplate]

Header content

[EndContentHeaderTemplate]

[EndList]
```
<table>
<thead>
<tr class="header">
<th><strong>Parameter</strong></th>
<th><strong>Description</strong></th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td><strong>StartList Parameters</strong></td>
<td></td>
</tr>
<tr class="even">
<td>Name</td>
<td>The unique name for the list in the template document. Each StartList token definition must have a unique name.</td>
</tr>
<tr class="odd">
<td>Path</td>
<td>Path to the attribute that contains the collection of records. Once the path is set, you will not be able to go out of the path inside the list.</td>
</tr>
<tr class="even">
<td>Source</td>
<td>Source of data for Path.  See  <a name="#Token-Source-(Parameter)">Token Source (Parameter).  Defaults to Attribute.</a></td>
</tr>
<tr class="odd">
<td>Sort</td>
<td><p>Optional parameter used for specifying the sort order of data in the list. Is used, at minimum a single attribute name should be specified, with an optional space followed by the order, which is Ascending or Descending. If no order is specified, the default is Ascending. If multiple attributes are used for sorting, the attribute order pair is delimited by a semicolon.</p>
<p>For example:</p>
<p>Sort=Attribute1 Descending ;Attribute2 Ascending</p></td>
</tr>
<tr class="even">
  <td>Where.Path</td>
  <td>Designates an optional path to an attribute on the Path entities that are used for a conditional evaluation for inclusion in the list output </td>
</tr>
  <tr class="odd">
  <td>Where.Operator</td>
  <td>The operator to use when comparing the Where.Path value to the Where.Value value.  If a non-value comparision is used (such as IsNotNull), no Where.Value is required.</td>
</tr>
<tr class="even">
  <td>Where.Value</td>
  <td>The value to compare the Where.Path value against, if the Where.Operator requires a comparison value.</td>
</tr>  
<tr class="odd">
  <td>Where.Conditions=@(<i>hub conditionals )</td>
  <td>Optional Hub Conditional expression for use of complex conditions for determination of conditional evaluation for inclusion in the list output.  See the <a href="/Partners/kBuilder/Guides/PortableView/CreatingPortableViewTemplates#hub-conditionals">[Hub Conditionals]</a> section above.</td>
</tr>  
</tbody>
</table>

The \[StartContentTemplate\]/\[EndContentTemplate\] section of a list definition will contain the content to display for a single record. This section must be defined for a list. The content can include any other token types supported by Kahua, including tables.

The \[StartEmptyTemplate\]/\[EndEmptyTemplate\] section of a list definition contains content that is output for the list if no data is
available for display of the list. For example, if showing a list of contacts, the empty template may output "No contacts available.". This section is not required.

The \[StartContentHeaderTemplate\]/\[EndContentHeaderTemplate\] section of a list defines an optional set of content that is output prior to the output of the data comprising the repeated \[StartContentTemplate\]/\[EndContentTemplate\] content.

### Examples

Template Content:

<table>
<tbody>
<tr class="odd">
<td><p>[StartList(Name=list1,Path=Meeting.MeetingItems)]</p>
<p>[StartContentTemplate]</p>
<p><strong>Item Number</strong> [Attribute(Number)]<br />
<strong>Category</strong> [Attribute(Category)]<br />
<strong>Subject</strong> [Attribute(Subject)]</p>
<p>[EndContentTemplate]</p>
<p>[StartEmptyTemplate]</p>
<p>No action items.</p>
<p>[EndEmptyTemplate]</p>
<p>[StartContentHeaderTemplate]</p>
<p><strong>Meeting Item</strong></p>
<p>[EndContentHeaderTemplate]</p>
<p>[EndList]</p></td>
</tr>
</tbody>
</table>

Template Output:

<table>
<tbody>
<tr class="odd">
<td><p><strong>Meeting Item</strong></p>
<p><strong>Item</strong> <strong>Number</strong> 0001<br />
<strong>Category</strong> Old Business<br />
<strong>Subject</strong> Testing</p>
<p><strong>Meeting Item</strong></p>
<p><strong>Item</strong> <strong>Number</strong> 0002<br />
<strong>Category</strong> New Business<br />
<strong>Subject</strong> Pricing</p>
<p><strong>Meeting Item</strong></p>
<p><strong>Item</strong> <strong>Number</strong> 0003<br />
<strong>Category</strong> New Business<br />
<strong>Subject</strong> Venue</p></td>
</tr>
</tbody>
</table>

## Conditional Tokens

Conditional tokens are used to define conditional content within a document, where the conditional output is based upon one or more data conditions defined against the record being output.

### Usage

\[IF(Source=\<source\>,Path=\<path\>,Operator=\<operator\>,Value=\<value\>,Conditions=@(*\<hub conditionals>*))\]  
\[THEN\]

*Content to show if IF condition is met.*

\[ENDTHEN\]

\[ELSE\]

*Content to show if IF condition is not met.*

\[ENDELSE\]

\[ENDIF\]

| **Parameter**     | **Description**                                                                |
| ----------------- | ------------------------------------------------------------------------------ |
| **IF Parameters** |                                                                                |
| Source            | Source of data for Path.  See  <a name="#Token-Source-(Parameter)">Token Source (Parameter)</a>.  Defaults to Attribute. |
| Path              | Path to the attribute that is compared for the IF condition.                   |
| Operator          | Operator to use for comparison                                                 |
| Value             | Value to compare the attribute value against if the operator requires a value. |
| Conditions=@(*\<hub conditionals>*) | Optional Hub Conditional expression to use in place of the Path/Operator/Value for complex conditional expression evaluation.  See the [Hub Conditionals](/Partners/kBuilder/Guides/PortableView/CreatingPortableViewTemplates#hub-conditionals) section above. |

The \[IF()\] token defines the criteria for a condition to check. If evaluated to True, the content in the \[THEN\]/\[ENDTHEN\] token range is evaluated and output. Note that the \[THEN\]/\[ENDTHEN\] is required following an \[IF\] token.

The \[ELSE\] token defines an optional alternative conditional content to evaluate when the \[IF\] condition evaluates to FALSE. The \[ELSE\] token must be terminated by the \[ENDELSE\] token, followed by the \[ENDIF\] token. If no \[ELSE\]/\[ENDELSE\] tokens are used, the \[IF\] token must be terminated by the \[ENDIF\] token. The \[ELSE\] token does take a whole line when in use. This can cause spacing issues when using conditionals.

Conditionals can be nested, so it is possible for the \[IF\] content area to contain subsidiary \[IF\] statements.

Conditionals can contain other containers, such as tables and lists.

Note that conditionals presently do not support the use of standard Word tables in their content (i.e. in the THEN or ELSE content).  When standard Word tables are used in the conditional content, erroneous rendering occurs of the content.  Future enhancements to the Kahua Portable View feature set may address this short coming and will be detailed here when available.

### Examples

Template Content:

<table>
<tbody>
<tr class="odd">
<td><p>[IF(Source=Attribute,Path=CommunicationsLetter.CcParticipants,Operator=IsNotEmpty)]<br />
[THEN]<br />
<strong>CC:</strong> [AttributeList(Path=CommunicationsLetter.CcParticipants,Delimiter=",",Attribute=ShortLabel)]</p>
<p>[ENDTHEN]</p>
<p>[ELSE]</p>
<p><strong>No CC.</strong></p>
<p>[ENDELSE]</p>
<p>[ENDIF]</p></td>
</tr>
</tbody>
</table>

Template Output:

|  |
| ------------------------------------------------ |
| **CC:** Fred Jones, Sally Williams, Jeff Simpson |

## Line Reduction Token

The line break reduction token will attempt to remove the newline character at the position of the line reduction token, thereby reducing unwanted white space in the document.

### Usages

`[?]`

# Reference Information

## Date Format Strings

The following date format strings can be used with the
\[Date(Format=x)\] token:

| **Format String**                                                              | **Description**                                                | **Example**                      |
| ------------------------------------------------------------------------------ | -------------------------------------------------------------- | -------------------------------- |
| Standard date/time formats:                                                    |                                                                |                                  |
| d                                                                              | Short date pattern                                             | 6/15/2009                        |
| D                                                                              | Long date pattern                                              | Monday, Jun 15, 2009             |
| f                                                                              | Full date/time pattern (short time)                            | Monday, June 15, 2009 1:45 PM    |
| F                                                                              | Full date/time pattern (long time)                             | Monday, June 15, 2009 1:45:30 PM |
| g                                                                              | General date/time pattern (short time)                         | 6/15/2009 1:45 PM                |
| G                                                                              | General date/time pattern (long time)                          | 6/15/2009 1:45:30 PM             |
| M or m                                                                         | Month/day pattern                                              | June 15                          |
| O or o                                                                         | Round-trip date/time pattern                                   | 2009-06-15T13:45:30.000000-07:00 |
| R or r                                                                         | RFC1123 pattern                                                | Mon, 15 Jun 2009 20:45:30 GMT    |
| s                                                                              | Sortable date/time pattern                                     | 2009-06-15T13:45:30              |
| t                                                                              | Short time pattern                                             | 1:45 PM                          |
| T                                                                              | Long time pattern                                              | 1:45:30 PM                       |
| u                                                                              | Universal sortable date/time pattern                           | 2009-06-15 20:24:30Z             |
| U                                                                              | Universal full date/time pattern                               | Monday, June 15 2009 8:45:30 PM  |
| Y or y                                                                         | Year month pattern                                             | June, 2009                       |
| Custom date/time formats: (These are combined to form custom date/time output) |                                                                |                                  |
| d                                                                              | Day of month, from 1 to 31.                                    | 5                                |
| dd                                                                             | Day of month, from 01 to 31.                                   | 05                               |
| ddd                                                                            | Abbreviated day of the week                                    | Fri                              |
| dddd                                                                           | Full name of day of week.                                      | Friday                           |
| f                                                                              | Tenths of a second in date and time.                           | 6                                |
| ff                                                                             | Hundredths of a second in date and time.                       | 61                               |
| fff                                                                            | Milliseconds in date and time.                                 | 612                              |
| ffff                                                                           | Ten thousandths of a second in date and time.                  | 6123                             |
| fffff                                                                          | Hundred thousandths of a second in date and time.              | 61234                            |
| ffffff                                                                         | Millionths of a second in date and time.                       | 612345                           |
| fffffff                                                                        | Ten millionths of a second in date and time                    | 6123451                          |
| F                                                                              | If non-zero, tenths of a second in date and time.              | 6                                |
| FF                                                                             | If non-zero, hundredths of a second in date and time.          | 61                               |
| FFF                                                                            | If non-zero, milliseconds in date and time.                    | 612                              |
| FFFF                                                                           | If non-zero, ten thousandths of a second in date and time.     | 6123                             |
| FFFFF                                                                          | If non-zero, hundred thousandths of a second in date and time. | 61234                            |
| FFFFFF                                                                         | If non-zero, millionths of a second in date and time.          | 612345                           |
| FFFFFFF                                                                        | If non-zero, ten millionths of a second in date and time       | 6123451                          |
| g or gg                                                                        | The period or era                                              | A.D.                             |
| h                                                                              | 12 hour clock value from 1 to 12.                              |                                  |
| hh                                                                             | 12 hour clock value from 01 to 12.                             |                                  |
| H                                                                              | 24-hour clock value from 0 to 23.                              |                                  |
| HH                                                                             | 24-hour clock value from 00 to 23.                             |                                  |
| K                                                                              | Time zone information                                          |                                  |
| m                                                                              | Minute from 0 to 59.                                           |                                  |
| mm                                                                             | Minute from 00 to 59.                                          |                                  |
| M                                                                              | Month from 1 to 12.                                            |                                  |
| MM                                                                             | Month from 01 to 12.                                           |                                  |
| MMM                                                                            | Abbreviated name of month                                      |                                  |
| MMMM                                                                           | Full name of month                                             |                                  |
| s                                                                              | Second from 0 to 59.                                           |                                  |
| ss                                                                             | Second from 00 to 59.                                          |                                  |
| t                                                                              | First character of AM/PM designator.                           |                                  |
| tt                                                                             | AM/PM designator                                               |                                  |
| y                                                                              | Year from 0 to 99.                                             |                                  |
| yy                                                                             | Year from 00 to 99.                                            |                                  |
| yyy                                                                            | Year with minimum of three digits.                             |                                  |
| yyyy                                                                           | Four-digit year.                                               |                                  |
| yyyyy                                                                          | Five-digit year. Probably not our problem at that point.       |                                  |
| z                                                                              | Hours offset from UTC.                                         |                                  |
| zz                                                                             | Hours offset from UTC, with leading zero.                      |                                  |
| zzz                                                                            | Hours and minutes offset from UTC.                             |                                  |
| :                                                                              | Time separator                                                 |                                  |
| /                                                                              | Date separator                                                 |                                  |

## Number Format Strings

The following number format strings can be used with the
\[Number(Format=x)\] token:

<table>
<thead>
<tr class="header">
<th><strong>Format String</strong></th>
<th><strong>Description</strong></th>
<th><strong>Example</strong></th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>Standard numeric formats:</td>
<td></td>
<td></td>
</tr>
<tr class="even">
<td>F</td>
<td>Fixed point decimal</td>
<td>123.45</td>
</tr>
<tr class="odd">
<td>F#</td>
<td>Fixed point decimal with # of precision digits shown</td>
<td>F0: 123<br />
F1: 123.4<br />
F2: 123.45</td>
</tr>
<tr class="even">
<td>N</td>
<td>Numeric</td>
<td>1,234,567.89</td>
</tr>
<tr class="odd">
<td>N#</td>
<td>Numeric with # of precision digits shown</td>
<td>N0: 1,234,568<br />
N1: 1,234,567.9<br />
N2: 1,234,567.89</td>
</tr>
<tr class="even">
<td>D</td>
<td>Integer digits</td>
<td>123</td>
</tr>
<tr class="odd">
<td>D#</td>
<td>Integer digits with minimum number of digits</td>
<td>D: 123<br />
D4: 0123</td>
</tr>
</tbody>
</table>


# Creating a Template

Use the following steps to create a document template utilizing
Microsoft Word:

1.  Open Microsoft Word.

2.  Create the word document, entering the desired content and
    information.

3.  For entries in the document where an entity attribute should be used
    to fill in a value, specify the appropriate token as indicated in
    the prior document section.

4.  Save the template document.

5.  Upload the template document to the appropriate application
    configuration and domain/project in Kahua.

## Tips for Editing Templates in Microsoft Word

The Aspose Words product along with the use of the special tokens for controlling the insertion of data into Word template files is very sensitive to certain Word document structures and line endings which can be somewhat hard to understand.

### Formatting Marks
An important tool in understanding how Word has laid out a document is to use the option in Word to display formatting marks. This will then show characters in the Word document indicating where line breaks and spaces as well as paragraph and section breaks occur. Note various Kahua document tokens expect for Word paragraphs to bracket the tokens to guarantee how resulting document text is inserted into the resulting document. Turning on the display of special characters in Word helps to explicitly see these paragraph breaks as well as other information that may affect the appearance of the resulting document.

![screenshot_2024-02-22_165606.png](/screenshot_2024-02-22_165606.png)
*(Example of Word with formatting marks displayed)*

To enable the display of formatting marks in Word, go to the File -> Options dialog. On the Display tab in the section titled "Always show these formatting marks on the screen", click all the options to see these formatting characters.

![screenshot_2024-02-22_165900.png](/screenshot_2024-02-22_165900.png)

### AutoCorrect
When entering portable view tokens and their parameters, it is important to pay attention to the operation of the Word AutoCorrect feature.  This feature will automatically change some entered characters to a different character which can cause some tokens to have syntactically incorrect content, this is particularly a problem for the XML token types and Hub conditional expressions.  The setting that controls this can be found in the  File -> Options dialog on the Proofing -> AutoCorrect Options dialog:
![screenshot_2024-02-22_171035.png](/screenshot_2024-02-22_171035.png)
In particular, the settings for "Replace as you type" for the "Straight quotes" with "smart quotes" will replace the entered double quote with the smart or typographer quote, as shown here:
![screenshot_2024-02-22_171245.png](/screenshot_2024-02-22_171245.png)
When used in a token, it is important to use a straight quote.  You can disable this feature using the settings, or you can undo an AutoCorrect by entering Ctrl-Z after typing the double quote which will restore the smart quote to the double quote or whatever auto correct replacement was performed.  A similar replacement is done with hyphens for a dash.


### Line Spacing
Another important item to be aware of that affects the line spacing of information in a Word document can be seen in the Page Layout section of the ribbon in the area called Spacing, in the "After" field. Typically, after a paragraph break, this automatically sets the "After" spacing to 10 points. This has the effect of adding additional white space between lines in a document. To prevent this, select a paragraph, go to the Page Layout -\> Spacing section and change the "After" spacing to 0. You may need to do this in multiple areas of your template document.
![screenshot_2024-02-22_170226.png](/screenshot_2024-02-22_170226.png)

Using the tables in Word can help with spacing and layout. Tabbing can cause issues and not allow the view to line up correctly. Instead creating a table to put the tokens in, allows you to move and space those tokens easier along the page.

### Table Row and Column Sizing
A common issue when formatting a Word table with a lot of content that includes the various tokens is that row heights or column widths are larger than desired.  As content is typed into a cell, this tends to expand the height and width and may result in row heights or column widths that are excessive.  These properties of the table layout can be controlled by using the table layout dialog to adjust the row heights and column widths to provide a more aethetically pleasing appearance:
![screenshot_2024-02-22_172627.png](/screenshot_2024-02-22_172627.png)
(Row height adjustment)

![screenshot_2024-02-22_172724.png](/screenshot_2024-02-22_172724.png)
(Column width adjustment)


# Templates and Manufactured Values

Applications and reports sometimes require the determination of calculated or manufactured values which cannot be stored as part of the
static information on an entity, for example, if a calculated value is a time dependent quantity. To support this in templates, the following technique should be used so that template tokens are available for template designers to access these calculated values:

*Note that this information is still accurate but relies upon Legacy infrastructure. This will be updated to reference some more recent Hub usages that simplify use of calculated information in portable views.*

1.  A portable view should reference a data source in the portable view definition. For example:

```XML
<PortableViews>  
  <PortableView Name="kahua_KitchenSink.KitchenSinkReportView"  
    Label="KitchenSinkReportView"  
    DefaultTemplate="KitchenSinkTemplate1"  
    DefaultLogoOption="ContactLogoOption">  
    <LogoOptions>...  </LogoOptions>  
    <DataSources>  
      <DataSource 
        Ref="kahua_KitchenSink.KitchenSinkItemDataForPortableView" >  
        <Parameters>  
          <Parameter Name="Id" Path="KitchenSinkItem.Id" />  
        </Parameters>  
      </DataSource>  
    </DataSources>  
  </PortableView>  
</PortableViews>
```

Note that a data source used on a portable view should include a parameter collection that passes in the path on the incoming entity for attributes that are used in the data source for identifying the entity being reported.

2.  The data source referenced in (1) above should define attributes in the Select collection that are populated by the platform script
    referenced by the data source. For example:
```XML
<DataSource Name="KitchenSinkItemDataForPortableView" Access="Read">  
  <PlatformScript Script="kahua_KitchenSink.AddAttributesToDataSource" />  
  <Parameters>  
    <Parameter Value="" Name="Id" />  
  </Parameters>  
  <Select>  
    <Attribute Name="KitchenSinkItem.Id" DataType="Integer" />  
    ...  
    <!-- These 2 fields are inserted by the platform script called by this data source -->  
    <Attribute Name="KitchenSinkItem.BogusA" DataType="Text" />  
    <Attribute Name="KitchenSinkItem.BogusB" DataType="Currency" />  
  </Select>  
  <From>  
    <Entity EntityDef="kahua_KitchenSink.KitchenSinkItem"  
      Alias="KitchenSinkItem" />  
  </From>  
  <Where>  
    <Attribute Name="KitchenSinkItem.Id">  
      <Equals Parameter="Id" />  
    </Attribute>  
  </Where>  
</DataSource>
```

3.  The platform script referenced by the data source in (2) above should add the attributes as defined in the Select collection from
    the data source. For example:
```XML
<Script Name="AddAttributesToDataSource" >  
  <Body>  
    <![CDATA[  
    function OnAfterGet(platform, getDataSourceContext)  
    {  
      if ( (getDataSourceContext.EntitySet == null) ||  
         (getDataSourceContext.EntitySet.Entities == null) ||  
         (getDataSourceContext.EntitySet.Entities.Count == 0))  
      {  
        return;  
      }  
      var ksEntity = getDataSourceContext.EntitySet.Entities[0];  
      var bogusAString = "This is bogus data.";  
      var bogusBCurrencyValue = new  
         kahua.kdk.entity.data.currency.CurrencyValue();  
      bogusBCurrencyValue.Amount = 100.0;

      ksEntity.AddAttribute('KitchenSinkItem.BogusA',  
        kahua.kdk.entity.EntityAttributeDataType.Text, bogusAString);  
      ksEntity.AddAttribute('KitchenSinkItem.BogusB',  
        kahua.kdk.entity.EntityAttributeDataType.Currency,  
        bogusBCurrencyValue);  
    }  
    ]]>  
  </Body>  
</Script>
```

# Deprecated Features
This section contains descriptions of features that have been deprecated or replaced with newer functionality to better achieve the intended behavior of the portable view feature.  Unless otherwise indicated, the deprecated feature is still supported, but is otherwise not maintained and the newer, recommended technique will be indicated.

## Project Metadata Tokens

> The project metadata tokens have been replaced with a more flexible technique that provides a wider range of capabilities.  To output any project level data in a portable view, use any of the token types that support the Source=Project parameter rather than the project metadata tokens described below.  See the Token Source (Parameter) section and the Attribute Tokens section.<br />
The benefit of this technique is that it eliminates the requirement to update the project app or extensions to include the EntityDefToken entry for a new attributes as described below in the Project Token Definition section.  Any of the tokens that support Source=Project can be used to access the project level data without any updates to the apps. <br />
Note that portable view templates utilizing the current project metadata tokens will continue to operate as expected.
{.is-warning}

The project metadata tokens provide the abilty to output information about the current project that the current entity exists in.  In general this should allow access to any attributes on the current project or portfolio manager object, however this requires that the project or project extension provide token definitions on the project entitydef in a section called "\<EntityDefTokens\>" as described later in this section.

Here are some tokens available from the base project app, see the Common Tokens section in Kahua configuration for the complete listing:

| **Token**                   | **Description**                                                                                                        |
| --------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| \[ProjectNumber\]           | The number assigned to the project   |
| \[ProjectName\]             | The name assigned to the project   |
| \[ProjectAddress1\]         | First address line for the project  |
| \[ProjectOwner.LastName\]   | Last name of contact assigned to the Project Owner roster role |

An example screenshot of the Common Tokens tab in app configuration in the Kahua hosts:
![projectcommontokens.png](/guides/portableview/projectcommontokens.png)


### Project Token Definition
Project tokens are defined in the kahua_Project app and extensions of the project app, such as Portfolio Manager that are used to dynamically emit the set of tokens that can be used to output project attribute information in portable views.  These tokens will be shown in the Common Tokens tab of the Portable View configuration for any app in Kahua.  If an attribute is available in the project app or extension, but not found in the Common Tokens area, then most likely it is missing from the EntityDefTokens section for the project or extension in which the attribute is defined.

EntityDefTokens is a section defined on the Project entitydef that will provide a token string that maps to an attribute on the project entity.  Below is an excerpt from the base Project app:
![projectentitydeftokens.png](/guides/portableview/projectentitydeftokens.png)

An EntityDefToken consists of the following pieces of information:

 `<EntityDefToken Name="Number" Path="Project.Number" Token="ProjectNumber" />`
 Name - the name of the token
 Path - the path to the attribute on the entity
 Token - the token content that will be used in a portable view template e.g. [Token]
 
 All tokens defined in the project app hierarchy will be included as an available token for use in portable views.  This means that for Portfolio Manager installations, all tokens defined in the base Project app are included (as shown above) as well as the additional tokens unique to Portfolio Manager (excerpt shown below):
 
 ![portfoliomanagertokens.png](/guides/portableview/portfoliomanagertokens.png)


### Usage

To use any of the Project Metadata tokens, specify as shown
above.

### Examples

| **Template Content:**       | **Template Output:**                  |
| --------------------------- | ------------------------------------- |
| \[ProjectNumber\]           | 0001-PRJ-A73                          |
| \[ProjectAddress1\]         | 123 Main Street                       |
| \[ProjectOwner.LastName\]   | Williams                              |
| \[ProjectName\]             | 123 Main Street Refurbish             |



