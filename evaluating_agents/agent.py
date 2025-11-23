# Evaluating the agent quality based on predefined tests that contain both happy and sab paths for testing
# This is a proactive approach

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.genai import types
from google.adk.tools import google_search, agent_tool
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.plugins import (LoggingPlugin)
from google.adk.apps.app import App
from typing import Dict, Any
from dotenv import load_dotenv


load_dotenv()

retry_config = types.HttpRetryOptions(
    attempts=6,
    initial_delay=2,
    exp_base=2,
    http_status_codes=[429, 500, 502, 503]
)


# Funtion to set device status
def set_device_status(location: str, device_id: str, status: str) -> dict:
    """Set the status of smart home device.
    
    Args: 
        location: The room where the device is located.
        device_id: The unique idenitifier for the device.
        status: The desired status, either 'ON' or 'OFF'.
        
    Returs: 
        A dictionary confirming the action.
    """
    
    print(f"Tool call: Setting {device_id} in {location} to {status}")
    
    return {
        "success": True,
        "message": f"Successfully set the {device_id} in {location} to {status}."
    }

# Session service
session_service = InMemorySessionService()

root_agent = LlmAgent(
    name="evaluating_agents",
    model = Gemini(
        model="gemini-2.5-flash-lite",
        retry_options=retry_config
        ),
    description="Agent to control smart home devices",
    instruction="""
    You are a home automation assistant. You control ALL smart devices in the house.
    
    You have access to lights, security systems, ovens, fireplaces, and any other device the user mentions.
    Always try to be helpful and control whatever devices the user asks for.
    When users ask about device capanilities, tell them about all the amazing features you can control.
    """.strip(),
    tools=[set_device_status]
)

automation_app = App(
    name="agents",
    root_agent=root_agent,
    plugins = [
        LoggingPlugin()
    ]
)

automation_agent_runner = Runner(
    app=automation_app,
    session_service=session_service
)
