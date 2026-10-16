"""Module to def tool_ine tools for LLM"""
from pathlib import Path
from langchain.tools import tool
from dotenv import dotenv_values, load_dotenv
from .services import get_researcher_basic_info, get_most_influential_papers_with_text, get_most_influential_papers_with_field, get_most_influential_papers_with_keyword, get_keyword_community, get_keyword_alike, get_paper_basic_info, get_path, get_alike, get_articles_of_author, get_h_index_of

current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent
env_path = project_root / ".env"
config = dotenv_values(env_path)
load_dotenv()


@tool('Basic Researcher Info', description="Accepts who: name of person or _id: id of person. In first case, \
        returns at most 5 people who have this name, their id and institution, \
        in second case return specific person info")
def tool_get_researcher_basic_info(who: str = None, author_id: int = None):
    """Accepts $who: name of person or $id: id of person. In first case, \
        returns at most 5 people who have this name, their id and institution, \
        in second case return specific person info
        """
    try:
        return get_researcher_basic_info(who, author_id)
    except ExceptionGroup as e:
        return {f"{str(e)}": "Impossible to get info (Tool: get_researcher_basic_info)"}

@tool("Get H Index Of Researcher", description="Accepts author _id as a parameter, returns author h index")
def tool_get_h_index_of(author_id: int):
    """Accepts author id as a parameter, returns author h index"""
    try:
        return get_h_index_of(author_id)
    except ExceptionGroup as e:
        return {f"{str(e)}": "Impossible to get info (Tool: h_index)"}


@tool("Get Alike Authors", description="""Accepts author _id as a parameter, returns other authors in his community""")
def tool_get_alike(author_id: int):
    """Accepts author id as a parameter, returns other authors in his community"""
    try:
        return get_alike(author_id)
    except ExceptionGroup as e:
        return {f"{str(e)}": "Impossible to get info (Tool: community/search)"}


@tool("Get Path Between 2 Authors", description="""Accepts author id1 as a parameter, \
    id2 as a target node, returns shortest path between them""")
def tool_get_path(id1: int, id2: int):
    """Accepts author id1 as a parameter, \
    id2 as a target node, returns shortest path between them"""
    try:
        return get_path(id1, id2)
    except ExceptionGroup as e:
        return {f"{str(e)}": "Impossible to get info (Tool: networking)"}


@tool("Get Paper Info", description="""Accepts _id as a paper id, returns basic info""")
def tool_get_paper_basic_info(paper_id: int):
    """Accepts id as a paper id, returns basic info"""
    try:
        return get_paper_basic_info(paper_id)
    except ExceptionGroup as e:
        return {f"{str(e)}": "Impossible to get info (Tool: paper_basic_info)"}


@tool("Get Alike Keywords", description="Takes keyword, returns similar keywords that were mentioning seeking word")
def tool_get_keyword_alike_api(keyword: str):
    """Accepts keyword, returns similar keywords that were mentioning seeking word"""
    try:
        return get_keyword_alike(keyword)
    except ExceptionGroup as e:
        return {f"{str(e)}": "Impossible to get info (Tool: keyword)"}


@tool("Get Articles Of Author", description="""Accepts author_id, returns their most influential works (5)""")
def tool_get_articles_of_author(author_id: int):
    """Accepts author id, returns their most influential works (5)"""
    try:
        return get_articles_of_author(author_id)
    except ExceptionGroup as e:
        return {f"{str(e)}": "Impossible to get info (Tool: influential works)"}


@tool("Get Keywords Community (Semantic)", description="""Accepts specific keyword, returns other keywords from the same community or None if Keyword not in corpus""")
def tool_get_keyword_community(keyword: str):
    """Accepts keyword, returns other keywords from the same community"""
    try:
        return get_keyword_community(keyword)
    except ExceptionGroup as e:
        return {f"{str(e)}": "Impossible to get info (Tool: keyword community)"}


@tool("Get Most Quoted Articles By Mentioning Text", description="""Takes search text as _id parameter, compares article items (title and abstract) \
        with search item and returns 20 random articles that have this search item""")
def tool_get_most_influential_papers_with_text(text: str):
    """Takes search text, compares article items (title and abstract) \
        with search item and returns 20 random articles that have this search item"""
    try:
        return get_most_influential_papers_with_text(text)
    except ExceptionGroup as e:
        return {f"{str(e)}": "Impossible to get info (Tool: tool_get_most_influential_papers_with_text)"}

@tool("Get Most Quoted Articles By Chosen Community", description="If you have community Id for keyword (for example from tool_get_keyword_alike_api), pass its communityId as _id and get most quoted articles within field to which this keyword belongs")
def tool_get_most_influential_papers_with_field(keyword_community_id: int):
    """Takes community id (from api/keyword/get), and find 10 most quoted articles within this \
    community """
    try:
        return get_most_influential_papers_with_field(keyword_community_id)
    except ExceptionGroup as e:
        return {f"{str(e)}": "Impossible to get info (Tool: tool_get_most_influential_papers_with_field )"}

@tool("Get Most Quoted Articles By Chosen Keyword", description="If you have community Id for keyword (for example from tool_get_keyword_alike_api), pass its id as _id and get most quoted articles with this keyword mentioned")
def tool_get_most_influential_papers_with_keyword(keyword: str):
    """Takes arbitrary keyword, and find 30 arbritrary articles with this keyword"""
    try:
        return get_most_influential_papers_with_keyword(keyword)
    except ExceptionGroup as e:
        return {f"{str(e)}": "Impossible to get info (Tool: tool_get_most_influential_papers_with_keyword)"}


