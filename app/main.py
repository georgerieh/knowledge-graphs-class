"""Module to run the FASTAPI Server"""
import logging
import os
from load import main
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import dotenv_values
from agent.graph import agent_executor, system_prompt_str
from agent.services import get_researcher_basic_info, get_most_influential_papers_with_text, get_most_influential_papers_with_field, get_most_influential_papers_with_keyword, get_keyword_community, get_keyword_alike, get_paper_basic_info, get_path, get_alike, get_articles_of_author, get_h_index_of
from langchain_core.messages import HumanMessage, SystemMessage, message_to_dict
import traceback

from neo4j import GraphDatabase
import langchain
logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.DEBUG)
logging.getLogger("httpcore").setLevel(logging.DEBUG)
langchain.verbose = True
langchain.debug = True
config = dotenv_values(".env")

app = FastAPI()

URI = os.getenv("NEO4J_URI")
AUTH = (config["graphs_username"], config["graphs_pass"])
try:
    driver = GraphDatabase.driver(URI, auth=AUTH)
except Exception as e:
    raise ConnectionError from e


def get_db_driver():
    """
    OOP pattern
    """
    return driver


class Prompt(BaseModel):
    """
    Used in LLM Call"""
    prompt: str
    
class ChatRequest(BaseModel):
  prompt: str

@app.on_event("startup")
async def startup_event():
    """
    This calling is necessary on start"""
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
            f"Graph 'Networking' projected: {record['nodeCount']} nodes, \
                {record['relationshipCount']} relationships."
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
                    """
        )
        l_record = louvain_result.single()
        print(
            f"Louvain completed: {l_record['communityCount']} communities found (Modularity: {\
                l_record['modularity']:.4f})."
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
            f"Graph 'KeywordNetwork' projected: {record['nodeCount']} nodes, {\
                record['relationshipCount']} relationships."
        )
        louvain_result2 = session.run(
            """ \
                CALL gds.louvain.write(
                    'KeywordNetwork',
                    {
                        writeProperty: 'communityId'
                    }
                )
                YIELD communityCount, modularity, ranLevels
                RETURN communityCount, modularity, ranLevels
            """
        )
        l_record = louvain_result2.single()
        print(
            f"Louvain completed: {l_record['communityCount']} communities found (Modularity: {\
                l_record['modularity']:.4f})."
        )


@app.get("/")
async def root():
    """
    Root"""
    return {"message": "Hello World"}

@app.get("/api/researcher/get_info")
def get_researcher_basic_info_api(who: str = None, _id: int = None):
    """
    Takes id of author, and returns his id and his institution (NOT WORKS).
    In case more than 1 person have this name
    """
    return get_researcher_basic_info(who, _id)

@app.get("/api/researcher/h_index")
def get_h_index_of_api(_id: int):
    """
    Takes id of author, and calculates his H-index
    """
    return get_h_index_of(_id)


@app.get("/api/researcher/most_influential")
def get_articles_of_author_api(_id: int):
    """
    Takes id of author, and returns 5 his most quoted works"""
    return get_articles_of_author(_id)


@app.get("/api/community/search")
def get_alike_api(_id: int):
    """
    Takes id of author, and returns 30 other
    researchers in the same community"""
    return get_alike(_id)


@app.get("/api/networking")
def get_path_api(id1: int, id2: int):
    """
    Takes id of researcher 1 and 2 and shows path between them by CO_AUTHORED_WITH relations"""
    return get_path(id1, id2)


@app.get("/api/paper/get_info")
def get_paper_basic_info_api(_id: int = None):
    """
    Takes id of paper, and returns info about this paper"""
    return get_paper_basic_info(_id)


@app.get("/api/keyword/get")
def get_keyword_alike_api(keyword: str):
    """
    Takes arbitrary keyword, and checks if keyword exists (or diff combinations)"""
    return get_keyword_alike(keyword)


@app.get("/api/keyword/search")
def get_keyword_community_api(_id: int):
    """
    Takes arbitrary keyword, and find 30 other \
    keywords that share the same community"""
    return get_keyword_community(_id)


@app.get("/api/article/search_by_keyword")
def get_most_influential_papers_with_keyword_api(_id: str):
    """
    Takes arbitrary keyword, and find 30 arbritrary articles with this keyword"""
    return get_most_influential_papers_with_keyword(_id)


@app.get("/api/article/search_by_field")
def get_most_influential_papers_with_field_api(_id: int):
    """
    Takes community id (from api/keyword/get), and find 10 most quoted articles within this \
    community """
    return get_most_influential_papers_with_field(_id)


@app.get("/api/article/search_by_text")
def get_most_influential_papers_with_text_api(_id: str):
    """
    Takes search text, compares article items (title and abstract) \
    with search item and returns 20 random articles that have this search item
    """
    return get_most_influential_papers_with_text(_id)


# @app.post("/chat")
# async def post_chat(prompt: Prompt):
#     """
#     API to proxy LLM call
#     """
#     try:
#         chat_completion = agent.invoke({
#         "messages": [HumanMessage(content=prompt.prompt)]
#         })

#         messages = [msg.dict() for msg in chat_completion["messages"]]
#         return {"response": messages}
#     except ExceptionGroup as e:
#         raise HTTPException(status_code=500) from e

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
  try:
    initial_state = {
        "messages": [
            SystemMessage(content=system_prompt_str),
            HumanMessage(content=request.prompt),
        ]
    }

    result = await agent_executor.ainvoke(initial_state)

    

    return {"messages": result}

  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e)) from e