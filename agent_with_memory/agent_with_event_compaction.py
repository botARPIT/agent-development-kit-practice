# This file includes how to use event compaction for efficiently summarizing the session conversation for saving the context window of the model

# Importing libraries
from dotenv import load_dotenv
import os
import uuid
from google.adk.agents import Agent, LlmAgent
from google.adk.models import Gemini
from google.genai import types
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService, DatabaseSessionService
from typing import Dict, Any
from google.adk.apps.app import App, EventsCompactionConfig
from google.adk.tools.tool_context import ToolContext

# Checking configuration
load_dotenv()
google_api_key = os.getenv("GOOGLE_API_KEY")
if not google_api_key:
    raise ValueError("Configuration Error")


# Create retry configuration
def create_retry_config():
    """Return retry configuration"""
    return types.HttpRetryOptions(
        attempts=6,
        exp_base=2,
        initial_delay=2,
        http_status_codes=[429, 500, 502, 503, 504]
    )

retry_config = create_retry_config()


# Create DB persistence
db_url = "sqlite:///my_agent_with_event_compaction.db"
session_service = DatabaseSessionService(db_url=db_url)

# Helper function that helps to manage the complete convesation between user and agent, it does creating/retrieving sessions
# Also, query processing and response streaming

# It takes the runner instance, list or single user queries and the session name

async def run_session(
        runner_instance: Runner,
        user_queries = None,
        session_name : str = "default"
): 
    # Print the session name
    print(f"Session name: {session_name}")
     
    # Get app name from runner_instance
    app_name = runner_instance.app_name
    

    # Try to create a new session or retrieve the existing one
    try:
        session = await session_service.get_session(
            app_name = app_name,
            user_id = USER_ID,
            session_id= session_name
        )
        if session != None:
            ()
        else:
            session = await session_service.create_session(
            app_name = app_name,
            user_id = USER_ID,
            session_id= session_name
        )
    except:
        print("Unable to create session")
    print(session)
    print(type(session))
    # Process queries of user
    # If single user query => convert it to list => format it to be suitable for Agent
    # If multiple user queries => process each query sequentially just as mentioned above

    if user_queries:
        # Single query
        if type (user_queries) == str:
            user_queries = [user_queries]
        
        # Multiple queries
        for query in user_queries:
            print(f"Query: {query}")
            
            # Convert query to the ADK content format
            query = types.Content(role="user", parts=[types.Part(text=query)])

            # Stream the agent's response asynchronously
            async for event in runner_instance.run_async(
                user_id = USER_ID,
                session_id = session.id,
                new_message = query
            ):
                # Check if content of event is valid
                if event.content and event.content.parts:
                    # Filter out empty or "None" response before printing
                    if (event.content.parts[0].text != "None"
                        and event.content.parts[0].text
                    ): 
                        print(f"{MODEL_NAME}: ", event.content.parts[0].text)
    
    else:
        print("No queries")

print("Created helper function")

MODEL_NAME = "gemini-2.5-flash-lite"

chatbot_agent = Agent(
    name="agent_with_memory",
    model = Gemini(
        model = MODEL_NAME,
        retry_options = retry_config
    ),
    description="A text chatbot"
)

# Create session using InMemorySessionService
# session_service = InMemorySessionService()

APP_NAME = "agents"
USER_ID = "default"
SESSION_NAME = "default"
INITIAL_STATE = {"name": "bhoot",
                 "favourite_destination_to_visit": "guwahti"}
# # Create runner
# runner = Runner(
#     agent=root_agent,
#     app_name=APP_NAME,
#     session_service=session_service,
    
# )

print("Agent Initialized")

# Defining app for event compaction
research_app_compacting = App(
    name = "research_app_compacting",
    root_agent= chatbot_agent,
    events_compaction_config = EventsCompactionConfig(
        compaction_interval = 5,
        overlap_size = 2
    ),
)

# Creating a runner for compact app
research_runner = Runner(
    app = research_app_compacting, 
    session_service = session_service
)


# async def main():
#     try: 
#         await run_session(
#         runner,
#         ["Hi, I am Bhoot! What is capital of Bahamas",
#         "What is my name"],
#         "test-2-session"
#         )
#     finally: 
#         try:
#             await runner.close()
#         except Exception as e:
#             print("Warning: runner.close() raised: ", repr(e))
         
async def main():
    while True:
        user_input = input("You: ")
        
        if user_input.lower() in ["exit"]:
            print("Ending conversation")
            break
        
        await run_session(research_runner, user_input, "tester_of_agentic_system")
    
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
    
     
