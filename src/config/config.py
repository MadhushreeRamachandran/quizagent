import os
from dotenv import load_dotenv
load_dotenv()

DB_NAME=os.getenv('DB_NAME')
DB_HOST=os.getenv('DB_HOST')
DB_PORT=os.getenv('DB_PORT')
DB_USER=os.getenv('DB_USER')
DB_PASSWORD=os.getenv('DB_PASSWORD')

HOST=os.getenv('HOST')
PORT=os.getenv('PORT')
LOG_LEVEL=os.getenv('LOG_LEVEL')

MODEL_ID=os.getenv('MODEL_ID')
PROVIDER=os.getenv('PROVIDER')
REGION=os.getenv('AWS_REGION')

Access_key_ID =os.getenv('Access_key_ID')
Secret_access_key = os.getenv('Secret_access_key')

MCP_SERVER_URL=os.getenv('MCP_SERVER_URL')
