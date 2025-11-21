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

# Output schema for the outline_agent
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

    additional_information: str = Field(
        description = "Additional information required by other agents"
    )
    

 
# Output schema for editor_agent
class EditedBlogSchema(BaseModel):
    title: str = Field(description= "Engaging blog title")
    content: str = Field(description= """Contains the entire blog body including:
        - Introduction hook
        - Main sections with proper headings
        - Sources/References section at the end
        - Conclusion""")
    sources: str = Field(description= "Contains the list of cited sources")



# Creates outline for the blog, based on the user input
outline_agent = Agent(
    name="outline_agent",
    model=Gemini(
        model="gemini-2.5-flash-lite",
        retry_options=retry_config,
        temperature = 0.3
    ),
    description="Outline agent, creates outline for the blog depending upon the topic requested by the user",
    instruction=""" You are an expert blog outline creator.
    Based on topic provided by the user, create a outline for the blog based on the following instructions:
    - There should be single and valid topic, if the user provides multi topic ask for confirmation
    - The headline of the blog should be catchy
    - MUST have an introduction hook
    - HAVE 4-5 main sections with 2-3 bullet points per section
    - A concluding thought
    - Any extra information required by the another agent or any specific condition mentioned by the user MUST be added in `additional_information` section
    """.strip(),
    
    output_schema = OutlineSchema,
    output_key="blog_outline"
)


# Creates draft based on the outline provided
writer_agent = Agent(
    name="writer_agent",
    model = Gemini(
        model = "gemini-2.5-flash-lite",
        retry_options = retry_config,
        temperature = 0.3,
    ),
    description="Drafts the blog based on the outline provided by the outline_agent",
    instruction=""" You are an expert blog writing agent.
    Write a blog based on this outline: {blog_outline} and following instructions:
    - The blog should be minimum of 300 and maximum of 600 words.
    - The tone of the blog should be ENGAGING and INFORMATIVE
    - Refer to the 'additional_information` section of blog_outline
    - Use `google_search` for fetching latest data and cite sources
    """.strip(),
    output_key="blog_draft",
    tools=[google_search]
)


# Checks the fact mentioned in the blog draft and flags any irregularities
fact_checker_agent = Agent(
    name = "fact_checker_agent",
    model = Gemini(
        model="gemini-2.5-flash-lite",
        retry_options = retry_config,
        temperature = 0.1
    ),
    description="Verifies the factual information present in the blog",
    instruction = """ Verify all claims in {blog_draft}:
    - Check dates and statistics are current
    - Flag unsupported claims
    - CRITICAL: If URLs are provided, use `google_search` to verify they exist and are valid
    - If URLs don't exist, find the correct URLs or suggest removing them
    - Provide concise, actionable feedback only (no repetition)
    - Flag vague claims like "astronomical", "massive", "huge" that lack specific data
    - MUST include actual links of verified sources
    """.strip(),
    tools = [google_search],
    output_key = "fact_checker_feedback"
)

# Edits the draft for grammatical errors and improves tone if required
editor_agent=Agent(
    name="editor_agent",
    model=Gemini(
        model="gemini-2.5-flash-lite",
        retry_options=retry_config,
        temperature = 0.3
    ),
    instruction="""Given the blog draft and feedback from the fact_checker: {blog_draft} \n {fact_checker_feedback},
     Your task is to:
    - Create a "Sources:" or "References:" section at the end with all citations
    - Format citations professionally with source names
    - Polish and fix grammatical errors
    - Improve writing style and sentence structure
    - DO NOT remove any factual citations or sources
    """.strip(),
    output_key = "final_blog",
    output_schema = EditedBlogSchema 
)


root_agent=SequentialAgent(
    name="blog_writer_agent",
    sub_agents=[outline_agent, writer_agent, fact_checker_agent, editor_agent]
)