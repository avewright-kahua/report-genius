# Overview
This document will provide a complete step-by-step walkthrough of how to create a basic portable view within Microsoft Word, upload the portable view as a template, configure an app to use it, and ultimately how to view it within the app as a report.

More detailed examples to come later.

# Creation of the Portable View
Many details here will be directly drawn from the [Creating Portable View Templates](https://build.kahua.com/en/Partners/kBuilder/Guides/PortableView/CreatingPortableViewTemplates) page. Given the complexity of that page, this page aims to simplify into a minimum viable product, enough to get a foot in the door.

# Configuration
In order to configure your app to use Word Portable View templates, the app must have at least one portable view defined in the Portable Views section of the app definition. Having a Portable View defined in the HubDef.PortableViews section is not required.

Once you have defined a PV within the app and installed it, the rest of the configuration is done within Kahua. Open your app in Kahua, then right click your app and select "Configure". Once the configuration page loads, you will select the "Portable Views" tab, then the "Templates" subtab. Click "Add". Select a View, give the template a short but descriptive name, and then click "Select File" to upload your Word document from the previous section. Click "OK".

Next, go to the "Templates Configuration" subtab. You may need to switch from "Inherit" to "Override". Make sure your newly created template has the "Include" box next to it checked, and hit "Save".

Now, go to the "Views" subtab. You may need to switch from "Inherit" to "Override". You can now select your new Template as the "Default Template" for your chosen view, then click "Save".

Note: It is possible to set the default template for a view within kBuilder, but it may still be necessary to do the rest of these steps within Kahua.

# Viewing the Portable View
Once you've configured the PV, it should be as simple as selecting an item in your log view and clicking the "View" button.

# Example Walkthrough (Legacy kBuilder)
Click on the link below to download tutorial video:
[Adding a word portable view.mp4](/portable_view/adding_a_portable_view_1.mp4)