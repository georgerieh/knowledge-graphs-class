import os
import urllib.error
import urllib.request

from dotenv import dotenv_values
from langchain.chat_models import init_chat_model
from langchain_community.graphs import Neo4jGraph
from langchain_core.prompts.prompt import PromptTemplate
from langchain_neo4j.chains.graph_qa.cypher import GraphCypherQAChain
from langchain_openai import ChatOpenAI
from langchain_openrouter import ChatOpenRouter
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent, create_react_agent
from . import tools
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import create_agent
from pathlib import Path
from dotenv import dotenv_values, load_dotenv
load_dotenv()


current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent
env_path = project_root / ".env"
config = dotenv_values(env_path)

graph = Neo4jGraph(
    url=os.getenv("NEO4J_URI"), username=config["graphs_username"], password=config["graphs_pass"], database="shop"
)


graph.refresh_schema()
graph_schema = graph.get_schema
model = ChatOpenRouter(model="openrouter/free", temperature=0, max_retries=2, api_key=config["OPENROUTER_API_KEY"])
prompt = ChatPromptTemplate.from_messages(
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
                "- Once you receive the tool output, synthesize it into a clear, helpful response for the user."
            ),
        )
        # MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)

prompt = prompt.partial(graph_schema=graph_schema)
system_string = prompt.format(graph_schema=graph_schema)

print(prompt)
tools = [
    tools.get_researcher_basic_info,
    tools.get_researcher_works_info,
    tools.get_h_index_of,
    tools.get_alike,
    tools.get_path,
]
agent = create_agent(
    model,
    tools=tools,
    # context_schema=UserContext,
    # checkpointer=InMemorySaver(),
    system_prompt=system_string,
)
# agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
