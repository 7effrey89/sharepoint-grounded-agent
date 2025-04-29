# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

# <ProgramSnippet>
import asyncio
import os
import dotenv
import configparser
from msgraph.generated.models.o_data_errors.o_data_error import ODataError
from utils.sp_pageGrabber import Graph
import pandas as pd

# Load environment variables from .env file
dotenv.load_dotenv()

async def main():
    
    # Load setting
    config = configparser.ConfigParser()
    azure_settings = config['azure'] = {}
    
    # Set these values directly in the azure_settings
    azure_settings['tenantId'] = os.getenv("AZURE_TENANT_ID")
    azure_settings['clientId'] = os.getenv("AZURE_CLIENT_ID")
    azure_settings['secret'] = os.getenv("AZURE_CLIENT_SECRET")

    graph: Graph = Graph(azure_settings)

    # Load environment variables from .env file
    sharepoint_config = r"./01_SharePoint_Extractor/sharepointConfig.csv"

    # Load the SharePoint configuration CSV file
    sharepoint_config_df = pd.read_csv(sharepoint_config)

    # Skip the header row and process only the data rows
    for index, row in sharepoint_config_df.iterrows():
        if index == 0:  # Skip the header row
            continue
        await make_graph_call(graph, row['SharepointSite'])
    
# </ProgramSnippet>


# <MakeGraphCallSnippet>

async def make_graph_call(graph: Graph, sharepoint_site):
    await graph.make_graph_call(sharepoint_site)
# </MakeGraphCallSnippet>

# Run main
asyncio.run(main())
