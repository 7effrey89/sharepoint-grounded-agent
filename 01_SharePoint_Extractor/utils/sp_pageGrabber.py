# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

# <UserAuthConfigSnippet>
from configparser import SectionProxy
from azure.identity import DeviceCodeCredential
from msgraph import GraphServiceClient
from msgraph.generated.users.item.user_item_request_builder import UserItemRequestBuilder
from msgraph.generated.users.item.mail_folders.item.messages.messages_request_builder import (
    MessagesRequestBuilder)
from msgraph.generated.users.item.send_mail.send_mail_post_request_body import (
    SendMailPostRequestBody)
from msgraph.generated.models.message import Message
from msgraph.generated.models.item_body import ItemBody
from msgraph.generated.models.body_type import BodyType
from msgraph.generated.models.recipient import Recipient
from msgraph.generated.models.email_address import EmailAddress
from azure.identity import ClientSecretCredential
from msgraph.generated.sites.sites_request_builder import SitesRequestBuilder
from kiota_abstractions.base_request_configuration import RequestConfiguration
from msgraph.generated.sites.item.pages.pages_request_builder import PagesRequestBuilder
from msgraph.generated.sites.item.pages.item.graph_site_page.graph_site_page_request_builder import GraphSitePageRequestBuilder
import os
import json

class Graph:
    settings: SectionProxy
    device_code_credential: DeviceCodeCredential
    user_client: GraphServiceClient

    def __init__(self, config: SectionProxy):
        self.settings = config
        client_id = self.settings['clientId']
        tenant_id = self.settings['tenantId']
        client_secret = self.settings['secret']
        # graph_scopes = self.settings['graphUserScopes'].split(' ')

        #https://stackoverflow.com/questions/51781898/aadsts70011-the-provided-value-for-the-input-parameter-scope-is-not-valid
        # You are using the client credential flow here, which means that you cannot dynamically request scopes. 
        # You must configure your required permission scopes on your app registration in apps.dev.microsoft.com, 
        # then you set the value of scope in your code to https://graph.microsoft.com/.default.
        graph_scopes = ['https://graph.microsoft.com/.default'] 

        # self.device_code_credential = DeviceCodeCredential(client_id, tenant_id = tenant_id, client_secret = client_secret)
        self.client_credential = ClientSecretCredential(
                tenant_id=tenant_id,
                client_id=client_id,
                client_secret=client_secret
            )
        # self.user_client = GraphServiceClient(self.device_code_credential, graph_scopes)
        self.user_client = GraphServiceClient(self.client_credential, graph_scopes)
# </UserAuthConfigSnippet>



    # <MakeGraphCallSnippet>
    async def make_graph_call(self, sharepointTitle):

        #find site
        query_params = SitesRequestBuilder.SitesRequestBuilderGetQueryParameters(
		    search = sharepointTitle,
            select = ["id","name","weburl","lastModifiedDateTime"]
        )

        request_configuration = RequestConfiguration(
            query_parameters = query_params,
        )

        Site = await self.user_client.sites.get(request_configuration = request_configuration)
        # print(Site)

        siteID = Site.value[0].id #id='m365x02897599.sharepoint.com,f5396752-1681-4405-a5ea-67370e80ad4a,ea9206ea-7449-4481-9034-23b3b6c36ff4'
        siteLastModifiedDateTime = Site.value[0].last_modified_date_time #DateTime(2024, 9, 12, 7, 39, 20, tzinfo=Timezone('UTC'))
        siteName = Site.value[0].name #name='MyFirstSharePointSite'
        siteUrl = Site.value[0].web_url #weburl='https://m365x02897599.sharepoint.com/sites/MyFirstSharePointSite'

        # Extract site details
        site_details = {
            "id": Site.value[0].id,
            "name": Site.value[0].name,
            "webUrl": Site.value[0].web_url,
            "lastModifiedDateTime": (
                Site.value[0].last_modified_date_time.isoformat()
                if hasattr(Site.value[0].last_modified_date_time, "isoformat")
                else str(Site.value[0].last_modified_date_time)
            )
        }

        # Save each page as its own JSON file
        output_dir = r"./01_SharePoint_Extractor/output"
        os.makedirs(output_dir, exist_ok=True)
        site_output_path = os.path.join(output_dir, "graph_output_site.json")
        with open(site_output_path, "w", encoding="utf-8") as f:
            json.dump(site_details, f, ensure_ascii=False, indent=2)
        print(f"Saved site details to {site_output_path}")

        ############################################################ PAGE OVERVIEW #######################################################################################
        #overview of pages in the site:
        query_params = PagesRequestBuilder.PagesRequestBuilderGetQueryParameters(
		select = ["id","name","title","weburl","lastModifiedDateTime"],
        )

        request_configuration = RequestConfiguration(
            query_parameters = query_params,
        )

        Pages = await self.user_client.sites.by_site_id(siteID).pages.get(request_configuration = request_configuration)
        # print(Pages)

        pages_list = []
        for page in Pages.value:
            # Convert DateTime objects to ISO strings
            last_modified = (
                page.last_modified_date_time.isoformat()
                if hasattr(page.last_modified_date_time, "isoformat")
                else str(page.last_modified_date_time)
            )

            page_details = {
                "id": page.id,
                "name": page.name,
                "webUrl": page.web_url,
                "lastModifiedDateTime": last_modified
            }

            # Append each page's details to the list
            pages_list.append(page_details)

        # Save all pages to a single JSON file
        output_dir = r"./01_SharePoint_Extractor/output"
        os.makedirs(output_dir, exist_ok=True)
        pages_output_path = os.path.join(output_dir, "graph_output_site_pages.json")
        with open(pages_output_path, "w", encoding="utf-8") as f:
            json.dump(pages_list, f, ensure_ascii=False, indent=2)
        print(f"Saved all pages details to {pages_output_path}")

        ############################################################ PAGE #######################################################################################


        pages_detail_list = []

        for page in Pages.value:
            # get page content
            query_params = GraphSitePageRequestBuilder.GraphSitePageRequestBuilderGetQueryParameters(
            expand = ["canvasLayout"],
            )

            request_configuration = RequestConfiguration(
                query_parameters = query_params,
            )

            result = await self.user_client.sites.by_site_id(siteID).pages.by_base_site_page_id(page.id).graph_site_page.get(request_configuration = request_configuration)

            # Convert DateTime objects to ISO strings
            last_modified = (
                page.last_modified_date_time.isoformat() 
                if hasattr(page.last_modified_date_time, "isoformat") 
                else str(page.last_modified_date_time)
            )

            # Try to convert canvas_layout to dict, else use str
            try:
                canvas_layout = result.canvas_layout.to_dict()
            except AttributeError:
                try:
                    canvas_layout = dict(result.canvas_layout)
                except Exception:
                    canvas_layout = str(result.canvas_layout)

            page_details_detail = {
                "Page_ID": page.id,
                "Page_Name": page.name,
                "Page_Title": page.title,
                "Page_URL": page.web_url,
                "Last_Modified": last_modified,
                "Page_Description"  : result.description,
                "Page_CanvasLayout" : canvas_layout
            }
            
            # print(f"Page Title: {page.title}")
            # print(f"Page URL: {page.web_url}")
            # print(f"Description: {result.description}")
            # print(f"Last Modified Date: {last_modified}")
            # print(f"Canvas Layout: {canvas_layout}")

            #append to  a list
            pages_detail_list.append(page_details_detail)

        # Save each page as its own JSON file
        output_dir = r"./01_SharePoint_Extractor/output"
        os.makedirs(output_dir, exist_ok=True)
        for page in pages_detail_list:
            # Use page title or name as filename, sanitized for filesystem
            filename = f"graph_output_{page['Page_Title']}.json"
            # Remove or replace characters not allowed in filenames, but keep the .json extension
            safe_filename = "".join(c for c in filename if c.isalnum() or c in (' ', '_', '-', '.')).rstrip()
            output_path = os.path.join(output_dir, safe_filename)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(page, f, ensure_ascii=False, indent=2)
            print(f"Saved page to {output_path}")

        return None
    
    # </MakeGraphCallSnippet>
