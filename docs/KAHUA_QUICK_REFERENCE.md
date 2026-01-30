# Kahua Portable View Quick Reference

## What is a Portable View Template?

A Word document with placeholder tokens that Kahua replaces with real data when rendered. 
Templates should be **clean, production-ready documents** - no meta-text like "Specification" or "Design Guide".

---

## Core Token Syntax

### Attribute (Text)
```
[Attribute(FieldName)]
[Attribute(Parent.Child)]
```

### Date
```
[Date(Source=Attribute,Path=DueDate,Format="d")]
```
- `"D"` = Long date (Tuesday, January 28, 2026)
- `"d"` = Short date (1/28/2026)

### Currency
```
[Currency(Source=Attribute,Path=Amount,Format="C2")]
```

### Number
```
[Number(Source=Attribute,Path=Quantity,Format="N0")]
```
- `"N0"` = Integer with commas (1,234)
- `"F2"` = 2 decimal places (1234.56)
- `"P1"` = Percent with 1 decimal (45.5%)

### Boolean
```
[Boolean(Source=Attribute,Path=IsComplete,TrueValue="Yes",FalseValue="No")]
```

---

## System Placeholders

```
[ProjectName]
[ProjectNumber]  
[CompanyLogo(Width=100,Height=50)]
[ReportModifiedTimeStamp]
```

---

## Collections/Tables

### Start Table
```
[StartTable(Name=ItemsTable,Source=Attribute,Path=Items,RowsInHeader=1)]
```

### Table Row (repeat for each item)
```
[Attribute(Description)]    [Currency(Source=Attribute,Path=Amount)]
```

### End Table
```
[EndTable]
```

---

## Conditional Display

Add `[?]` suffix to make content show only when field has value:
```
[Attribute(OptionalField)][?]
```

---

## Example Template Structure

A clean RFI template document would contain:

```
[CompanyLogo(Height=60,Width=60)]

[Attribute(RFI.Number)]
[Attribute(RFI.Subject)]

Status: [Attribute(RFI.Status)]          Priority: [Attribute(RFI.Priority)]
Date: [Date(Source=Attribute,Path=RFI.Date,Format="d")]
Due: [Date(Source=Attribute,Path=RFI.DueDate,Format="d")]

Question
[Attribute(RFI.Question)]

Response
[Attribute(RFI.Response)]
```

**NOT** a document describing what the template should look like.
