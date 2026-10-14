from fastapi import FastAPI, Query, Depends
from neo4j import GraphDatabase
from dotenv import dotenv_values
from load import main, run_query
import os

config = dotenv_values(".env")

app = FastAPI()

URI = os.getenv("NEO4J_URI")
AUTH = (config["graphs_username"], config["graphs_pass"])
try:
    driver = GraphDatabase.driver(URI, auth=AUTH)
except:
    pass


def get_db_driver():
    return driver


@app.on_event("startup")
async def startup_event():
    driver.verify_connectivity()
    print("Connection established.")
    with driver.session() as session:
        result = session.run("MATCH (n) RETURN count(n) AS count")
        count = result.single()["count"]

        if count > 0:
            print(f"Database already contains data ({count} nodes). Skipping import.")

        else:
            print("Database is empty. Starting import...")
            main(driver)
            print("Data successfully loaded.")

        proj_result = session.run(
            """
                CALL gds.graph.project.cypher(
                    'Networking',
                    'MATCH (auth:Author) RETURN id(auth) AS id',
                    'MATCH (auth1:Author)<-[:WRITTEN_BY]-(a:Article)-[:WRITTEN_BY]->(auth2:Author)
                    WHERE auth1 < auth2
                    RETURN id(auth1) as source, id(auth2) as target, "CO_AUTHORED_WITH" AS type'
                )
                YIELD nodeCount, relationshipCount
                RETURN nodeCount, relationshipCount
            """
        )
        record = proj_result.single()
        print(
            f"Graph 'Networking' projected: {record['nodeCount']} nodes, {record['relationshipCount']} relationships."
        )
        louvain_result = session.run(
                    """
                        CALL gds.louvain.write(
                            'Networking',
                            {
                                writeProperty: 'communityId'
                            }
                        )
                        YIELD communityCount, modularity, ranLevels
                        RETURN communityCount, modularity, ranLevels
                    """)
        l_record = louvain_result.single()
        print(
            f"Louvain completed: {l_record['communityCount']} communities found (Modularity: {l_record['modularity']:.4f})."
        )
        proj_result2 = session.run(
            """
                CALL gds.graph.project.cypher(
                    'KeywordNetwork',
                    'MATCH (k:Keyword) RETURN id(k) AS id',
                    'MATCH (k1:Keyword)<-[:HAS_KEYWORD]-(a:Article)-[:HAS_KEYWORD]->(k2:Keyword)
                    WHERE id(k1) < id(k2)
                    RETURN id(k1) AS source, id(k2) AS target, "SHARED_ARTICLE" AS type'
                )
                YIELD nodeCount, relationshipCount
                RETURN nodeCount, relationshipCount
            """
        )
        record = proj_result2.single()
        print(
            f"Graph 'KeywordNetwork' projected: {record['nodeCount']} nodes, {record['relationshipCount']} relationships."
        )
        louvain_result2 = session.run(""" \
                CALL gds.louvain.write(
                    'KeywordNetwork',
                    {
                        writeProperty: 'communityId'
                    }
                )
                YIELD communityCount, modularity, ranLevels
                RETURN communityCount, modularity, ranLevels
            """)
        l_record = louvain_result2.single()
        print(
            f"Louvain completed: {l_record['communityCount']} communities found (Modularity: {l_record['modularity']:.4f})."
        )


@app.get("/")
async def root():
    # TODO: Add main page
    return {"message": "Hello World"}


# @app.get("/api/researcher/explore")
# async def get_researcher_suggestions_from_db( who: str = "", driver = Depends(get_db_driver)):
#     query = '''
#     MATCH (n:Author)
#     WHERE n.name =~ ".*$who.*"
#     RETURN n.name, n.id, n.institution
#     '''
#     with driver.session() as session:
#         result = session.run(query, {'name': who})
#         return [record.data() for record in result]
#     # if not results:
#     #     return f"No researcher found similar t name {who}."
#     # else:
#     #     names_list = [record["name"] for record in results]
#     #     return f"Possible names of {who} are: " + ", ".join(names_list)
#     return results


@app.get("/api/researcher/get_info")
def get_researcher_basic_info_api(who: str = None, id: int = None, driver=Depends(get_db_driver)):
    query = """
    MATCH (n:Author)
    WHERE ($id IS NOT NULL AND n.id = $id)
       OR ($who IS NOT NULL AND $who <> '' AND toLower(n.name) CONTAINS toLower($who))
    RETURN n.name, n.id, n.institution
    LIMIT 5
    """
    with driver.session() as session:
        result = session.run(query, {"who": who, "id": id})
        return [record.data() for record in result]
    # if not results:
    #     return f"No researcher found similar t name {who}."
    # else:
    #     names_list = [record["name"] for record in results]
    #     return f"Possible names of {who} are: " + ", ".join(names_list)


@app.get("/api/researcher/get_works_info")
def get_researcher_works_info_api(id: int, driver=Depends(get_db_driver)):
    query = """
    CALL {
        MATCH (n:Author {id: $id})<-[:WRITTEN_BY]-(m)
        RETURN m.id as paper, COUNT((m)<-[:REFERENCES]-[n]) AS quotes
    }
    RETURN paper, quotes
    ORDER BY quotes DESC
    """
    with driver.session() as session:
        result = session.run(query, {"id": id})
        return [record.data() for record in result]
    # if not results:
    #     return f"No researcher found similar t name {who}."
    # else:
    #     names_list = [record["name"] for record in results]
    #     return f"Possible names of {who} are: " + ", ".join(names_list)


@app.get("/api/researcher/h_index")
def get_h_index_of_api(id: int, driver=Depends(get_db_driver)):
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
        result = session.run(query, {"id": id})
        return [record.data() for record in result]
    # if not results:
    #     return f"No researcher found with name {of}."
    # else:
    #     return f"H-index of {of} is {results}"


@app.get("/api/researcher/most_influential")
def get_articles_of_author_api(id: int, driver=Depends(get_db_driver)):
    query = """
    
    MATCH (n:Author {id: $id})<-[:WRITTEN_BY]-(t:Article)
    OPTIONAL MATCH (a:Article)-[:REFERENCES]->(t)
    WITH t, count(a) AS citations
    RETURN n.name, n.id, t, citatitions
    ORDER BY citations DESC
    LIMIT 5
    """
    with driver.session() as session:
        result = session.run(query, {"id": id})
        return [record.data() for record in result]
    # if not results:
    #     return f"No researcher found with name {of}."
    # else:
    #     return f"H-index of {of} is {results}"


@app.get("/api/community/search")
def get_alike_api(id: int, driver=Depends(get_db_driver)):
    query = """
    CALL {
    MATCH (a:Author {id: $similar_to})
    RETURN a.louvainCommunity as id
    }
    WITH id
    MATCH (a:Author)
    WHERE a.louvainCommunity = id
    RETURN a.name
    """
    with driver.session() as session:
        result = session.run(query, {"similar_to": id})
        return [record.data() for record in result]


## introduce one scientist to another path


@app.get("/api/networking")
def get_path_api(id1: int, id2: int, driver=Depends(get_db_driver)):
    query = """
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
        return [record.data() for record in result]


@app.get("/api/paper/get_info")
def get_paper_basic_info_api(id: int = None, driver=Depends(get_db_driver)):
    query = """
    MATCH (n:Article)
    WHERE ($id IS NOT NULL AND n.id = $id)
    RETURN n
    """
    with driver.session() as session:
        result = session.run(query, {"id": id})
        return [record.data() for record in result]
    # if not results:
    #     return f"No researcher found similar t name {who}."
    # else:
    #     names_list = [record["name"] for record in results]
    #     return f"Possible names of {who} are: " + ", ".join(names_list)


@app.get("/api/keyword/get")
def get_keyword_alike_api(keyword: str, driver=Depends(get_db_driver)):
    query = """
    MATCH (n:Keyword)
    WHERE n.id =~ ".*"+$id+".*"
    RETURN n
    LIMIT 10
    """
    with driver.session() as session:
        result = session.run(query, {"id": keyword})
        return [record.data() for record in result]

@app.get("/api/keyword/search")
def get_keyword_community_api(id: int, driver=Depends(get_db_driver)):
    query = """
    MATCH (a:Keyword {communityId: $similar_to})
    WITH a, rand() as r
    ORDER BY r
    LIMIT 30
    RETURN a.name AS name, r
    
    """
    with driver.session() as session:
        result = session.run(query, {"similar_to": id})
        return [record.data() for record in result]
    
@app.get("/api/article/search_by_keyword")
def get_most_influential_papers_with_keyword_api(id: str, driver=Depends(get_db_driver)):
    query = """
    MATCH (a:Article)-[:HAS_KEYWORD]->(k:Keyword {id: $id})
    WITH a, rand() as r
    ORDER BY r
    LIMIT 30
    RETURN a, r 
    """
    with driver.session() as session:
        result = session.run(query, {"id": id})
        return [record.data() for record in result]

@app.get("/api/article/search_by_field")
def get_most_influential_papers_with_field_api(id: int, driver=Depends(get_db_driver)):
    query = """
    MATCH (a:Article)-[:HAS_KEYWORD]->(k:Keyword {communityId: $id})
    OPTIONAL MATCH (a:Article)-[:REFERENCES]->(t:Article)
    WITH a, count(t) AS citations
    RETURN a, citations
    ORDER BY citations DESC
    LIMIT 10
    """
    with driver.session() as session:
        result = session.run(query, {"id": id})
        return [record.data() for record in result]
    return

@app.get("/api/article/search_by_text")
def get_most_influential_papers_with_text_api(id: str, driver=Depends(get_db_driver)):
    query = """
    MATCH (a:Article)
    WITH a, rand() as r
    WHERE a.title =~ ".*" + $id + ".*" OR a.rebuilt_abstract =~ ".*" + $id + ".*"
    ORDER BY r
    LIMIT 20
    RETURN a, rand() as r
    """
    with driver.session() as session:
        result = session.run(query, {"id": id})
        return [record.data() for record in result]