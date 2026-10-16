import math
import os
from dotenv import dotenv_values
from neo4j import GraphDatabase
config = dotenv_values(".env")
URI = os.getenv("NEO4J_URI")
AUTH = (os.getenv("GRAPHS_USERNAME"), os.getenv("GRAPHS_PASS"))
try:
    driver = GraphDatabase.driver(URI, auth=AUTH)
except Exception as e:
    raise ConnectionError from e

def sanitize_floats(obj):
  """Recursively replaces NaN, Inf, and -Inf with None for JSON compliance."""
  if isinstance(obj, float):
    if math.isnan(obj) or math.isinf(obj):
      return None
    return obj
  elif isinstance(obj, dict):
    return {k: sanitize_floats(v) for k, v in obj.items()}
  elif isinstance(obj, list):
    return [sanitize_floats(v) for v in obj]
  return obj

def get_researcher_basic_info(who: str = None, author_id: int = None):
    """
    Takes id of author, and returns his id and his institution (NOT WORKS).
    In case more than 1 person have this name
    """
    query = """
    MATCH (n:Author)
    WHERE ($id IS NOT NULL AND n.id = $id)
       OR ($who IS NOT NULL AND $who <> '' AND toLower(n.name) CONTAINS toLower($who))
    RETURN n.name, n.id, n.Institution
    """
    with driver.session() as session:
        result = session.run(query, {"who": who, "id": author_id})
        return sanitize_floats([record.data() for record in result])


def get_h_index_of(author_id: int):
    """
    Takes id of author, and calculates his H-index
    """
    query = """
    
    MATCH (n:Author {id: $id})<-[:WRITTEN_BY]-(t:Article)
    OPTIONAL MATCH (a:Article)-[:REFERENCES]->(t)
    WITH t, count(a) AS citations
    ORDER BY citations DESC
    WITH collect(citations) AS citationCounts
    UNWIND range(1, size(citationCounts)) AS i
    WITH i, citationCounts[i-1] AS cit
    WHERE cit >= i
    RETURN coalesce(max(i), 0) AS h_index
    """
    with driver.session() as session:
        result = session.run(query, {"id": author_id})
        return [record.data() for record in result]

def get_articles_of_author(author_id: int):
    """
    Takes id of author, and returns 5 his most quoted works"""
    query = """
    
    MATCH (n:Author {id: $id})<-[:WRITTEN_BY]-(t:Article)
    OPTIONAL MATCH (a:Article)-[:REFERENCES]->(t)
    WITH n, t, count(a) AS citations
    RETURN n.name, n.id, t, citations
    ORDER BY citations DESC
    LIMIT 5
    """
    with driver.session() as session:
        result = session.run(query, {"id": author_id})
        return sanitize_floats([record.data() for record in result])

def get_alike(author_id: int):
    """
    Takes id of author, and returns 30 other
    researchers in the same community"""
    query = """
    CALL {
    MATCH (a:Author {id: $similar_to})
    RETURN a.louvainCommunity as id
    }
    WITH id
    MATCH (a:Author)
    WHERE a.louvainCommunity = id
    RETURN a.name
    LIMIT 30
    """
    with driver.session() as session:
        result = session.run(query, {"similar_to": author_id})
        return sanitize_floats([record.data() for record in result])

def get_path(id1: int, id2: int):
    """
    Takes id of researcher 1 and 2 and shows path between them by CO_AUTHORED_WITH relations"""
    query = """
    MATCH (sourceNodeObj {id: $source})
    MATCH (targetNodeObj {id: $target})
    CALL gds.allShortestPaths.delta.stream('Networking', {
        sourceNode: $source
    })
    YIELD index, sourceNode, targetNode, totalCost, nodeIds, costs, path
    WHERE targetNode = $target
    RETURN
        index,
        gds.util.asNode(sourceNode).name AS sourceNodeName,
        gds.util.asNode(targetNode).name AS targetNodeName,
        totalCost,
        [nodeId IN nodeIds | gds.util.asNode(nodeId).name] AS nodeNames,
        costs,
        nodes(path) AS path
    ORDER BY index
    """
    with driver.session() as session:
        result = session.run(query, {"source": id1, "target": id2})
        return sanitize_floats([record.data() for record in result])

def get_paper_basic_info(paper_id: int = None):
    """
    Takes id of paper, and returns info about this paper"""
    query = """
    MATCH (n:Article)
    WHERE ($id IS NOT NULL AND n.id = $id)
    RETURN n
    """
    with driver.session() as session:
        result = session.run(query, {"id": paper_id})
        return sanitize_floats([record.data() for record in result])

def get_keyword_alike(keyword: str):
    """
    Takes arbitrary keyword, and checks if keyword exists (or diff combinations)"""
    query = """
    MATCH (n:Keyword)
    WHERE n.id =~ ".*"+$id+".*"
    RETURN n
    LIMIT 10
    """
    with driver.session() as session:
        result = session.run(query, {"id": keyword})
        return sanitize_floats([record.data() for record in result])

def get_keyword_community(keyword: str):
    """
    Takes arbitrary keyword, and find 30 other \
    keywords that share the same community"""
    query = """
    MATCH (a:Keyword {communityId: $similar_to})
    WITH a, rand() as r
    ORDER BY r
    LIMIT 30
    RETURN a.name AS name, r
    
    """
    with driver.session() as session:
        result = session.run(query, {"similar_to": keyword})
        return sanitize_floats([record.data() for record in result])

def get_most_influential_papers_with_keyword(keyword: str):
    """
    Takes arbitrary keyword, and find 30 arbritrary articles with this keyword"""
    query = """
    MATCH (a:Article)-[:HAS_KEYWORD]->(k:Keyword {id: $id})
    WITH a, rand() as r
    ORDER BY r
    LIMIT 30
    RETURN a, r 
    """
    with driver.session() as session:
        result = session.run(query, {"id": keyword})
        return sanitize_floats([record.data() for record in result])

def get_most_influential_papers_with_field(keyword_community_id: int):
    """
    Takes community id (from api/keyword/get), and find 10 most quoted articles within this \
    community """
    query = """
    MATCH (a:Article)-[:HAS_KEYWORD]->(k:Keyword {communityId: $id})
    OPTIONAL MATCH (a:Article)-[:REFERENCES]->(t:Article)
    WITH a, count(t) AS citations
    RETURN a, citations
    ORDER BY citations DESC
    LIMIT 10
    """
    with driver.session() as session:
        result = session.run(query, {"id": keyword_community_id})
        return sanitize_floats([record.data() for record in result])

def get_most_influential_papers_with_text(text: str):
    """
    Takes search text, compares article items (title and abstract) \
    with search item and returns 20 random articles that have this search item
    """
    query = """
    MATCH (a:Article)
    WITH a, rand() as r
    WHERE a.title =~ ".*" + $id + ".*" OR a.rebuilt_abstract =~ ".*" + $id + ".*"
    ORDER BY r
    LIMIT 20
    RETURN a, rand() as r
    """
    with driver.session() as session:
        result = session.run(query, {"id": text})
        return sanitize_floats([record.data() for record in result])