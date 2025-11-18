from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.genai import types
from datetime import datetime
from google.adk.tools import google_search, FunctionTool
from google.adk.runners import InMemoryRunner
from dotenv import load_dotenv
import os

# Configuration check
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
google_api_key = os.getenv("GOOGLE_API_KEY")
if google_api_key:
    print("Start Building!!")
else:
    raise ValueError("Unable to find API Key")



# Defining a function to be used as a tool
def get_current_time() -> dict:
    """ Return the current time in format: YYYY-MM-DD HH:MM:SS

    Returns:
        Dictionary with the current timestamp
        dict: {"current_time" : current_time}
    """
    return {"current_time": datetime.now().strftime("%y-%m-%d %h-%m-%s")}



# Funtion for retry config
def create_retry_config():
    """ This function creates basic retry configuration for the llm
    """
    return types.HttpRetryOptions(
        attempts=6,
        exp_base=2,
        initial_delay=5,
        http_status_codes=[429, 500, 501, 503, 504]
    )
# Retry configuration
retry_config = create_retry_config()
    
# Adk looks for this agent when executing a workflow
root_agent = Agent(
    name="greeting_agent",
    model = Gemini(
        model = "gemini-2.5-flash-lite",
        retry_options = retry_config
    ),
    description="A simple agent that greets and chats with the user",
    instruction= """ You are a helpful chatbot. Follow the instructions below carefully:
    - FIRST ask for the user's name, and greet them with name
    - USE the `google_search` tool only IF the user asks something out of your training data OR something you are unsure of
    - USE the 'get_current_time` function if the user ask for current time and return it to the user.
    """,
    tools = [get_current_time]
)

# runner = InMemoryRunner(agent = root_agent)
