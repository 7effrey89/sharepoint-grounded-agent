from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import os
import pandas as pd


# Load environment variables from .env file
load_dotenv()

# Connection string
SERVER = os.getenv("AZURE_SQL_server") 
DATABASE = os.getenv("AZURE_SQL_database")
USERNAME = os.getenv("AZURE_SQL_username")
PASSWORD = os.getenv("AZURE_SQL_password")
DRIVER = os.getenv("AZURE_SQL_driver")

# Database and table details
TABLE_SCHEMA = os.getenv("AZURE_SQL_WATERMARK_SCHEMA")
TABLE_NAME = os.getenv("AZURE_SQL_WATERMARK_TABLE")

QUERY = f'SELECT id, page_id, lastModifiedDateTime, name, webUrl, title, is_active, lastExtractionDateTime FROM {TABLE_SCHEMA}.{TABLE_NAME};'
DROP_TABLE = f"DROP TABLE {TABLE_SCHEMA}.{TABLE_NAME}"
INIT_TABLE = f"""
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = '{TABLE_NAME}' AND schema_id = SCHEMA_ID('{TABLE_SCHEMA}'))
CREATE TABLE {TABLE_SCHEMA}.{TABLE_NAME} (
    id INT IDENTITY(1,1),
    page_id VARCHAR(100), 
    site_id VARCHAR(100), 
    lastModifiedDateTime datetime,
    name VARCHAR(100),
    webUrl VARCHAR(100),
    title VARCHAR(100),
    is_active bit,
    lastExtractionDateTime datetime,
);
"""

def init_connection():
    """
    Initializes a connection to the database using the provided credentials.

    Returns:
        engine (sqlalchemy.engine.Engine): The SQLAlchemy engine object representing the database connection.
    """
    # Create connection engine
    connection_string = f'mssql+pyodbc://{USERNAME}:{PASSWORD}@{SERVER}/{DATABASE}?driver={DRIVER}'
    engine = create_engine(connection_string, echo=True)
    return engine

def execute_sql_command(batch_command):
    """
    Executes a batch SQL command.
    """
    engine = init_connection()
    with engine.begin() as conn:
        conn.execute(text(batch_command))

# CRUD operations
def Select_query(query):
    engine = init_connection()
    with engine.connect() as connection:
        result = pd.read_sql_query(query, connection.connection)
        return result
    
def update_sharepoint_watermark_table(pages, siteID):
    # Check if the `value` array in `pages` has content
    if not pages.value or len(pages.value) == 0:
        print("No pages found in the response.")
        return
    
    # Create a list to hold the SELECT statements
    select_statements = []

    # Loop through the `value` array in `pages`
    for page in pages.value:
        # Extract attributes from each page
        page_id = page.id
        web_url = page.web_url
        last_modified = (
            page.last_modified_date_time.strftime('%Y-%m-%d %H:%M:%S') #YYYY-MM-DD HH:MM:SS
            if hasattr(page.last_modified_date_time, "strftime")
            else str(page.last_modified_date_time)
        )
        name = page.name
        title = getattr(page, "title", None)  # Use getattr to handle missing attributes

        # Create a SELECT statement for the current page
        select_statement = f"""
        SELECT '{page_id}' AS page_id, 
               '{siteID}' AS site_id, 
               '{last_modified}' AS lastModifiedDateTime, 
               '{name}' AS name, 
               '{web_url}' AS webUrl, 
               '{title}' AS title
        """
        select_statements.append(select_statement)

    # Combine all SELECT statements with UNION ALL
    combined_select = " UNION ALL ".join(select_statements)

    # if not added_rows:
    #     return
    
    # # Create a single SELECT statement with UNION ALL
    # select_statements = []
    # for row in added_rows:
    #     select_statement = f"""
    #     SELECT '{row['id']}' AS page_id, 
    #            '{siteID}' AS site_id, 
    #            '{row['lastModifiedDateTime']}' AS lastModifiedDateTime, 
    #            '{row['name']}' AS name, 
    #            '{row['webUrl']}' AS webUrl, 
    #            '{row['title']}' AS title
    #     """
    #     select_statements.append(select_statement)
    
    # # Combine all SELECT statements with UNION ALL
    # combined_select = " UNION ALL ".join(select_statements)
    
    # Create the MERGE command using the combined SELECT statement
    merge_command = f"""
    MERGE INTO {TABLE_SCHEMA}.{TABLE_NAME} AS target
    USING ({combined_select}) AS source
    ON (target.page_id = source.page_id)
    WHEN MATCHED THEN
        UPDATE SET 
            target.lastModifiedDateTime = source.lastModifiedDateTime,
            target.name = source.name,
            target.webUrl = source.webUrl,
            target.title = source.title,
            target.is_active = 1
    WHEN NOT MATCHED BY TARGET THEN
        INSERT (page_id, site_id, lastModifiedDateTime, name, webUrl, title, is_active, lastExtractionDateTime)
        VALUES (source.page_id, source.site_id, source.lastModifiedDateTime, source.name, source.webUrl, source.title, 1, 0)
    WHEN NOT MATCHED BY SOURCE THEN
       UPDATE SET target.is_active = 0
    ;
    """
    execute_sql_command(merge_command)

def update_page_watermark(page_id, currentDateTime):

    batch_command = f"UPDATE {TABLE_SCHEMA}.{TABLE_NAME} SET lastExtractionDateTime='{currentDateTime}' WHERE page_id = '{page_id}'"

    print(batch_command)
    execute_sql_command(batch_command)

#Initiate the watermark
execute_sql_command(INIT_TABLE)