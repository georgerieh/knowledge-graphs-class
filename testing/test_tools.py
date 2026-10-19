from unittest.mock import patch, MagicMock
from langchain_core.messages import AIMessage
from langgraph.graph import END
with (
    patch("langchain_neo4j.Neo4jGraph") as mock_neo4j_graph,
    patch("app.agent.services.GraphDatabase") as mock_graph_db,
):
    mock_graph_instance = MagicMock()
    mock_neo4j_graph.return_value = mock_graph_instance

    # from fastapi.testclient import TestClient
    # from app.main import app
    import app.agent.tools as tools
    import app.agent.services as services

def test_tool_get_h_index():
    author_id = 1
    called_function = tools.tool_get_h_index_of.invoke(input={'author_id':author_id})
    assert called_function == {'status': 'not_found', 'data': [], 'message': 'No researcher found in db.'}
    
def test_tool_get_h_index_exception():
    with patch("app.agent.tools.get_h_index_of") as mock_get_info:
        
        exc_group = ExceptionGroup("Database failed", [Exception("Connection timeout")])
        mock_get_info.side_effect = exc_group

        response = tools.tool_get_h_index_of.invoke({"author_id": 1})
        expected_key = str(exc_group)
        assert response == {expected_key: "Impossible to get info (Tool: h_index)"}

def test_tool_get_alike():
    author_id = 1
    called_function = tools.tool_get_alike.invoke(input={'author_id':author_id})
    assert called_function == {'status': 'not_found', 'data': [], 'message': 'No researcher found in database.'}

def test_get_alike_exception():
    with patch("app.agent.tools.get_alike") as mock_function_call:
        
        exc_group = ExceptionGroup("Database failed", [Exception("Connection timeout")])
        mock_function_call.side_effect = exc_group

        response = tools.tool_get_alike.invoke({"author_id": 1})
        expected_key = str(exc_group)
        assert response == {expected_key: "Impossible to get info (Tool: community/search)"}

def test_tool_get_path():
    author_id = 1
    called_function = tools.tool_get_path.invoke(input={'id1':author_id, 'id2': author_id})
    assert called_function == {'status': 'not_found', 'data': [], 'message': "No path between 2 researches'."} 

def test_tool_get_path_exception():
    with patch("app.agent.tools.get_path") as mock_function_call:
        
        exc_group = ExceptionGroup("Database failed", [Exception("Connection timeout")])
        mock_function_call.side_effect = exc_group

        response = tools.tool_get_path.invoke({"id1": 1, "id2": 2})
        expected_key = str(exc_group)
        assert response == {expected_key: "Impossible to get info (Tool: networking)"}


def test_tool_get_paper_basic_info():
    paper_id = 1
    called_function = tools.tool_get_paper_basic_info.invoke(input={'paper_id':paper_id})
    assert called_function == {'status': 'not_found', 'data': [], 'message': "No articles for 1'."}

def test_tool_get_paper_basic_info_exception():
    with patch("app.agent.tools.get_paper_basic_info") as mock_function_call:
        
        exc_group = ExceptionGroup("Database failed", [Exception("Connection timeout")])
        mock_function_call.side_effect = exc_group

        response = tools.tool_get_paper_basic_info.invoke({"paper_id": 1})
        expected_key = str(exc_group)
        assert response == {expected_key: "Impossible to get info (Tool: paper_basic_info)"}


def test_tool_get_keyword_alike_api():
    keyword = 'str'
    called_function = tools.tool_get_keyword_alike.invoke(input={'keyword':keyword})
    assert called_function ==  {'status': 'not_found', 'data': [], 'message': "No keyword look alikes found for 'str'. Try checking for typos or use a broader term."}

def test_tool_get_keyword_alike_exception():
    with patch("app.agent.tools.get_keyword_alike") as mock_function_call:
        
        exc_group = ExceptionGroup("Database failed", [Exception("Connection timeout")])
        mock_function_call.side_effect = exc_group

        response = tools.tool_get_keyword_alike.invoke({"keyword": 'str'})
        expected_key = str(exc_group)
        assert response == {expected_key: "Impossible to get info (Tool: keyword alike)"}

def test_tool_get_articles_of_author():
    author_id = 1
    called_function = tools.tool_get_articles_of_author.invoke(input={'author_id':author_id})
    assert called_function == {'status': 'not_found', 'data': [], 'message': "No articles for 1'."}

def test_tool_get_articles_of_author_exception():
    with patch("app.agent.tools.get_articles_of_author") as mock_function_call:
        
        exc_group = ExceptionGroup("Database failed", [Exception("Connection timeout")])
        mock_function_call.side_effect = exc_group

        response = tools.tool_get_articles_of_author.invoke({"author_id": 1})
        expected_key = str(exc_group)
        assert response == {expected_key: "Impossible to get info (Tool: influential works)"}
    

def test_tool_get_keyword_community():
    id = 1
    called_function = tools.tool_get_keyword_community.invoke(input={'id_':id})
    assert called_function == {'status': 'not_found', 'data': [], 'message': 'No keyword is found with this id.'}

def test_tool_get_keyword_community_exception():
    with patch("app.agent.tools.get_keyword_community") as mock_function_call:
        
        exc_group = ExceptionGroup("Database failed", [Exception("Connection timeout")])
        mock_function_call.side_effect = exc_group

        response = tools.tool_get_keyword_community.invoke({"id_": 1})
        expected_key = str(exc_group)
        assert response == {expected_key: "Impossible to get info (Tool: keyword community)"}
    


def test_tool_get_most_influential_papers_with_text():
    text = 'text'
    called_function = tools.tool_get_most_influential_papers_with_text.invoke(input={'text':text})
    assert called_function ==  {'status': 'not_found', 'data': [], 'message': "No articles found with text in db'."}

def test_tool_get_most_infl_papers_with_text_exception():
    with patch("app.agent.tools.get_most_influential_papers_with_text") as mock_function_call:
        
        exc_group = ExceptionGroup("Database failed", [Exception("Connection timeout")])
        mock_function_call.side_effect = exc_group

        response = tools.tool_get_most_influential_papers_with_text.invoke({"text": 'str'})
        expected_key = str(exc_group)
        assert response == {expected_key: "Impossible to get info (Tool: tool_get_most_influential_papers_with_text)"}


def test_tool_get_most_influential_papers_with_field():
    keyword_community_id = 1
    called_function = tools.tool_get_most_influential_papers_with_field.invoke(input={'keyword_community_id':keyword_community_id})
    assert called_function == {'status': 'not_found', 'data': [], 'message': 'No articles found with this community id.'} 

def test_tool_get_most_infl_papers_with_field_exception():
    with patch("app.agent.tools.get_most_influential_papers_with_field") as mock_function_call:
        
        exc_group = ExceptionGroup("Database failed", [Exception("Connection timeout")])
        mock_function_call.side_effect = exc_group

        response = tools.tool_get_most_influential_papers_with_field.invoke({"keyword_community_id": 1})
        expected_key = str(exc_group)
        assert response == {expected_key: "Impossible to get info (Tool: tool_get_most_influential_papers_with_field )"}


def test_tool_get_most_influential_papers_with_keyword():
    keyword = 'str'
    called_function = tools.tool_get_most_influential_papers_with_keyword.invoke(input={'keyword': keyword})
    # assert called_function == services.get_most_influential_papers_with_keyword(keyword=keyword)
    assert called_function == {'status': 'not_found', 'data': [], 'message': "No articles found with this keyword mentioned'."}
    # assert called_function == []

def test_tool_get_most_infl_papers_with_keyword_exception():
    with patch("app.agent.tools.get_most_influential_papers_with_keyword") as mock_function_call:
        
        exc_group = ExceptionGroup("Database failed", [Exception("Connection timeout")])
        mock_function_call.side_effect = exc_group

        response = tools.tool_get_most_influential_papers_with_keyword.invoke({"keyword": 'str'})
        expected_key = str(exc_group)
        assert response == {expected_key: "Impossible to get info (Tool: tool_get_most_influential_papers_with_keyword)"}

def test_execure_query():
    query = 'str'
    called_function = tools.execute_query(query= query)
    assert called_function == services.execute_query(query=query)

    