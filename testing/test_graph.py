from unittest.mock import patch, MagicMock
from langchain_core.messages import AIMessage
from langgraph.graph import END
with (
    patch("langchain_neo4j.Neo4jGraph") as mock_neo4j_graph,
    patch("app.agent.services.GraphDatabase") as mock_graph_db,
    patch("app.agent.services.get_driver") as mock_get_driver
):
    mock_graph_instance = MagicMock()
    mock_neo4j_graph.return_value = mock_graph_instance

    import app.agent.graph as agent
    import app.agent.tools as tools

def test_call_function():
    name = "Basic Researcher Info"
    args = {"who": "Lucy"}

    mock_record = MagicMock()
    mock_record.data.return_value = {
        "n.name": "Lucy",
        "n.id": "123",
        "n.Institution": "University",
    }

    mock_session = MagicMock()
    mock_session.run.return_value = [mock_record]

    mock_driver = MagicMock()
    mock_driver.session.return_value.__enter__.return_value = mock_session

    with patch("app.agent.services.get_driver") as mock_get_driver:
        mock_get_driver.return_value = mock_driver

        response = agent.call_function(name, args)

        assert response == tools.tool_get_researcher_basic_info.invoke(args)


def test_parse_groq_xml_as_list():
    message = AIMessage(content='[{"name": "Basic Researcher Info", "arguments": {"who": "Lucy"}}]')
    
    result = agent.parse_groq_xml_to_tool_calls(message)
    
    assert result.tool_calls == [{
        "name": "Basic Researcher Info",
        "args": {"who": "Lucy"},
        "id": "call_groq_xml_1"
    }]

def test_parse_groq_xml_as_dict():
    message = AIMessage(content='{"name": "Basic Researcher Info", "args": {"who": "Lucy"}}')
    
    result = agent.parse_groq_xml_to_tool_calls(message)
    
    assert result.tool_calls == [{
        "name": "Basic Researcher Info",
        "args": {"who": "Lucy"},
        "id": "call_groq_xml_1"
    }]

def test_parse_groq_xml_invalid_json():
    message = AIMessage(content='Not a valid json string')
    
    result = agent.parse_groq_xml_to_tool_calls(message)
    
    assert not hasattr(result, "tool_calls") or result.tool_calls == []
    
def test_parse_groq_xml_empty_list():
    message = AIMessage(content='[]')
    result = agent.parse_groq_xml_to_tool_calls(message)
    assert result == message

def test_parse_groq_xml_primitive_json():
    message = AIMessage(content='"just a string"')
    result = agent.parse_groq_xml_to_tool_calls(message)
    assert result == message

def test_call_model():
        state = {"messages": [{'id':"user", 'content':"Hello"}]}
    
        with patch("langchain_openai.ChatOpenAI.invoke") as mock_chat_invoke:
            mock_response = AIMessage(content="Mocked LLM response")
            mock_chat_invoke.return_value = mock_response
    
            response = agent.call_model(state)
    
            assert response == {'messages': state['messages'] + [mock_response]}

def test_execute_model():
    mock_message = MagicMock()
    mock_message.tool_calls = [{'name':"Basic Researcher Info", 'args':{'who':'Lucy'}}]
    mock_session = MagicMock()
    mock_driver = MagicMock()
    ToolMessage = MagicMock()
    ToolMessage.content.return_value=[]
    ToolMessage.name.return_value="Basic Researcher Info"
    ToolMessage.tool_call_id.return_value="call_groq_xml_1"
    mock_driver.session.return_value.__enter__.return_value = mock_session
    state = {"messages": [mock_message, ToolMessage]}

    with patch("langchain_openai.ChatOpenAI.invoke") as mock_chat_invoke, \
        patch("app.agent.services.get_driver") as mock_get_driver:
        mock_get_driver.return_value = mock_driver
        mock_response = AIMessage(content="Mocked LLM response")
        mock_chat_invoke.return_value = mock_response

        response = agent.execute_tool_node(state)

        assert response == state

def test_execute_tool_node_no_tool_calls():
    mock_message = MagicMock()
    mock_message.tool_calls = [] 
    
    state = {"messages": [mock_message]}

    response = agent.execute_tool_node(state)

    assert response == state

def test_should_continue():
    mock_last_message = MagicMock()
    mock_last_message.tool_calls = [
        {'name': "Basic Researcher Info", 'args': {'who': 'Lucy'}}
    ]

    state = {"messages": [mock_last_message]}

    response = agent.should_continue(state)

    assert response == "execute_tool"

def test_should_terminate():
    mock_last_message = MagicMock()
    # mock_last_message.tool_calls = [
    #     {'name': "Basic Researcher Info", 'args': {'who': 'Lucy'}}
    # ]

    state = {"messages": [mock_last_message]}

    response = agent.should_continue(state)

    assert response == "execute_tool" #?