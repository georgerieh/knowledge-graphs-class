"""Module to load define LLM"""

import os
import json
from pathlib import Path
from dotenv import dotenv_values, load_dotenv
from langchain_neo4j import Neo4jGraph
from langchain_core.messages import ToolMessage, AIMessage
from langchain_core.utils.function_calling import convert_to_openai_tool
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
import langchain
from . import tools

langchain.verbose = True
langchain.debug = True

load_dotenv()


current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent
env_path = project_root / ".env"
config = dotenv_values(env_path)

graph = Neo4jGraph(
    url=os.getenv("NEO4J_URI"), username=config["graphs_username"], password=config["graphs_pass"], database="shop"
)


graph.refresh_schema()
GRAPH_SCHEMA = graph.get_schema
MODEL = ChatOpenAI(
    model="hf.co/bartowski/Llama-3-Groq-8B-Tool-Use-GGUF:Q6_K_L",
    base_url="http://host.docker.internal:12434/engines/v1",
    api_key="na",
    temperature=0.3,
)
TOOLS = [
    tools.tool_get_researcher_basic_info,
    tools.tool_get_h_index_of,
    tools.tool_get_alike,
    tools.tool_get_path,
    tools.tool_get_paper_basic_info,
    tools.tool_get_articles_of_author,
    tools.tool_get_keyword_community,
    tools.tool_get_most_influential_papers_with_text,
    tools.tool_get_most_influential_papers_with_field,
    tools.tool_get_most_influential_papers_with_keyword,
]
TOOL_MAP = {}
for t in TOOLS:
    TOOL_MAP[t.name] = t
    if hasattr(t, "func"):
        TOOL_MAP[t.func.__name__] = t
tool_names = ", ".join([t.name for t in TOOLS])


def generate_groq_system_prompt(tools_list, schema):
    openai_tools = [convert_to_openai_tool(t) for t in tools_list]
    tools_json_list = [json.dumps(tool, indent=2) for tool in openai_tools]
    formatted_tools = ",\n".join(tools_json_list)

    return f"""You are an expert graph database assistant with function calling capability. Your job is to help users query an academic corpus graph database using available tools.

You are provided with function signatures within XML tags. You may call one or more functions to assist with the user query. For each function call, return a JSON object with function name and arguments within XML tags.

<tools>
[
{formatted_tools}
]
</tools>

Database Schema:
{schema}

INSTRUCTIONS:
- To fetch information from the database, use tools unless it is a general question.
- Do not guess or make up answers; always query the database using the tools.
- Once you receive the tool output, synthesize it into a clear, helpful response for the user, and present the results in a Markdown table if requested.
- You have access to the following tools: {tool_names}. Use them when necessary.
- If asked about system queries (for example, available tools) do not use tools, rather provide a list of what you have in human readable form
- Your query might involve complex steps. For example, a person might be interested in someones research, but have only his Name. Get his id first, and then query articles tool with his id.add()
- If tool returned None/NaN/[] - try another approach or stop
- if you tried 3+ times, stop
"""


def call_function(name, args):
    return TOOL_MAP[name].invoke(args)


def parse_groq_xml_to_tool_calls(response: AIMessage) -> AIMessage:
    content = response.content.strip()
    try:
        parsed = json.loads(content)

        if isinstance(parsed, list) and len(parsed) > 0:
            tool_item = parsed[0]
            name = tool_item.get("name")
            args = tool_item.get("arguments") or tool_item.get("args") or {}

        elif isinstance(parsed, dict):
            name = parsed.get("name")
            args = parsed.get("arguments") or parsed.get("args") or {}
        else:
            return response
        if name:
            response.tool_calls = [
                {
                    "name": name,
                    "args": args,
                    "id": "call_groq_xml_1",
                }
            ]
    except (json.JSONDecodeError, ExceptionGroup):
        pass

    return response


cleansed_model = MODEL | parse_groq_xml_to_tool_calls
system_prompt_str = generate_groq_system_prompt(TOOLS, GRAPH_SCHEMA)


def call_model(state):
    messages = state["messages"]
    response = cleansed_model.invoke(messages)
    return {"messages": messages + [response]}


def execute_tool_node(state):
    messages = state["messages"]
    last_message = messages[-1]

    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        tool_call = last_message.tool_calls[0]
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]

        tool_obj = TOOL_MAP.get(tool_name)

        if tool_obj:
            print(f"\n⚡ Executing Tool: {tool_name} with args {tool_args}...")
            try:
                result = tool_obj.invoke(tool_args)
                print(f"Tool Result: {result}\n")

                tool_msg = ToolMessage(
                    content=str(result),
                    tool_call_id=tool_call.get("id", "call_groq_xml_1"),
                    name=tool_name,
                )
                return {"messages": messages + [tool_msg]}
            except ExceptionGroup as e:
                print(f"Error in tool execution: {e}")
                error_msg = ToolMessage(
                    content=f"Error executing {tool_name}: {str(e)}",
                    tool_call_id=tool_call.get("id", "call_groq_xml_1"),
                    name=tool_name,
                )
                return {"messages": messages + [error_msg]}
        else:
            print(f" Tool '{tool_name}' not found in TOOL_MAP! Available keys:" f" {list(TOOL_MAP.keys())}")

    return state


def should_continue(state):
    last_message = state["messages"][-1]

    if getattr(last_message, "tool_calls", None):
        tool_name = last_message.tool_calls[0]["name"]
        if tool_name in TOOL_MAP:
            return "execute_tool"

    return END


workflow = StateGraph(dict)

workflow.add_node("agent", call_model)
workflow.add_node("execute_tool", execute_tool_node)

workflow.set_entry_point("agent")

workflow.add_conditional_edges(
    "agent",
    should_continue,
    {"execute_tool": "execute_tool", END: END},
)
workflow.add_edge("execute_tool", "agent")

agent_executor = workflow.compile()