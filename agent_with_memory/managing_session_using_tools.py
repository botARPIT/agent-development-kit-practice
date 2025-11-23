# This file includes how to make changes to a state using tools

# Importing libraries
from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.genai import types
from google.adk.tools import google_search, ToolContext
from google.adk.apps.app import App, EventsCompactionConfig
from google.adk.runners import Runner
from google.adk.sessions import DatabaseSessionService
from dotenv import load_dotenv
from typing import Dict, Any

load_dotenv()

retry_config = types.HttpRetryOptions(
    attempts = 7,
    initial_delay=2,
    exp_base=2,
    http_status_codes=[429, 500, 502, 503]
)

database_url = "sqlite:///chatbot.db"
session_service = DatabaseSessionService(db_url = database_url)



# Initial state
initial_state = {
    "name": "toaster"
}
USER_ID = "tester"


# Helper function to create session, and pass the users query and get response from agent
async def run_session_with_args(
    runner_instance : Runner,
    user_queries = None,
    session_name: str = "default"
): 
    # Get app name, to pass it as args to get sessoin info
    app_name = runner_instance.app_name
    # Check if a session exists with session_id if not create one
    try:
        session = await session_service.get_session(
            app_name = app_name,
            user_id = USER_ID,
            session_id= session_name
        )
        if session != None:
            return
        else:
            session = await session_service.create_session(
            app_name = app_name,
            user_id = USER_ID,
            session_id= session_name
        )
    except:
        print("Unable to create session")
        
    print(type(session))
        
    
    # Check if there are any queries passed by the user, if yes process it one by one
    
    if user_queries:
        if type (user_queries) == str:
            user_queries = [user_queries]
        
        for query in user_queries:
            
            # Convert the query in ADK content format:
            query = types.Content(role="user", parts=[types.Part(text = query)])
            
            # Stream the response of agent asynchronously
            async for event in runner_instance.run_async(
                user_id=USER_ID,
                session_id = session.id,
                new_message = query
            ):
                if event.content and event.content.parts:
                    if(event.content.parts[0].text != "None"
                       and event.content.parts[0].text
                       ):
                           print(f"{runner_instance.app_name}: ", event.content.parts[0].text)
    else:   
        print("No queries passed by the user")
    
    
# This section will comprise of defining sections for the use of tools
# Define scope levels for state keys, this helps to store the keys depending on their type

USER_NAME_SCOPE_LEVELS = ("temp", "user", "app")

# Define tool that can write to session state using tool context
# The 'user:' prefix indicates that it is a user specific data

def save_user_info(
    tool_context: ToolContext,
    user_name: str,
    country: str
) -> Dict[str, any]:

    """ 
    Tool to record and save the user name and country to session state
    
    Args:
        user_name: The username to store in the session
        country: The name of user's country
    """
    
    # Write to session state using 'user:' prefix for the user data
    tool_context.state["user:name"] = user_name
    tool_context.state["user:country"] = country
    
    return {"status": "success"}

# Tool to read data from the session state

def retrieve_user_info(
    tool_context: ToolContext
) -> Dict[str, Any]:
    
    user_name = tool_context.state.get("user:name", "Username not found")
    country = tool_context.state.get("user:country", "Country not found")
    
    return {
        "status": "success",
        "username": user_name,
        "country": country
        }
    
    
# Defining agent
root_agent = Agent(
    name="agent_with_memory",
    model=Gemini(
        model="gemini-2.5-flash",
        retry_options=retry_config
    ),
    instruction="Helpful chatbot",
    description="""
    You are a helpful chatbot.
    Use the following tools for managing user context:
    * To record username and country when provided use `save_userinfo` tool.
    * To fetch username and country when required user `retrieve_userinfo` tool.
    """,
    tools = [save_user_info, retrieve_user_info]
)

chatbot_app = App(
    name="agents",
    root_agent=root_agent,
    # Summarize session conversation using EventCompactionConfig
    events_compaction_config= EventsCompactionConfig(
        compaction_interval=3,
        overlap_size=1
    )
)

chatbot_runner = Runner(
    app=chatbot_app, # App or agent depending upon the use case or object used to build it
    session_service= session_service
)

# Defining async function to start the execution
async def main():
    while True:
        user_input = input("You: ")
        
        if user_input.lower() in ["exit"]:
            print("Ending conversation")
            break
        
        await run_session_with_args(chatbot_runner, user_input, "state_management_using_tools-1")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())



