# Portable Views Start to Finish

## Overview of Portable Views

### What is a Portable View?

A *Portable View* is the rendered, PDF view of an entity, or document, in Kahua. There are two main types of Portable Views: Stimulsoft Portable Views and Microsoft Word Portable Views. 

#### Stimulsoft Portable Views

Stimulsoft Portable Views are created with Kahua's Stimulsoft Report editor and are defined in the app definition. In order to edit a portable view, you must edit the app definition. 

#### Word Portable Views

Word Portable Views are edited with Microsoft Word or with our Portable View Template Editor. The available tokens in the configuration tools are defined with a datasource in the PortableView node of the app definition. Word Portable Views are not installed with the app definition; they are uploaded in configuration after app installation.

### Where are Portable Views Defined in the app definition?

Portable Views are defined and managed in a few different areas of the app definition. 

`<Reports>`
![portable_views_image1.png](/development/featuredocs/portableviews/portable_views_image1.png)
The Reports node allows a user to create reports and portable views embedded in the app definition. Reports of Type "View" can be used as a portable view. 

`<PortableViews>`
![portable_views_image2.png](/development/featuredocs/portableviews/portable_views_image2.png)
The App def level Portable View node contains a datasource that defines the tokens available in the portable view / token configuration. 
**NOTE: Word Portable Views do not require the token be defined in the data source to render correctly, this is only to display the tokens in configuration for reference by the user.
 
`<Hubdef.PortableViews>`
![portable_views_image3.png](/development/featuredocs/portableviews/portable_views_image3.png)
The Portable View Node in the hubdef defines which reports(s) - defined in the app def `<Report>` Node to make available to the user as a portable view. It further defines the actions availabe on the Portable View. 
* View - Displays the Portable View when a user selects the "View" action.
* Message  - ??
* Send -  Attaches the portable view to an email when the user selects the "Send" Action.

## How to Create a Stimulsoft Portable View

In order to create and view a Stimulsoft Portable View, follow the below steps:
1. Create a "Legacy Report"
2. In the inspector, select "View" for Type
2. Define the report in the Stimulsoft Report Editor
3. Reference the Report in the Hubdef Portable View Node

### Creating the Report Definition
* Right-Click on the Reports node in the project explorer, and select _Add Report_. The _New Report_ dialog will appear.
* Enter a name for the report. Names in Kahua never have spaces. Common naming convention for stimulsoft portable views include __[Entity]View__ or __[Entity]PV__. 
* Choose **Legacy Report** for the report type.
* Open the drop-down and rename the child Report to the same name as the Legacy Report. The “(Legacy Report)” and “(Report)” **must have the same name** for the portable view to function. 
* In the Inspector on the "(Report)", scroll down to the very bottom and choose **View** for **Type**

#### Technical Details
* The stimulsoft report was created. Stimulsoft reports are xml files. As a result, the stimulsoft report defining xml is located in the Reports tab.

### Generating the Data Source
1. Open the report in Stimulsoft by double clicking on it. 
1. Open the drop-down for the report in the Project Explorer and right click Data Sources.
1. Choose **Generate Data Source…**. 
1. Choose the Entity Definition for the View. This is typically the primary entity of the app. 
* A datasource was generated automatically by kBuilder. This datasource selects data from the entity selected and provides it to the stimulsoft report definition.
  * Some apps on the repo will reference a datasource in the legacy DataSources node of the app def vs defining one in the Reports node.
  * Some app developers prefer to define their own data sources vs relying on the kBuilder generated data sources. 
  * You should be able to observe a one to one relationship of the items in the datasource select statement and the columns in the stimulsoft report dictionary.


### Defining the Report with Stimulsoft
This section will not define the details of using stimulsoft, refer to separate documentation on creating reports. 

To create a basic report, do the following:

1. On the dictionary tab of the report writer, expand the __DataSources__ then __Result__. You should see a Data Source named the same as the entity name selected when creating the report. Expand the DataSource with your entity name to view the attributes available for the report.
2. Drag the attributes you would like to see on your report over to the report layout and style as desired. 
3. When the report is complete, save as required. 

### Reference the Report in the Hubdef Portable View Node

If you install the app now, having completed steps one and two noted above, you will not be able to render the portable view. The report is defined however, the HubDef must define how the portable view is to be displayed and used by the user. To define the hubdef portion of the portable view:
1. Right-Click on the Portable View Node _Inside_ the HubDef. Select _Add Portable View_.

2. Name your portable view. It is best practice to name the portable view, the same name as the report and the app def portable view (discussed later).

3. Define the following attributes for the portable view:

	| Attribute | Description |
	| :----------------- | :----------- |
	| Entity Defintion | This defines the entity the portable view is displaying, this should match the same entity selected on the report. |
	| Entity Path | _OPTIONAL_ |
	| Label | The Portable View Label displays in portable view configuration as well as the view drop down menu in the case there are multiple portable views in the hubdef with _View_ Usage. |
	| Name | Name of the HubDef Portable View. This should match the portable view name in the app def and the report name. |
	| Report | Stimulsoft Report in the App Def '<Reports>' section that will render. |
	| Usage | View will enable the portable view to be viewed when user selects the view action. Send attaches the portable view to messages when user selects the Send action. Message??? |
 
4. With the portable view defined in the hub definition, the portable view will now appear in messages with Send button, and render on selection of view button.

>**IMPORTANT NOTE! - KAHUA CACHES PORTABLE VIEW PDFS AFTER VIEWING. IT IS ALWAYS NECESSARY TO MODIFY THE RECORD AND SAVE IN ORDER FOR KAHUA TO RE-RENDER THE PORTABLE VIEW.**
{.is-info}


