import math
import os
from dotenv import dotenv_values
from CyVer import SyntaxValidator, SchemaValidator
from neo4j import GraphDatabase

config = dotenv_values(".env")
URI = os.getenv("NEO4J_URI")
AUTH = (os.getenv("GRAPHS_USERNAME"), os.getenv("GRAPHS_PASS"))
driver = None


def get_driver():
    global driver
    if driver is None:
        try:
            uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
            user = os.getenv("NEO4J_USER", "neo4j")
            password = os.getenv("NEO4J_PASSWORD", "password")
            driver = GraphDatabase.driver(uri, auth=(user, password))
            return driver
        except Exception as e:
            raise ConnectionError from e
    else:
        return driver
_syntax_validator = None

def get_syntax_validator():
    global _syntax_validator
    if _syntax_validator is None:
        try:
            driver = get_driver()
            if driver:
                _syntax_validator = SyntaxValidator(driver, check_multilabeled_nodes=True)
        except ExceptionGroup:
            pass
    return _syntax_validator

_schema_validator = None

def get_schema_validator():
    global _schema_validator
    if _schema_validator is None:
        try:
            driver = get_driver()
            if driver:
                _schema_validator = SchemaValidator(driver)
        except ExceptionGroup:
            pass
    return _schema_validator

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
    with get_driver().session() as session:
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
    with get_driver().session() as session:
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
    with get_driver().session() as session:
        result = session.run(query, {"id": author_id})
        return sanitize_floats([record.data() for record in result])


def get_alike(author_id: int):
    """
    Takes id of author, and returns 30 other
    researchers in the same community"""
    query = """
    CALL {
    MATCH (a:Author {id: $similar_to})
    RETURN a.communityId as id
    }
    WITH id
    MATCH (a:Author {communityId: id})
    with a, rand() as sorting_parameter_ignore
    ORDER BY sorting_parameter_ignore
    LIMIT 30
    RETURN a.name, a.id, a.Institution, sorting_parameter_ignore
    """
    with get_driver().session() as session:
        result = session.run(query, {"similar_to": author_id})
        return sanitize_floats([record.data() for record in result])


def get_path(id1: int, id2: int):
    """
    Takes id of researcher 1 and 2 and shows path between them by CO_AUTHORED_WITH relations"""
    query = """
    MATCH (n:Author {id: $source})
    MATCH (m:Author {id: $target})
    CALL gds.shortestPath.dijkstra.stream('Networking', {
        sourceNode: n,
        targetNode: m
    })
    YIELD sourceNode, targetNode, totalCost, nodeIds
    RETURN 
        gds.util.asNode(sourceNode).name AS source, 
        gds.util.asNode(targetNode).name AS target, 
        totalCost AS distance,
        [nodeId IN nodeIds | gds.util.asNode(nodeId).name] AS pathAuthorNames
    """
    with get_driver().session() as session:
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
    with get_driver().session() as session:
        result = session.run(query, {"id": paper_id})
        return sanitize_floats([record.data() for record in result])


def get_keyword_alike(keyword: str):
    """
    Takes arbitrary keyword, and checks if keyword exists (or diff combinations)"""
    query = """
    MATCH (n:Keyword)
    WHERE n.id =~ toLower(".*"+$id+".*")
    RETURN n
    LIMIT 10
    """
    with get_driver().session() as session:
        result = session.run(query, {"id": keyword})
        return sanitize_floats([record.data() for record in result])


def get_keyword_community(community_id: int):
    """
    Takes arbitrary keyword, and find 30 other \
    keywords that share the same community"""
    query = """
    MATCH (a:Keyword {communityId: $similar_to})
    WITH a, rand() as sorting_parameter_ignore
    ORDER BY sorting_parameter_ignore
    LIMIT 30
    RETURN a.name AS name, sorting_parameter_ignore
    
    """
    with get_driver().session() as session:
        result = session.run(query, {"similar_to": community_id})
        return sanitize_floats([record.data() for record in result])


def get_most_influential_papers_with_keyword(keyword: str):
    """
    Takes arbitrary keyword, and find 30 arbritrary articles with this keyword"""
    query = """
    MATCH (a:Article)-[:HAS_KEYWORD]->(k:Keyword {id: $id})
    WITH a, rand() as sorting_parameter_ignore
    ORDER BY sorting_parameter_ignore
    LIMIT 30
    RETURN a, sorting_parameter_ignore 
    """
    with get_driver().session() as session:
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
    with get_driver().session() as session:
        result = session.run(query, {"id": keyword_community_id})
        return sanitize_floats([record.data() for record in result])


def get_most_influential_papers_with_text(text: str):
    """
    Takes search text, compares article items (title and abstract) \
    with search item and returns 20 random articles that have this search item
    """
    query = """
    MATCH (a:Article)
    WITH a, rand() as sorting_parameter_ignore
    WHERE a.title =~ toLower(".*" + '$id' + ".*") OR a.rebuilt_abstract =~ toLower(".*" + $id + ".*")
    WITH a, sorting_parameter_ignore
    ORDER BY sorting_parameter_ignore
    LIMIT 20
    RETURN a, sorting_parameter_ignore
    """
    with get_driver().session() as session:
        result = session.run(query, {"id": text})
        return sanitize_floats([record.data() for record in result])


def execute_query(query: str):
    """
    Takes arbitrary query as input and returns result from Neo4j
    """
    with get_driver().session() as session:
        result = session.run(query)
        return sanitize_floats([record.data() for record in result])
