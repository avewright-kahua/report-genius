# Adding Word Portable View Template Walkthrough
This document is a walkthrough to add a basic Word Portable View Template to the Observations App.

**Note:** This walkthrough assumes that you have already created the Word Portable View Template. Please see at [Creating Portable View Templates](https://build.kahua.com/en/Partners/kBuilder/Guides/PortableView/CreatingPortableViewTemplates) if not created yet.
## Step 1 - Define Portable View at App Level
At the app level, right click on **"Portable Views"** and create a new one.

For Word Portable Views, the name needs to be `[AppName].[Word_PV_Name]`. This naming convention adds the Word Portable View (`Word_PV_Name`) to the app (`AppName`).
- Example: This walkthrough adds a Word Portable View to the BrandonP_Observations app
  - Therefore, the Portable View name would be `BrandonP_Observations.TestWordPV` 

<img src="/portable_view/adding-word-pv-walkthrough/wordpvstep1a.gif" style="width:45%;">

Unfortunately, the inspector does not prompt for a label. A label needs to be added in the XML.
<img src="/portable_view/adding-word-pv-walkthrough/wordpvstep1b.gif" style="width:45%;">


## Step 2 - Define Portable View at Hub Level
Defining Portables Views at the hub definition defines which Portable Views to make available to the user.

In hub definitions in your desired hub definition (in the walkthrough it's the **NoWorkflow** hub definition), right click on **"Portable Views"**, and give it a name.
<video src="/portable_view/adding-word-pv-walkthrough/wordpvstep2a.mp4" controls style="max-width: 1000px; height: auto;"></video>

Defining Portable Views at the hub definition also defines the actions availabe on the Portable View via the `Usage` property.

- View - Displays the Portable View when a user selects the "View" action.
- Message - Allows the Portable View to be attached to a message via message directive.
- Send - Attaches the Portable View to an email when the user selects the "Send" Action.

Since adding the `Usage` property is not supported by kBuilder 2025 yet, you need to assign it in the XML.
<img src="/portable_view/adding-word-pv-walkthrough/wordpvstep2b.gif" style="width:60%;">

## Step 3 - Adding the Portable View in Configuration
Install your app to your desired environment and domain.

Click on the 3 dots next to the app name and go to the configuration.
<img src="/portable_view/adding-word-pv-walkthrough/wordpvstep3a.png" style="width:25%;">

Make your way to the **Templates** section under the **Portable Views** tab.
<img src="/portable_view/adding-word-pv-walkthrough/wordpvstep3b.png" style="width:30%;">

In this walkthrough, I will use the Word Portable View Template below. Please see at [Creating Portable View Templates](https://build.kahua.com/en/Partners/kBuilder/Guides/PortableView/CreatingPortableViewTemplates) if not created yet.
<img src="/portable_view/adding-word-pv-walkthrough/wordpvstep3d.png" style="width:45%;">

After adding the Word Portable View Template, make sure the **Preview Status** is "Rendered". Again, if you haven't created a template yet, please see at [Creating Portable View Templates](https://build.kahua.com/en/Partners/kBuilder/Guides/PortableView/CreatingPortableViewTemplates).
<img src="/portable_view/adding-word-pv-walkthrough/wordpvstep3c.png" style="width:40%;">

## Step 4 - Assign Template in the View
After adding the Word Portable View Template:
1) <u>**Set the Template Override**</u>
      - Navigate to Templates Configuration.
      - Click Override.
      - Check the box next to your Word Portable View template.

2) <u>**Make It the Default View**</u>
      - Go to Views.
      - Select your Word Portable View template as the default template.

![wordpvstep4.gif](/portable_view/adding-word-pv-walkthrough/wordpvstep4.gif)


## Step 5 - Check Portable View in App
Make sure to save your changes before going back to the app.

Go to your desired record and enjoy your new Word Portable View.
<img src="/portable_view/adding-word-pv-walkthrough/wordpvstep5.gif" style="width:45%;">