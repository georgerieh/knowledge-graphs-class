from unittest.mock import patch, MagicMock
import numpy as np
import pytest
import neo4j
with (
    patch("langchain_neo4j.Neo4jGraph") as mock_neo4j_graph,
    patch("app.agent.services.GraphDatabase") as mock_graph_db,
):
    mock_graph_instance = MagicMock()
    mock_neo4j_graph.return_value = mock_graph_instance
    # from fastapi.testclient import TestClient
    from app.main import app
    import app.agent.services as services

def test_sanitize_floats():

    mock_record = MagicMock(spec=dict)
    mock_record.return_value = {'key': np.nan}
    mock_driver = MagicMock()
    with patch("app.agent.services.get_driver") as mock_get_driver:
        mock_get_driver.return_value = mock_driver

        response = services.sanitize_floats(mock_record)

        assert response == {}

def test_get_driver():
    with patch("app.agent.services.GraphDatabase") as mock_graph_db:
        driver = MagicMock()
        mock_graph_db.driver.return_value = driver

        
        response = services.get_driver()
        assert response == driver

def test_get_driver_not_available():
    services.driver = None
    with patch("app.agent.services.GraphDatabase") as mock_graph_db:
        mock_graph_db.driver.side_effect = Exception("Connection failed")
        with pytest.raises(ConnectionError):
            services.get_driver()

def test_get_driver_exists():
    driver = MagicMock()
    services.driver = driver
    response = services.get_driver()
    assert response == driver
    
def test_get_h_index_of():
    author_id = 1
    mock_record = MagicMock()
    mock_record.data.return_value = {'node': 'value'}
    mock_session = MagicMock()
    mock_session.run.return_value = [mock_record]
    mock_driver = MagicMock()
    mock_driver.session.return_value.__enter__.return_value = mock_session
    with patch("app.agent.services.get_driver") as mock_get_driver:
        mock_get_driver.return_value = mock_driver
        response = services.get_h_index_of(author_id=author_id)
        assert response == [{'node': 'value'}]

def test_get_articles_of_author():
    author_id = 1
    mock_record = MagicMock()
    mock_record.data.return_value = {'node': 'value'}
    mock_session = MagicMock()
    mock_session.run.return_value = [mock_record]
    mock_driver = MagicMock()
    mock_driver.session.return_value.__enter__.return_value = mock_session
    with patch("app.agent.services.get_driver") as mock_get_driver:
        mock_get_driver.return_value = mock_driver
        response = services.get_articles_of_author(author_id=author_id)
        assert response == [{'node': 'value'}]

def test_get_alike():
    author_id = 1
    mock_record = MagicMock()
    mock_record.data.return_value = {'author_id': 1, 'node':'value'}
    mock_session = MagicMock()
    mock_session.run.return_value = [mock_record]
    mock_driver = MagicMock()
    mock_driver.session.return_value.__enter__.return_value = mock_session
    with patch("app.agent.services.get_driver") as mock_get_driver:
        mock_get_driver.return_value = mock_driver
        response = services.get_alike(author_id=author_id)
        assert response == [{'author_id': 1, 'node':'value'}]
        mock_session.run.assert_called_once()
        called_args = mock_session.run.call_args[0] ## session.run
        assert author_id in called_args[1].values()
        

def test_get_path():
    author_id = 1
    author_id2 = 2
    
    mock_record = MagicMock()
    mock_record.data.return_value = {
        'source': 'Alice', 
        'target': 'Bob', 
        'distance': 2.0, 
        'pathAuthorNames': ['Alice', 'Charlie', 'Bob']
    }

    mock_session = MagicMock()
    mock_session.run.return_value = [mock_record]
    
    mock_driver = MagicMock()
    mock_driver.session.return_value.__enter__.return_value = mock_session

    with patch("app.agent.services.get_driver") as mock_get_driver:
        mock_get_driver.return_value = mock_driver

        response = services.get_path(id1=author_id, id2=author_id2)
        
        assert response == [{
            'source': 'Alice', 
            'target': 'Bob', 
            'distance': 2.0, 
            'pathAuthorNames': ['Alice', 'Charlie', 'Bob']
        }]

        mock_session.run.assert_called_once()
        called_args = mock_session.run.call_args[0] ## session.run
        assert author_id in called_args[1].values() or author_id == called_args[1].get("source")

def test_paper():
    paper_id = 1
    
    mock_record = MagicMock()
    mock_record.data.return_value = {
        'paper_id': 1, 
        'node': 'value'
    }

    mock_session = MagicMock()
    mock_session.run.return_value = [mock_record]
    
    mock_driver = MagicMock()
    mock_driver.session.return_value.__enter__.return_value = mock_session

    with patch("app.agent.services.get_driver") as mock_get_driver:
        mock_get_driver.return_value = mock_driver

        response = services.get_paper_basic_info(paper_id=paper_id)
        
        assert response == [{
        'paper_id': 1, 
        'node': 'value'
        }]

        mock_session.run.assert_called_once()
        called_args = mock_session.run.call_args[0] ## session.run
        assert paper_id in called_args[1].values() or paper_id == called_args[1].get("paper_id")

def test_keyword_alike():
    keyword = 'string'
    mock_record = MagicMock()
    mock_record.data.return_value = {
        'keyword': 'string', 
        'node': 'value'
    }

    mock_session = MagicMock()
    mock_session.run.return_value = [mock_record]
    
    mock_driver = MagicMock()
    mock_driver.session.return_value.__enter__.return_value = mock_session

    with patch("app.agent.services.get_driver") as mock_get_driver:
        mock_get_driver.return_value = mock_driver

        response = services.get_keyword_alike(keyword=keyword)
        
        assert response == [{
        'keyword': 'string', 
        'node': 'value'
    }]

        mock_session.run.assert_called_once()
        called_args = mock_session.run.call_args[0] ## session.run
        assert keyword in called_args[1].values() or keyword == called_args[1]['keyword']

def test_keyword_community():
    keyword_community_id = 1
    
    mock_record = MagicMock()
    mock_record.data.return_value = {
        'keyword': 'string', 
        'node': 'value',
        'communityId': 1
    }

    mock_session = MagicMock()
    mock_session.run.return_value = [mock_record]
    
    mock_driver = MagicMock()
    mock_driver.session.return_value.__enter__.return_value = mock_session

    with patch("app.agent.services.get_driver") as mock_get_driver:
        mock_get_driver.return_value = mock_driver

        response = services.get_keyword_community(community_id=keyword_community_id)
        
        assert response == [{
            'keyword': 'string', 
            'node': 'value',
            'communityId': 1
        }]

        mock_session.run.assert_called_once()
        called_args = mock_session.run.call_args[0] ## session.run
        assert keyword_community_id in called_args[1].values() or keyword_community_id == called_args[1]['communityId']

def test_get_most_influential_papers_with_keyword():
    keyword = 'string'
    
    mock_record = MagicMock()
    mock_record.data.return_value = {
        'keyword': 'string', 
        'node': 'value',
        'communityId': 1
    }

    mock_session = MagicMock()
    mock_session.run.return_value = [mock_record]
    
    mock_driver = MagicMock()
    mock_driver.session.return_value.__enter__.return_value = mock_session

    with patch("app.agent.services.get_driver") as mock_get_driver:
        mock_get_driver.return_value = mock_driver

        response = services.get_most_influential_papers_with_keyword(keyword=keyword)
        
        assert response == [{
            'keyword': 'string', 
            'node': 'value',
            'communityId': 1
        }]

        mock_session.run.assert_called_once()
        called_args = mock_session.run.call_args[0] ## session.run
        assert keyword in called_args[1].values() or keyword == called_args[1]['keyword']

def test_get_most_ifluential_papers_with_field():
    keyword_community_id = 1
    
    mock_record = MagicMock()
    mock_record.data.return_value = {
        'keyword': 'string', 
        'node': 'value',
        'communityId': 1
    }

    mock_session = MagicMock()
    mock_session.run.return_value = [mock_record]
    
    mock_driver = MagicMock()
    mock_driver.session.return_value.__enter__.return_value = mock_session

    with patch("app.agent.services.get_driver") as mock_get_driver:
        mock_get_driver.return_value = mock_driver

        response = services.get_most_influential_papers_with_field(keyword_community_id=keyword_community_id)
        
        assert response == [{
            'keyword': 'string', 
            'node': 'value',
            'communityId': 1
        }]

        mock_session.run.assert_called_once()
        called_args = mock_session.run.call_args[0] ## session.run
        assert keyword_community_id in called_args[1].values() or keyword_community_id == called_args[1]['communityId']

def test_get_most_ifluential_papers_with_text():
    text = 'value'
    
    mock_record = MagicMock()
    mock_record.data.return_value = {
        'keyword': 'string', 
        'text': 'value',
        'communityId': 1
    }

    mock_session = MagicMock()
    mock_session.run.return_value = [mock_record]
    
    mock_driver = MagicMock()
    mock_driver.session.return_value.__enter__.return_value = mock_session

    with patch("app.agent.services.get_driver") as mock_get_driver:
        mock_get_driver.return_value = mock_driver

        response = services.get_most_influential_papers_with_text(text=text)
        
        assert response == [{
            'keyword': 'string', 
            'text': 'value',
            'communityId': 1
        }]

        mock_session.run.assert_called_once()
        called_args = mock_session.run.call_args[0] ## session.run
        assert text in called_args[1].values() or text == called_args[1]['text']

def test_execute_query():
    text = 'MATCH n RETURN n LIMIT 1'
    
    mock_record = MagicMock()
    mock_record.data.return_value = {
        'keyword': 'string', 
        'text': 'value',
        'communityId': 1
    }
    mock_result = MagicMock()
    mock_result.single.return_value = mock_record

    mock_session = MagicMock()
    mock_session.run.return_value = mock_result
    
    mock_driver = MagicMock(spec=neo4j.Driver)
    mock_driver.session.return_value.__enter__.return_value = mock_session

    with patch("app.agent.services.get_driver") as mock_get_driver, \
    patch("app.agent.services.get_syntax_validator") as mock_get_validator:
        
        mock_get_driver.return_value = mock_driver
        
        mock_validator_instance = MagicMock()
        mock_validator_instance.validate.return_value = (True, [])
        mock_get_validator.return_value = mock_validator_instance

        response = services.execute_query(query=text)
        assert response == []
        mock_session.run.assert_called_once_with(text)