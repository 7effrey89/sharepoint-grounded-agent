import json
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import os
import pandas as pd
from datetime import datetime
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
import utils.sp_contentParser
import utils.sql_utils

# Load environment variables from .env file
load_dotenv()

# Azure Cognitive Search configuration
SEARCH_SERVICE_ENDPOINT = os.environ["AZURE_SEARCH_SERVICE_ENDPOINT"]
SEARCH_INDEX_NAME = os.getenv("AZURE_SEARCH_INDEX", "int-vec")
credential = AzureKeyCredential(os.getenv("AZURE_SEARCH_ADMIN_KEY")) if os.getenv("AZURE_SEARCH_ADMIN_KEY") else DefaultAzureCredential()

async def updated_documents(sharepointTitle, currentDateTime, sharepointType, graph):

    #Issue graph Query: Get SiteID based on sharepointTitle
    siteID = await utils.sp_contentParser.getSiteId(graph, sharepointTitle)

    pages = await utils.sp_contentParser.getSitePageOverview(graph, siteID)

    #insert and update watermark table
    utils.sql_utils.update_sharepoint_watermark_table(pages, siteID)

    # Show the watermark table
    df = utils.sql_utils.Select_query(utils.sql_utils.QUERY)
    print(df)
    
    # Initialize an empty list to store updated rows
    updated_pages_documents = []


    # Compare 'lastModifiedDateTime' with 'lastExtractionDateTime' and extract the page if it is newer
    for index, row in df.iterrows():
        if pd.to_datetime(row['lastModifiedDateTime']) > pd.to_datetime(row['lastExtractionDateTime']):
            await utils.sp_contentParser.getPageContent(graph, siteID, row['page_id']) #extract html from sharepoint page 
            utils.sql_utils.update_page_watermark(row['page_id'], currentDateTime) #update the lastExtractionDateTime in watermark table

        updated_pages_documents.append(row['page_id'] + '.json')  # Append the updated page_id to the list

    return updated_pages_documents



#Remove existing documents in search index to avoid left-overs if previous document was longer than the current one
def removeDocumentInAISearchIndex(array_document_name_and_extention):
    #figure out how to retrieve all chucnk_ids for the same docuent, they share same parentid or title page_id+.json
    # Create a SearchClient
    search_client = SearchClient(endpoint=SEARCH_SERVICE_ENDPOINT,
                                index_name=SEARCH_INDEX_NAME,
                                credential=credential)
        
    for document_name_and_extension in array_document_name_and_extention:
        # Search for documents where title matches the current document name and extension. we assume top 1000 results will cover all chunks related to the document.
        search_results = search_client.search(search_text="*", filter=f"title eq '{document_name_and_extension}'", top=1000)

        # Extract chunk_id values
        chunk_ids = [doc['chunk_id'] for doc in search_results if 'chunk_id' in doc] 

        print(f"Chunk IDs for {document_name_and_extension}:", chunk_ids)

        # Loop through chunk_ids and delete each document
        for chunk_id in chunk_ids:
            document_key = chunk_id
            result = search_client.delete_documents(documents=[{"chunk_id": document_key}])
            print(f"Deletion of document {document_key} succeeded: {result[0].succeeded}")
