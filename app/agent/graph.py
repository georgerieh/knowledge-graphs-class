"""Module to load define LLM"""

import os
import json
from enum import Enum
from typing import TypedDict, Annotated, List, Dict, Optional, Literal
from pydantic import BaseModel, Field
import operator
from pathlib import Path
from dotenv import dotenv_values, load_dotenv
from langchain_neo4j import Neo4jGraph
from langchain_core.messages import ToolMessage, AIMessage, HumanMessage, SystemMessage
from langchain_core.utils.function_calling import convert_to_openai_tool
from langchain_core.output_parsers import PydanticOutputParser
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
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
    base_url="http://host.docker.internal:12434/v1",
    api_key="na",
    temperature=0.3,
    timeout=180,
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


class RouteSelection(str, Enum):
    END = "end"
    AGENT = "agent"
    TOOL = "tool"


class ToolCallSchema(BaseModel):
    name: str = Field(description="The exact name of the tool to call")
    arguments: Dict[str, str | int | float | bool | None] = Field()


class AgentStructuredOutput(BaseModel):
    # thought: Optional[str] = Field(description="Step-by-step reasoning plan")
    tool_calls: List[ToolCallSchema] = Field(
        default=[],
        description="List of tool calls to execute. LEAVE EMPTY if you are ready to give the final answer or you dont need tools",
    )
    answer: Optional[str] = Field(
        default=None,
        description="Final response to user. ONLY fill this if you are completely finished and answering the user directly. ",
    )
    next_action: Literal["tool", "agent", "end"] = Field(default="end")


class State(TypedDict):
    messages: Annotated[list, add_messages]
    retry_count: Annotated[int, operator.add]
    ai_message_count: int
    tool_iteration_count: int
    last_tool_signature: str
    next_action: str


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


Your tools:
{formatted_tools}
Database Schema:
{schema}

INSTRUCTIONS:
- To fetch information from the database, use tools unless it is a general question.
- Be concise
- Do not guess or make up answers; always query the database using the tools.
- Once you receive the tool output, synthesize it into a clear, helpful response for the user, and present the results in a Markdown table.
- If you have a complex task, that involves multiple tools, you might choose one data point from many that are returned by tool. Choose the best one for your task.
- If asked about system queries (for example, available tools) do not use tools, rather provide a list of what you have in human readable form
- Your query might involve complex steps. For example, a person might be interested in someones research, but have only his Name. Get his id first, and then query articles tool with his id.
- If tool returned None/NaN/[] - try another approach or stop
- if you tried 3+ times, stop
CRITICAL RULES:
1. Do NOT hardcode arbitrary numerical IDs (like 123). Use the string/name provided by the user, or query the database first to find the correct ID.
2. IF A TOOL RETURNS AN EMPTY RESULT (`[]`, `None`, or `NaN`), DO NOT MAKE UP AN ANSWER. You must either try another tool or inform the user that no data was found.
3. Pay attention between get keyword info (looks for keywords that share same root) and get keyword community (once you extract the community id, you can pass it there
4. you must follow your system prompt to call tools properly - return only 1 layer json payload to call tool. Plan accordingly, and execute complex queryies in chain of tool calls. If tool failed, try another tool - return the tool call in the message where you encounter error
**Do NOT stop or output a final answer to the user** until you have executed all necessary steps in the chain and gathered all required data.
5. You have an opportunity to run arbitrary query, if user asks you to do it and you dont have a tool for that. 
Mention that you need **another tool** if you dont have all the necessary information and need a tool call
CRITICAL ENVIRONMENT RULES:
You are in the environment that does not allow ongoing user interaction after user input. Therefore, your own automity is preferred. 
"""


def call_function(name, args):
    return TOOL_MAP[name].invoke(args)


def parse_groq_xml_to_tool_calls(response: AIMessage) -> AIMessage:
    content = response.content.strip()
    tool_calls = []
    try:
        parsed = json.loads(content)
        items = parsed if isinstance(parsed, list) else [parsed]
    except (json.JSONDecodeError, ExceptionGroup):
        items = []

    for i, item in enumerate(items):
        if "type" in item:
            function = item["function"]
            name = function.get("name")
            args = function.get("arguments") or function.get("args") or {}
            call_id = function.get("id", i)
        else:
            name = item.get("name")
            args = item.get("arguments") or item.get("args") or {}
            call_id = item.get("id", i)
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except json.JSONDecodeError:
                pass
        if name:
            tool_calls.append(
                {
                    "name": name,
                    "args": args,
                    "id": f"call_groq_xml_{call_id}",
                }
            )

    if tool_calls:
        response.tool_calls = tool_calls

    return response


cleansed_model = MODEL.with_structured_output(AgentStructuredOutput)

system_prompt_str = generate_groq_system_prompt(TOOLS, GRAPH_SCHEMA)


def call_model(state):
    messages = state["messages"]
    ai_count = state.get("ai_message_count", 0)

    # Ensure system prompt is included
    if not any(isinstance(m, SystemMessage) for m in messages):
        full_messages = [SystemMessage(content=system_prompt_str)] + messages
    else:
        full_messages = messages

    # Invoke model — LangChain automatically parses the output into AgentStructuredOutput
    result: AgentStructuredOutput = cleansed_model.invoke(full_messages)

    # Map structured output tool calls into LangGraph format
    if result.tool_calls:
        ai_message = AIMessage(content="Executing tools...")
        ai_message.tool_calls = [
            {"name": tc.name, "args": tc.arguments, "id": f"call_struct_{i}"} for i, tc in enumerate(result.tool_calls)
        ]
    else:
        ai_message = AIMessage(content=result.answer or "No response generated.")

    return {
        "messages": [ai_message],
        "ai_message_count": ai_count + 1,
        "next_action": result.next_action,
    }


def execute_tool_node(state):
    messages = state["messages"]
    last_message = messages[-1]
    tool_iteration_count = state.get("tool_iteration_count", 0) + 1

    if tool_iteration_count > 5:
        print("\nCIRCUIT BREAKER TRIGGERED: Too many sequential tool loops. Forcing stop.")
        forced_message = AIMessage(
            content="I have gathered the available data from the database. Here are the results based on the tool queries executed."
        )
        return {
            "messages": [forced_message],
            "retry_node": 0,
            "tool_iteration_count": tool_iteration_count,
            "last_tool_signature": "",
            "next_action": "agent",
            "ai_message_count": state.get("ai_message_count", 0),
        }
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        tool_messages = []
        last_signature = state.get("last_tool_signature", None)
        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_id = tool_call.get("id", "call_1")
            current_signature = f"{tool_name}:{tool_args}"
            if current_signature == last_signature:
                print(f"\nLOOP GUARD: Blocked duplicate call to {tool_name} with {tool_args}")
                tool_messages.append(
                    ToolMessage(
                        content=(
                            "You just ran this exact tool with these exact arguments and received the output above. "
                            "Do NOT repeat this tool call. Use another tool with data you already have"
                            "You might need to think about using another tool and mention 'another tool' in your message to have opportunity to call this tool"
                            "Reflect in your next message what tool you are going to use in your next time"
                        ),
                        tool_call_id=tool_id,
                        name=tool_name,
                    )
                )
                continue
            tool_obj = TOOL_MAP.get(tool_name) or TOOL_MAP.get(normalize_tool_name(tool_name))

            if tool_obj:
                print(f"\n⚡ Executing Tool: {tool_name} with args {tool_args}...")
                try:
                    result = tool_obj.invoke(tool_args)
                    tool_messages.append(ToolMessage(content=str(result), tool_call_id=tool_id, name=tool_name))
                except Exception as e:
                    tool_messages.append(
                        ToolMessage(
                            content=f"Error executing {tool_name}: {str(e)}", tool_call_id=tool_id, name=tool_name
                        )
                    )
            else:
                tool_messages.append(
                    ToolMessage(content=f"Error: Tool '{tool_name}' not found.", tool_call_id=tool_id, name=tool_name)
                )
        new_signature = f"{last_message.tool_calls[0]['name']}:{last_message.tool_calls[0]['args']}"
        return {
            "messages": tool_messages,
            "ai_message_count": 0,
            "retry_count": 0,
            "tool_iteration_count": tool_iteration_count,
            "last_tool_signature": new_signature,
            "next_action": "agent",
        }

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
        "retry_count": retry_count,
        "ai_message_count": state.get("ai_message_count", 0),
        "next_action": "agent",
    }


def route_after_agent(state):
    messages = state["messages"]
    last_message = messages[-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "execute_tool"
    elif state.get("next_action") == "agent":
        return "agent"
    # if last_message.next_action == 'end'
    return END


def route_after_tool(state):
    messages = state["messages"]
    last_message = messages[-1]
    retry_count = state.get("retry_count", 0)

    if hasattr(last_message, "type") and last_message.type == "tool":
        content_str = str(last_message.content)
        if "Error" in content_str or "validation error" in content_str.lower():
            if retry_count < 2:
                return "retry"
            return END

    return "agent"


workflow = StateGraph(State)
workflow.add_node("agent", call_model)
workflow.add_node("execute_tool", execute_tool_node)
workflow.add_node("retry", retry_node)
workflow.set_entry_point("agent")
workflow.add_conditional_edges(
    "agent",
    route_after_agent,
    {
        "agent": "agent",
        "execute_tool": "execute_tool",
        END: END,
    },
)

workflow.add_conditional_edges("execute_tool", route_after_tool, {"retry": "retry", "agent": "agent", END: END})

workflow.add_edge("retry", "agent")

agent_executor = workflow.compile()
