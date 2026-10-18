"""Module to load define LLM"""

import os
import json
from pathlib import Path
from dotenv import dotenv_values, load_dotenv
from langchain_neo4j import Neo4jGraph
from langchain_core.messages import ToolMessage, AIMessage, HumanMessage
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
    model="hf.co/bartowski/Llama-3-Groq-8B-Tool-Use-GGUF:Q4_K_L",
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
    tools.tool_get_keyword_alike,
    tools.tool_get_keyword_community,
    tools.tool_get_most_influential_papers_with_text,
    tools.tool_get_most_influential_papers_with_field,
    tools.tool_get_most_influential_papers_with_keyword,
    tools.tool_execute_query,
]


def normalize_tool_name(name: str) -> str:
    """Standardizes tool names across spaces, casing, and underscores."""
    return name.lower().replace(" ", "").replace("_", "").replace("-", "")


TOOL_MAP = {}
for t in TOOLS:
    TOOL_MAP[t.name] = t
    TOOL_MAP[normalize_tool_name(t.name)] = t
    if hasattr(t, "func"):
        TOOL_MAP[t.func.__name__] = t
        TOOL_MAP[normalize_tool_name(t.func.__name__)] = t
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
- Always output tool calling as json. This example of good calling and parsing:
[
  {{
    "id": 0,
    "name": TOOL_VALUE",
    "arguments": {{"PARAM": PARAM_VALUE}}
  }}
]
which is parsed as 
Tool Calls:
  Get Keywords Community (call_groq_xml_1)
 Call ID: call_groq_xml_1
  Args:
    id_: 123

REPLACE TOOL_VALUE, PARAM, PARAM_VALUE with necessary information
CRITICAL RULES:
1. Do NOT hardcode arbitrary numerical IDs (like 123). Use the string/name provided by the user, or query the database first to find the correct ID.
2. IF A TOOL RETURNS AN EMPTY RESULT (`[]`, `None`, or `NaN`), DO NOT MAKE UP AN ANSWER. You must either try another tool or inform the user that no data was found.
3. Pay attention between get keyword info (looks for keywords that share same root) and get keyword community (once you extract the community id, you can pass it there
4. you must follow your system prompt to call tools properly - return only 1 layer json payload to call tool. Plan accordingly, and execute complex queryies in chain of tool calls. If tool failed, try another tool - return the tool call in the message where you encounter error
**Do NOT stop or output a final answer to the user** until you have executed all necessary steps in the chain and gathered all required data.
"""


def call_function(name, args):
    return TOOL_MAP[name].invoke(args)


def parse_groq_xml_to_tool_calls(response: AIMessage) -> AIMessage:
    content = response.content.strip()
    try:
        parsed = json.loads(content)
        items = parsed if isinstance(parsed, list) else [parsed]
        tool_calls = []

        for i, item in enumerate(items):
            name = item.get("name")
            args = item.get("arguments") or item.get("args") or {}
            call_id = item.get("id", i)

            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    pass

            if name:
                tool_calls.append({
                    "name": name,
                    "args": args,
                    "id": f"call_groq_xml_{call_id}",
                })

        if tool_calls:
            response.tool_calls = tool_calls

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
        new_messages = list(messages)
        
        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_id = tool_call.get("id", "call_groq_xml_1")

            tool_obj = TOOL_MAP.get(tool_name) or TOOL_MAP.get(normalize_tool_name(tool_name))

            if tool_obj:
                print(f"\n⚡ Executing Tool: {tool_name} with args {tool_args}...")
                try:
                    result = tool_obj.invoke(tool_args)
                    print(f"Tool Result: {result}\n")

                    new_messages.append(ToolMessage(
                        content=str(result),
                        tool_call_id=tool_id,
                        name=tool_name,
                    ))
                except Exception as e:
                    print(f"Error in tool execution: {e}")
                    new_messages.append(ToolMessage(
                        content=f"Error executing {tool_name}: {str(e)}",
                        tool_call_id=tool_id,
                        name=tool_name,
                    ))
            else:
                new_messages.append(ToolMessage(
                    content=f"Error: Tool '{tool_name}' not found.",
                    tool_call_id=tool_id,
                    name=tool_name,
                ))

        return {"messages": new_messages, "retry_count": 0}

    return state


def retry_node(state):
    messages = state["messages"]
    retry_count = state.get("retry_count", 0) + 1
    
    hint_prompt = (
        f"Reflexion (Attempt {retry_count}/2): Your previous tool call returned an empty result (`[]`) or failed. "
        "This usually means your request was wrong, an overly specific query, or the wrong tool. "
        "Do NOT repeat the exact same call. Try a broader term, correct any potential typos, "
        "or use a completely different tool to find what you're looking for."
    )
    
    return {
        "messages": messages + [HumanMessage(content=hint_prompt)],
        "retry_count": retry_count
    }

def route_after_agent(state):
    messages = state["messages"]
    last_message = messages[-1]

    if getattr(last_message, "tool_calls", None):
        return "execute_tool"
    return END


def route_after_tool(state):
    messages = state["messages"]
    last_message = messages[-1]
    retry_count = state.get("retry_count", 0)

    if hasattr(last_message, "type") and last_message.type == "tool":
        content_str = str(last_message.content)
        try:
            response_json = json.loads(content_str)
            status = response_json.get("status")
            
            if status == "error":
                if retry_count < 2:
                    return "retry"
                return END
                
            elif status == "not_found":
                if retry_count < 1: 
                    return "retry"
                return END
                
        except json.JSONDecodeError:
            pass

    return "agent"


workflow = StateGraph(dict)

workflow.add_node("agent", call_model)
workflow.add_node("execute_tool", execute_tool_node)
workflow.add_node("retry", retry_node)
workflow.set_entry_point("agent")

workflow.add_conditional_edges(
    "agent",
    route_after_agent,
    {
        "execute_tool": "execute_tool",
        END: END,
    },
)

workflow.add_conditional_edges(
    "execute_tool",
    route_after_tool,
    {
        "retry": "retry",
        "agent": "agent",
        END: END
    }
)

workflow.add_edge("retry", "agent")

agent_executor = workflow.compile()