# Portable View Parent and Child Multiple Entities

## Overview
This page is for creating and using mulitple entities in a portable view (PV).
It will walk through setting up the PV, adding the extra entities, and creating 
a relation bewtween the entites.

### Entites
There will need to be multiple entities in your application such as these; 
ParentRecord and ChildRecord.

![figure1.png](/portable_view/multiple_entities/figure1.png)

## Setting up the Portable View
Create a record in your app. Name it, put it as type ???View???, and make the 
entity definition the parent entity of your app.

![figure2.png](/portable_view/multiple_entities/figure2.png)

## Adding an Extra Entity
When you look into data sources for the PV you will only see the parent entity. 
We need to add another entity to the Data Source by going down the project 
explorer, into ???reports???, your report, ???data sources???, the parent entity, and 
then into the ???select??? section. You should see an attribute for the child entity 
short label.

![figure3.png](/portable_view/multiple_entities/figure3.png)

You will want to right click this and Generate Attributes. This will expand your 
attributes for the child entity and create the new data source for the child entity 
in the PV record page.

![figure4.png](/portable_view/multiple_entities/figure4.png)

![figure5.png](/portable_view/multiple_entities/figure5.png)

> It may help to clean up all the un useful attributes in the ???select??? section. 
This will allow finding the correct attributes to be easier as you create the 
PV. The best way to do this is by going into the ???Modify Definition??? of the 
app and then delete any attributes will do not need. You can do this for both 
of the entities.
{.is-info}

## Creating the Relation between Entities
Now we will need to create a relation between the two entities. In order to do this though 
we will need to add a new column to the child entity that will relate back to the parent. 
Right click the child entity data source and select new column. The ???Name in Source??? of 
this column has to be \<YourParentEntityName\>_Id, for this example it would be ???ParentRecord_Id???. 
The ???Name??? and ???Alias??? will be the same, and the type will be ???long???.

![figure6.png](/portable_view/multiple_entities/figure6.png)

Now we can create the relation. Right click the child entity data source again and select 
???New Relation?????? this time. Name the relation, and then for the child entity select the parent
entity Id and for the parent entity select the Id.

![figure7.png](/portable_view/multiple_entities/figure7.png)

## Placing and Testing
Now you can drag and drop the entities on the PV and set it up the way you would 
like it. Then just save and install the app to an environment and make sure it is 
working properly.

![figure8.png](/portable_view/multiple_entities/figure8.png)

![figure9.png](/portable_view/multiple_entities/figure9.png)