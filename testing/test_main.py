from unittest.mock import patch, MagicMock
from langchain_core.messages import AIMessage
from langgraph.graph import END
with (
    patch("langchain_neo4j.Neo4jGraph") as mock_neo4j_graph,
    patch("app.agent.services.GraphDatabase") as mock_graph_db,
):
    mock_graph_instance = MagicMock()
    mock_neo4j_graph.return_value = mock_graph_instance

    from fastapi.testclient import TestClient
    from app.main import app
    import app.agent.graph as agent
    import app.agent.tools as tools


client = TestClient(app)


def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}
