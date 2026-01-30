# Kahua Portable View Syntax Reference

Extracted from real customer templates (screenshots).

## Basic Attribute Syntax

```
[Attribute(FieldName)]
[Attribute(Parent.ChildField)]
[Attribute(Meeting.Subject)]
[Attribute(DailyReport.Weather.Weather)]
```

## Date Fields

```
[Date(Path=DueDate,Format="D")]
[Date(Path=DailyReport.Date,Format="D")]
[Date(Source=Attribute,Path=Meeting.Date,Format="D")]
```

Format options:
- `"D"` = Long date (Tuesday, January 28, 2026)
- `"d"` = Short date (1/28/2026)

## Currency Fields

```
[Currency(Path=ScheduledValue)]
[Currency(Path=BalanceToFinish)]
[Currency(Source=Attribute,Path=Field,Format="C2")]
```

## Number Fields

```
[Number(Format=F2,Source=Attribute,Path=Reading)]
[Number(Path=TotalPercent,Format="F0")]%
```

## System Placeholders

```
[ProjectName]
[ProjectNumber]
[DomainPartitionName]
[ContractNo]
[CompanyLogo(Width=100,Height=50)]
[ReportModifiedTimeStamp]
[PartitionTimeZoneAbbreviated]
```

## List/Table Syntax

### Simple List
```
[StartList(Name=Items,Source=Attribute,Path=Meeting.MeetingItems,Sort=Type,Descending;Number,Ascending)]
[StartContentTemplate]
  ... content per item ...
[EndContentTemplate][?]
[EndList][?]
```

### Table with Grouping
```
[StartTable(Name=TableName,Source=Attribute,Path=Items,RowsInHeader=4)]
  <StartTable.Sorts>
    <Sort Path="ContractItem.Number" Direction="Ascending" />
  </StartTable.Sorts>
  <StartTable.Grouping GroupMode="SubTotal" GroupBy="ContractItem.Id" TotalMode="Summary">
    <Grouping.Operations>
      <Sum>
        <Sum.Paths>
          <Path SourcePath="ScheduledValue" TargetPath="SumScheduledValue" />
        </Sum.Paths>
      </Sum>
    </Grouping.Operations>
  </StartTable.Grouping>
</StartTable>
```

### Simple Table
```
[StartTable(Name=WorkPerformedTodayTable,Source=Attribute,Path=DailyReport.Companies,ShowEmptyTable="True",RowsInHeader=1)]
... table rows with [Attribute(...)] placeholders ...
[EndTable]
```

## Attribute List (Comma-separated)

```
[AttributeList(Path=Companies,Delimiter=", ",Attribute=Company.ShortLabel)]
```

## Conditional Display

```
[Attribute(Field)][?]
```
The `[?]` suffix makes the field optional/conditional.

## CRITICAL: What a Template IS vs IS NOT

### A template IS:
- A Word document (DOCX) with actual Kahua placeholder text embedded
- Professional layout with tables, borders, formatting
- Literal `[Attribute(Number)]` text that Kahua replaces at runtime

### A template is NOT:
- Documentation explaining placeholder syntax
- Markdown describing how to build a template
- Instructions for the user

## Example: Correct RFI Template Structure

The DOCX file should contain this literal content (with Word formatting):

```
┌──────────────────────────────────────────────────────────────┐
│ [CompanyLogo(Width=100,Height=50)]                    RFI    │
│                                                              │
│ RFI No: [Attribute(Number)]                                  │
│ Subject: [Attribute(Subject)]                                │
├──────────────────────────────────────────────────────────────┤
│ Status: [Attribute(Status)]                                  │
│ Due: [Date(Source=Attribute,Path=DueDate,Format="d")]        │
├──────────────────────────────────────────────────────────────┤
│ QUESTION                                                     │
│ [Attribute(Question)]                                        │
├──────────────────────────────────────────────────────────────┤
│ RESPONSE                                                     │
│ [Attribute(Response)]                                        │
└──────────────────────────────────────────────────────────────┘
```

NOT this kind of output:

```
# RFI Template

## Placeholder Reference
- [Attribute(Number)] - The RFI number
- [Attribute(Subject)] - The subject line
...
```
