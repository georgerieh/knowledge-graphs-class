"""Module to def tool_ine tools for LLM"""

import re
from pathlib import Path
from langchain.tools import tool
from dotenv import dotenv_values, load_dotenv
from .services import (
    get_researcher_basic_info,
    get_most_influential_papers_with_text,
    get_most_influential_papers_with_field,
    get_most_influential_papers_with_keyword,
    get_keyword_community,
    get_keyword_alike,
    get_paper_basic_info,
    get_path,
    get_alike,
    get_articles_of_author,
    get_h_index_of,
    execute_query,
    get_schema_validator,
    get_syntax_validator,
)

current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent
env_path = project_root / ".env"
config = dotenv_values(env_path)
load_dotenv()

FORBIDDEN_KEYWORDS = ["DELETE", "DETACH", "REMOVE", "SET", "CREATE", "MERGE", "DROP"]
MUST_KEYWORDS = ["LIMIT"]


@tool(
    "Basic Researcher Info",
    description="Accepts who: name of person or _id: id of person. In first case, \
        returns at most 5 people who have this name, their id and institution, \
        in second case return specific person info",
)
def tool_get_researcher_basic_info(who: str = None, author_id: int = None):
    """Accepts $who: name of person or $id: id of person. In first case, \
        returns at most 5 people who have this name, their id and institution, \
        in second case return specific person info
        """
    try:
        response = get_researcher_basic_info(who, author_id)
        if not response:
            return {"status": "not_found", "data": [], "message": "No researcher found in db."}
        return {"status": "success", "data": response, "message": "Found researcher info in database."}
    except ExceptionGroup as e:
        return {f"{str(e)}": "Impossible to get info (Tool: get_researcher_basic_info)"}


@tool("Get H Index Of Researcher", description="Accepts author _id as a parameter, returns author h index")
def tool_get_h_index_of(author_id: int):
    """Accepts author id as a parameter, returns author h index"""
    try:
        response = get_h_index_of(author_id)
        if not response:
            return {"status": "not_found", "data": [], "message": "No researcher found in db."}
        return {"status": "success", "data": response, "message": "Found researcher, and his H index is returned."}
    except ExceptionGroup as e:
        return {f"{str(e)}": "Impossible to get info (Tool: h_index)"}


@tool("Get Alike Authors", description="""Accepts author _id as a parameter, returns other authors in his community""")
def tool_get_alike(author_id: int):
    """Accepts author id as a parameter, returns other authors in his community"""
    try:
        response = get_alike(author_id)
        if not response:
            return {"status": "not_found", "data": [], "message": "No researcher found in database."}
        return {
            "status": "success",
            "data": response,
            "message": "Found researcher and list of researches in his community is provided.",
        }
    except ExceptionGroup as e:
        return {f"{str(e)}": "Impossible to get info (Tool: community/search)"}


@tool(
    "Get Path Between 2 Authors",
    description="""Accepts author id1 as a parameter, \
    id2 as a target node, returns shortest path between them""",
)
def tool_get_path(id1: int, id2: int):
    """Accepts author id1 as a parameter, \
    id2 as a target node, returns shortest path between them"""
    try:
        response = get_path(id1, id2)
        if not response:
            return {"status": "not_found", "data": [], "message": "No path between 2 researches'."}
        return {"status": "success", "data": response, "message": "Found path."}
    except ExceptionGroup as e:
        return {f"{str(e)}": "Impossible to get info (Tool: networking)"}


@tool("Get Paper Info", description="""Accepts _id as a paper id, returns basic info""")
def tool_get_paper_basic_info(paper_id: int):
    """Accepts id as a paper id, returns basic info"""
    try:
        response = get_paper_basic_info(paper_id)
        if not response:
            return {"status": "not_found", "data": [], "message": f"No articles for {paper_id}'."}
        return {"status": "success", "data": response, "message": "Found article in database."}
    except ExceptionGroup as e:
        return {f"{str(e)}": "Impossible to get info (Tool: paper_basic_info)"}


@tool("Get Articles Of Author", description="""Accepts author_id, returns their most influential works (5)""")
def tool_get_articles_of_author(author_id: int):
    """Accepts author id, returns their most influential works (5)"""
    try:
        response = get_articles_of_author(author_id)
        if not response:
            return {"status": "not_found", "data": [], "message": f"No articles for {author_id}'."}
        return {"status": "success", "data": response, "message": "Found articles in database."}
    except ExceptionGroup as e:
        return {f"{str(e)}": "Impossible to get info (Tool: influential works)"}


@tool(
    "Get Keyword Info with Text",
    description="""Accepts specific word or text, returns keywords that contain this word or None if Keyword not in corpus""",
)
def tool_get_keyword_alike(keyword: str):
    """Accepts keyword, returns other keywords that sound alike"""
    try:
        response = get_keyword_alike(keyword)
        if not response:
            return {
                "status": "not_found",
                "data": [],
                "message": f"No keyword look alikes found for '{keyword}'. Try checking for typos or use a broader term.",
            }
        return {"status": "success", "data": response, "message": "Found look alikes."}
    except ExceptionGroup as e:
        return {f"{str(e)}": "Impossible to get info (Tool: keyword alike)"}


@tool(
    "Get Keywords Community by communityId",
    description="""Accepts specific keyword community id, returns other keywords from the same community or None if Keyword not in corpus""",
)
def tool_get_keyword_community(id_: int):
    """Accepts keyword community id, returns other keywords from the same community"""
    try:
        response = get_keyword_community(id_)
        if not response:
            return {"status": "not_found", "data": [], "message": "No keyword is found with this id."}
        return {"status": "success", "data": response, "message": "Found keyword community example."}
    except ExceptionGroup as e:
        return {f"{str(e)}": "Impossible to get info (Tool: keyword community)"}


@tool(
    "Get Most Quoted Articles By Mentioning Text",
    description="""Takes search text as _id parameter, compares article items (title and abstract) \
        with search item and returns 20 random articles that have this search item""",
)
def tool_get_most_influential_papers_with_text(text: str):
    """Takes search text, compares article items (title and abstract) \
        with search item and returns 20 random articles that have this search item"""
    try:
        response = get_most_influential_papers_with_text(text)
        if not response:
            return {"status": "not_found", "data": [], "message": "No articles found with text in db'."}
        return {"status": "success", "data": response, "message": "Found article in database with this text."}
    except ExceptionGroup as e:
        return {f"{str(e)}": "Impossible to get info (Tool: tool_get_most_influential_papers_with_text)"}


@tool(
    "Get Most Quoted Articles By Chosen Community",
    description="If you have community Id for keyword (for example from tool_get_keyword_alike_api), pass its communityId as _id and get most quoted articles within field to which this keyword belongs",
)
def tool_get_most_influential_papers_with_field(keyword_community_id: int):
    """Takes community id (from api/keyword/get), and find 10 most quoted articles within this \
    community """
    try:
        response = get_most_influential_papers_with_field(keyword_community_id)
        if not response:
            return {"status": "not_found", "data": [], "message": f"No articles found with this community id."}
        return {
            "status": "success",
            "data": response,
            "message": "Found article in database with this keyword community id.",
        }
    except ExceptionGroup as e:
        return {f"{str(e)}": "Impossible to get info (Tool: tool_get_most_influential_papers_with_field )"}


@tool(
    "Get Most Quoted Articles By Chosen Keyword",
    description="If you have community Id for keyword (for example from tool_get_keyword_alike_api), pass its id as _id and get most quoted articles with this keyword mentioned",
)
def tool_get_most_influential_papers_with_keyword(keyword: str):
    """Takes arbitrary keyword, and find 30 arbritrary articles with this keyword"""
    try:
        response = get_most_influential_papers_with_keyword(keyword)
        if not response:
            return {"status": "not_found", "data": [], "message": "No articles found with this keyword mentioned'."}
        return {"status": "success", "data": response, "message": "Found article in database."}
    except ExceptionGroup as e:
        return {f"{str(e)}": "Impossible to get info (Tool: tool_get_most_influential_papers_with_keyword)"}


@tool("Query Neo4j and get results")
def tool_execute_query(query: str):
    """
    Takes query and get results. Use with caution
    """
    is_valid_syntax, syntax_metadata = get_syntax_validator().validate(query, database_name="shop")
    schema_score, schema_metadata = get_schema_validator().validate(query=query, database_name="shop")
    query_upper = query.upper()
    list_keywords_banned = []
    list_keywords_must = []
    for keyword in FORBIDDEN_KEYWORDS:
        if re.search(r"\b" + keyword + r"\b", query_upper):
            list_keywords_banned.append(keyword)
    for keyword in MUST_KEYWORDS:
        if keyword.upper() not in query_upper:
            list_keywords_must.append(keyword)
    try:
        if is_valid_syntax and schema_score > 0.5 and len(list_keywords_banned) == 0 and len(list_keywords_must) == 0:
            response = execute_query(query)
            if not response:
                return {"status": "not_found", "data": [], "message": "Nothing found for this query."}
            return {"status": "success", "data": response, "message": "Found results in database."}
        else:
            response = f"Schema metadata report: {schema_metadata}, syntax metadata report: {syntax_metadata}. Banned statements check - not allowed: {list_keywords_banned}. Missing keywords check - include them: {list_keywords_must} Please adjust"
        return {"status": "error", "data": response, "message": "Validator alarm."}
    except ExceptionGroup as e:
        return {f"{str(e)}": "Impossible to get info (Tool: execute_query)"}
