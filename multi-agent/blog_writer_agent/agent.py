'''
Creating a blog writer agent, with hybrid workflow:
- Seqential workflow:
    - Outline agent: To create the blog outline based on the topic requested by the user
    - Draft agent: Creates a rough draft with required content
    - Editor agent: Reviews the draft and edits if any changes required
- Iterative workflow:
    - Critic agent: Evaluates the draft thoroughly based on the predefined criteria, generates a response
                    if approved else trigger the draft agent to rewrite the draft again.
''' 
# Importing basic libraries

from google.adk.agents import Agent, SequentialAgent, LoopAgent
from google.adk.models.google_llm import Gemini
from google.adk.tools import google_search, AgentTool, set_model_response_tool
from google.genai import types
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import os



# Configuration check
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
google_api_key = os.getenv("GOOGLE_API_KEY")
if google_api_key:
    print("Start building!!")
else:
    raise ValueError("Unable to find api key")

# Create retry configuration
def create_retry_configuration():
    """ Returns retry configuration for the agents
    """

    return types.HttpRetryOptions(
        attempts=5,
        exp_base=2,
        initial_delay=2,
        http_status_codes=[429, 500, 502, 503, 504]
    )

retry_config = create_retry_configuration()

class OutlineSchema(BaseModel):
    title: str = Field(
        description = "Catchy headline for the blog"
        ),

    introduction_hook: str = Field(
        description = "Introduction hook for the blog. Should be concise and clear"
    )

    main_section: str = Field(
        description = "Contains the main body of the blog"
    )

    conclusion: str = Field(
        description= "Conclusion thought for the blog"
    )

    additional_innformation: str = Field(
        description = "Additional information required by other agents"
    )

# Creates outline for the blog, based on the user input
outline_agent = Agent(
    name="outline_agent",
    model=Gemini(
        model="gemini-2.5-flash-lite",
        retry_options=retry_config
    ),
    description="Outline agent, creates outline for the blog depending upon the topic requested by the user",
    instruction=""" You are an expert blog outline creator.
    Based on topic provided by the user, create a outline for the blog based on the following instructions:
    - If the topic user requested is out of your training data use `google_search` tool to fetch the relevant data from authentic sources
    - There should be single and valid topic, if the user provides multi topic ask for confirmation
    - The headline of the blog should be catchy
    - MUST have an introduction hook
    - HAVE 4-5 main sections with 2-3 bullet points per section
    - A concluding thought
    - Any extra information required by the another agent MUST be added in `additional_information` section
    """.strip(),
    # tools=[google_search],
    output_schema=OutlineSchema,
    output_key="blog_outline"
)

root_agent=SequentialAgent(
    name="blog_writer_agent",
    sub_agents=[outline_agent]
)