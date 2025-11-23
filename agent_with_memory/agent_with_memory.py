# This file includes required infomation to the user's long memory


# Importing libraries
from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.genai import types
from google.adk.tools import google_search, ToolContext, load_memory
from google.adk.apps.app import App, EventsCompactionConfig
from google.adk.memory import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import DatabaseSessionService
from dotenv import load_dotenv
from typing import Dict, Any

load_dotenv()

retry_config = types.HttpRetryOptions(
    attempts=7,
    initial_delay=2,
    exp_base=2,
    http_status_codes=[429, 500, 502, 503]
)

database_url = "sqlite:///chatbot.db"
session_service = DatabaseSessionService(db_url = database_url)

# Define memory service

memory_service = InMemoryMemoryService() # Built-in memory service for development and testing

# Initial state
initial_state = {
    "name": "toaster"
}
USER_ID = "tester"


# Helper function to create session, pass the users query and get response from agent and add it to agent's memory
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
                session_id=session.id,
                new_message=query
            ):
                if event.content and event.content.parts:
                    if(event.content.parts[0].text != "None"
                       and event.content.parts[0].text
                       ):
                           print(f"{runner_instance.app_name}: ", event.content.parts[0].text)
                           await memory_service.add_session_to_memory(session)
    else:   
        print("No queries passed by the user")
        
        
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
    """,
    tools=[load_memory]
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
    session_service=session_service,
    memory_service=memory_service
)

# Defining async function to start the execution
async def main():
    while True:
        user_input = input("You: ")
        
        if user_input.lower() in ["exit"]:
            print("Ending conversation")
            break
        
        await run_session_with_args(chatbot_runner, user_input, "agent_with_memory_2")
        

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())



