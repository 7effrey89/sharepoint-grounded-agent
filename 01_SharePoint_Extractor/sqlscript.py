import os
import dotenv

# Load environment variables from .env file
dotenv.load_dotenv()

CLIENT_NAME = os.getenv("CLIENT_NAME")

# Run this to allow service principal to access the database instead of using sql authentication

# Run below script in SQL Server Management Studio (SSMS) to create a user for the service principal
print(f"""
CREATE USER [{CLIENT_NAME}] FROM EXTERNAL PROVIDER;
ALTER ROLE db_datawriter ADD MEMBER [{CLIENT_NAME}];

GRANT CREATE TABLE TO [{CLIENT_NAME}];
ALTER USER [{CLIENT_NAME}] WITH DEFAULT_SCHEMA = dbo;
GRANT SELECT ON SCHEMA::dbo TO [{CLIENT_NAME}];
GRANT INSERT ON SCHEMA::dbo TO [{CLIENT_NAME}];
GRANT UPDATE ON SCHEMA::dbo TO [{CLIENT_NAME}];
GRANT DELETE ON SCHEMA::dbo TO [{CLIENT_NAME}];
""")