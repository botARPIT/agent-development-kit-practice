# Here, the agent acts as an orchestrator without using any workflow for managing the multi-agent workflow

# Importing libraries
from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.genai import types
from google.adk.tools import google_search, FunctionTool, AgentTool
from dotenv import load_dotenv
import os

# Configuration check
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
google_api_key = os.getenv("GOOGLE_API_KEY")
if google_api_key:
    print("Start Building!!")
else:
    raise ValueError("Unable to find API Key")

# Defining retry configuration
def create_retry_config():
    """ Creates basic retry configuration for the agent
    """
    return types.HttpRetryOptions(
        attempts=5,
        exp_base=2,
        initial_delay=2,
        http_status_codes=[429, 500, 501, 503, 504]
    )
retry_config = create_retry_config()


""" - This is a multi-agent system comprising of 2 agents. one is research agent that uses google_search tool to gather latest findings about a topic
- Other agent is a summariser agent, the task of the agent is to summarise the findings of the researcher agent
"""

researcher_agent = Agent(
    name="ResearcherAgent",
    model = Gemini(
        model="gemini-2.5-flash-lite",
        retry_options = retry_config,
    ),
    description="Researcher agent used to find latest findings about a topic using google_search",
    instruction="""You are a expert reseach agent.
    Given a particular topic, you goal is to:
    - USE the `google_search` tool to find the latest findings about the topic only from trusted and reputed sources
    - MAKE SURE the information is valid and real
    - Present the latest 5-6 findings along with their citations
    """,
    tools=[google_search],
    output_key="research_agent_findings" # This key will be used to store the findings / responses made by this agent seperately in the session state
)

summariser_agent = Agent(
    name="SummariserAgent",
    model= Gemini(
        model="gemini-2.5-flash-lite",
        retry_options=retry_config
    ),
    description="Summariser agent that summarises the facts passed to it as input from the reaserch agent",
    instruction=""" Given the following research findings: {research_agent_findings},
    FOLLOW the following instructions carefully:
    - Create a concise summary of the research findings
    - Never insert any knowlege or sentence that is not in the research findings
    - Return the summary
    """,
    output_key="final_summary_from_summarizer_agent"
)

# This is the orchestrator agent, it will control the flow of execution
root_agent = Agent(
    name="agent_as_orchestrator",
    model=Gemini(
        model="gemini-2.5-flash-lite",
        retry_options=retry_config
    ),
    description="Orchestrator agent, passes findings from the research agent to the summarise agent",
    instruction=""" You are a research coordinator, your goal is to answer the user's query by orchestrating a workflow.
    Follow the follwing instructions carefully:
    - Call the `ResearcherAgent` to find the latest findings in the user requested field
    - After the latest findings, call the `SummariserAgent` tool to create a concise summary of the extracted findings
    - Present the final summary to the user
    """,
    tools= [AgentTool(researcher_agent), AgentTool(summariser_agent)]
)
