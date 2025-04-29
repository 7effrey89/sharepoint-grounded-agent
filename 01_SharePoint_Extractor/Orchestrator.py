import configparser
import json
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import os
import pandas as pd
from datetime import datetime
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
import utils.ais_utils
from utils.sp_contentParser import Graph

import asyncio

import utils.sp_contentParser

async def main2():
    # Load environment variables from .env file
    sharepoint_config = r"./01_SharePoint_Extractor/sharepointConfig.csv"

    # Format the datetime as yyyy-mm-dd hh:mm:ss
    currentDateTime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Load setting
    config = configparser.ConfigParser()
    azure_settings = config['azure'] = {}

    # Set these values directly in the azure_settings
    azure_settings['tenantId'] = os.getenv("AZURE_TENANT_ID")
    azure_settings['clientId'] = os.getenv("AZURE_CLIENT_ID")
    azure_settings['secret'] = os.getenv("AZURE_CLIENT_SECRET")

    graph: Graph = Graph(azure_settings)

    # Load the SharePoint configuration CSV file
    sharepoint_config_df = pd.read_csv(sharepoint_config)
    
    # Skip the header row and process only the data rows
    for index, row in sharepoint_config_df.iterrows():

        sharepointTitle = row['SharepointSite']
        sharepointType = row['Type']
        
        updated_documents = await utils.ais_utils.updated_documents(sharepointTitle, currentDateTime, sharepointType, graph)

        #Remove existing documents in search index to avoid left-overs if previous document was longer than the current one
        utils.ais_utils.removeDocumentInAISearchIndex(updated_documents)

        #Run azure-search-integrated-vectorization-sample.ipynb to start uploading .json files from 03_AISearch_Ingestion/data/documents/ to Azure Blob Storage
            #optional: empty the folder 03_AISearch_Ingestion/data/documents/ before running the notebook to avoid uploading unchanged files OR
            #or moves files around in folder to keep status of new and old files


asyncio.run(main2())