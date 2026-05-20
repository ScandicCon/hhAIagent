import os
from dotenv import load_dotenv

load_dotenv()

HH_CLIENT_ID = os.getenv("HH_CLIENT_ID")
HH_CLIENT_SECRET = os.getenv("HH_CLIENT_SECRET")
HH_USER_AGENT = os.getenv(
    "HH_USER_AGENT",
    "hh-ai-assistant/1.0 (your_email@gmail.com)"
)