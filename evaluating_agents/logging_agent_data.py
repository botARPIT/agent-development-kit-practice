# Includes how to enable obeservability of agentic system using built in plugins
# This is an reactive approach

# Importing libraries
from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.genai import types
from google.adk.tools import google_search, AgentTool
from google.adk.apps.app import App, EventsCompactionConfig
from google.adk.memory import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import DatabaseSessionService
from google.adk.plugins.logging_plugin import (LoggingPlugin)
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
    
    
# Function to count number of papers
def count_papers(papers: list[str]):
    """
    This function counts the number of papers in a list of strings.
    
    Args:
        papers: A list of strings, where each string is a research paper.
    
    Returns:
        The number of papers in the list.
    """    
    
    return len(papers)

search_agent = Agent(
    name="search_agent",
    model=Gemini(
        model = "gemini-2.5-flash-lite",
        retry_options=retry_config,
        temperature=0.2
    ),
    description="Searches for research papers using google search",
    instruction="""Use google_search tool to find information on the given topic.
    Return raw search results
    If the user asks for a list of papers, then give them the list of research papers you found not the summary
    """,
    tools = [google_search]
)
        
# Defining agent
root_agent = Agent(
    name="evaluating_agents",
    model=Gemini(
        model="gemini-2.5-flash-lite",
        retry_options=retry_config
    ),
    description="Research paper finder",
    instruction="""
    Your task is to find the research paper and find them.
    
    You MUST ALWAYS follow these steps:
    1) Find the research papers on the user provided topic using the 'google_search_agent'.
    2) Then, pass the papers to 'count_papers' tool to count the number of papers returned.
    3) Return both the list of research papers and the total number of papers.
    """,
    
    tools=[AgentTool(agent = search_agent), count_papers]
)

chatbot_app = App(
    name="agents",
    root_agent=root_agent,
    # Summarize session conversation using EventCompactionConfig
    events_compaction_config= EventsCompactionConfig(
        compaction_interval=3,
        overlap_size=1
    ),
    plugins=[
        LoggingPlugin() # Adds standard logging across the agent
        ] 
)

chatbot_runner = Runner(
    app=chatbot_app, # App or agent depending upon the use case or object used to build it
    session_service=session_service,
    memory_service=memory_service,
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



