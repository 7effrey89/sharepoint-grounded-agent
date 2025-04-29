import json
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import os
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

# Load environment variables from .env file
load_dotenv()

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

async def getSiteId(self, sharepointTitle):

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

    fullSiteId = Site.value[0].id #id='m365x02897599.sharepoint.com,f5396752-1681-4405-a5ea-67370e80ad4a,ea9206ea-7449-4481-9034-23b3b6c36ff4'

    ids = fullSiteId.split(',')

    # Retrieve the second part
    return ids[1]

    # #example of query:
    # #https://graph.microsoft.com/v1.0/sites/microsofteur.sharepoint.com:/teams/GettingReadyforTridentFabric  
    # url = f"https://graph.microsoft.com/v1.0/sites/mngenvmcap938500.sharepoint.com:/sites/{sharepointTitle}"


async def getSitePageOverview(self, siteID):
    #issue a graph query to get the pages based on the sharepoint id
    
    #example of query:
    #https://graph.microsoft.com/v1.0/sites/microsofteur.sharepoint.com:/teams/GettingReadyforTridentFabric  
    # url = f"https://graph.microsoft.com/v1.0/sites/{siteID}/pages?select=id,name,title,weburl,lastModifiedDateTime"
    
    query_params = PagesRequestBuilder.PagesRequestBuilderGetQueryParameters(
    select = ["id","name","title","weburl","lastModifiedDateTime"],
    )

    request_configuration = RequestConfiguration(
        query_parameters = query_params,
    )

    Pages = await self.user_client.sites.by_site_id(siteID).pages.get(request_configuration = request_configuration)
    # print(Pages)

    return Pages


async def getPageContent(self, siteID, page_id):
    # get page content
    query_params = GraphSitePageRequestBuilder.GraphSitePageRequestBuilderGetQueryParameters(
    expand = ["canvasLayout"],
    )

    request_configuration = RequestConfiguration(
        query_parameters = query_params,
    )
    
    result = await self.user_client.sites.by_site_id(siteID).pages.by_base_site_page_id(page_id).graph_site_page.get(request_configuration = request_configuration)

    # Convert DateTime objects to ISO strings
    last_modified = (
        result.last_modified_date_time.isoformat() 
        if hasattr(result.last_modified_date_time, "isoformat") 
        else str(result.last_modified_date_time)
    )

    # Try to convert canvas_layout to dict, else use str
    try:
        canvas_layout = result.canvas_layout.to_dict()
    except AttributeError:
        try:
            canvas_layout = dict(result.canvas_layout)
        except Exception:
            canvas_layout = str(result.canvas_layout)

    page_details = {
        "Page_ID": result.id,
        "Page_Name": result.name,
        "Page_Title": result.title,
        "Page_URL": result.web_url,
        "Last_Modified": last_modified,
        "Page_Description"  : result.description,
        "Page_CanvasLayout" : canvas_layout
    }

    # Save each page as its own JSON file
    output_dir = r"./01_SharePoint_Extractor/output"
    os.makedirs(output_dir, exist_ok=True)

    # Use page title or name as filename, sanitized for filesystem
    filename = f"graph_output_{page_details['Page_Title']}.json"
    
    # Remove or replace characters not allowed in filenames, but keep the .json extension
    safe_filename = "".join(c for c in filename if c.isalnum() or c in (' ', '_', '-', '.')).rstrip()
    output_path = os.path.join(output_dir, safe_filename)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(page_details, f, ensure_ascii=False, indent=2)

    print(f"Saved page to {output_path}")

    #Issue graph Query: 
    # url = f"https://graph.microsoft.com/v1.0/sites/{siteID}/pages/{page_id}/microsoft.graph.sitePage?$expand=canvasLayout"
    
    #Samples graph Query: 
    # MyPage1.aspx:
    # https://graph.microsoft.com/v1.0/sites/c4a7b3a3-0c67-498e-b974-fc9b5a62324d/pages/be29d9e0-e1ed-4e61-b889-67a6d2b7ada2/microsoft.graph.sitePage?$expand=canvasLayout

    # MyPage2.aspx:
    # https://graph.microsoft.com/v1.0/sites/c4a7b3a3-0c67-498e-b974-fc9b5a62324d/pages/41c59019-d5ad-41f7-8ddb-b7804e540b54/microsoft.graph.sitePage?$expand=canvasLayout
    