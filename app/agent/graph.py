"""Module to load define LLM"""
import os
from pathlib import Path
from dotenv import dotenv_values, load_dotenv
from langchain_community.graphs import Neo4jGraph
from langchain_openrouter import ChatOpenRouter
from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import create_agent
from . import tools

load_dotenv()


current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent
env_path = project_root / ".env"
config = dotenv_values(env_path)

graph = Neo4jGraph(
    url=os.getenv("NEO4J_URI"), \
        username=config["graphs_username"], password=config["graphs_pass"], database="shop"
)


graph.refresh_schema()
GRAPH_SCHEMA = graph.get_schema
MODEL = ChatOpenRouter(model="openrouter/free", \
    temperature=0, max_retries=2, api_key=config["OPENROUTER_API_KEY"])
_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            (
                "You are an expert graph database assistant. Your job is to help users query "
                "an academic corpus graph database using the available tools.\n\n"
                "Database Schema:\n{graph_schema}\n\n"
                "INSTRUCTIONS:\n"
                "- You MUST use the provided tools to fetch information from the database.\n"
                "- Do not guess or make up answers; always query the database using the tools.\n"
                """- Once you receive the tool output, 
                synthesize it into a clear, helpful response for the user."""
            ),
        )
    ]
)

PROMPT = _PROMPT.partial(graph_schema=GRAPH_SCHEMA)
SYSTEM_STRING = PROMPT.format(graph_schema=GRAPH_SCHEMA)

TOOLS = [
    tools.get_researcher_basic_info,
    tools.get_researcher_works_info,
    tools.get_h_index_of,
    tools.get_alike,
    tools.get_path,
]
agent = create_agent(
    MODEL,
    tools=TOOLS,
    system_prompt=SYSTEM_STRING,
)
