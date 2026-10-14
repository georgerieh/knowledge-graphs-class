from pathlib import Path
import requests
from langchain.tools import tool
from dotenv import dotenv_values, load_dotenv

current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent
env_path = project_root / ".env"
config = dotenv_values(env_path)
load_dotenv()

@tool
def get_researcher_basic_info(who: str = None, id: int = None):
    """Accepts $who: name of person or $id: id of person. In first case, \
        returns at most 5 people who have this name, their id and institution, \
        in second case return specific person info
        
        Args:
            who: name of the researcher
            id: Id of the researcher in database
        """
    url_ = "http://localhost:8000/api/researcher/get_info"
    params = {"who": who, "id": id}
    response = requests.get(url_, params=params, timeout=120)
    if response.status_code == 200:
        return response.json()
    return {"error": "Impossible to get info (Tool: get_researcher_basic_info)"}


@tool
def get_researcher_works_info(id: int):
    """Accepts author id as a parameter, \
        returns author works in decreasing order of quoting number"""
    url_ = "http://localhost:8000/api/researcher/get_works_info"
    params = {"id": id}
    response = requests.get(url_, params=params, timeout=120)
    if response.status_code == 200:
        return response.json()
    return {"error": "Impossible to get info (Tool: get_works_info)"}


@tool
def get_h_index_of(id: int):
    """Accepts author id as a parameter, returns author h index"""
    url_ = "http://localhost:8000/api/researcher/h_index"
    params = {"id": id}
    response = requests.get(url_, params=params, timeout=120)
    if response.status_code == 200:
        return response.json()
    return {"error": "Impossible to get info (Tool: h_index)"}


@tool
def get_alike(id: int):
    """Accepts author id as a parameter, returns other authors in his community"""
    url_ = "http://localhost:8000/api/community/search"
    params = {"id": id}
    response = requests.get(url_, params=params, timeout=120)
    if response.status_code == 200:
        return response.json()
    return {"error": "Impossible to get info (Tool: community/search)"}


@tool
def get_path(id1: int, id2: int):
    """Accepts author id1 as a parameter, \
    id2 as a target node, returns shortest path between them"""
    url_ = "http://localhost:8000/api/networking"
    params = {"id1": id1, "id2": id2}
    response = requests.get(url_, params=params, timeout=120)
    if response.status_code == 200:
        return response.json()
    return {"error": "Impossible to get info (Tool: networking)"}


@tool
def get_paper_basic_info(id: int):
    """Accepts id as a paper id, returns basic info"""
    url_ = "http://localhost:8000/api/paper/get_info"
    params = {"id": id}
    response = requests.get(url_, params=params, timeout=120)
    if response.status_code == 200:
        return response.json()
    return {"error": "Impossible to get info (Tool: paper_basic_info)"}


@tool
def get_keyword_alike_api(keyword: str):
    """Accepts keyword, returns similar keywords that were mentioning seeking word"""
    url_ = "http://localhost:8000/api/keyword/get"
    params = {"id": keyword}
    response = requests.get(url_, params=params, timeout=120)
    if response.status_code == 200:
        return response.json()
    return {"error": "Impossible to get info (Tool: keyword)"}


@tool
def get_articles_of_author(id: int):
    """Accepts author id, returns their most influential works (5)"""
    url_ = "http://localhost:8000/api/researcher/most_influential"
    params = {"id": id}
    response = requests.get(url_, params=params, timeout=120)
    if response.status_code == 200:
        return response.json()
    return {"error": "Impossible to get info (Tool: influential works)"}

@tool
def get_keyword_community(keyword: str):
    """Accepts keyword, returns other keywords from the same community"""
    url_ = "http://localhost:8000/api/keyword/search"
    params = {keyword}
    response = requests.get(url_, params=params, timeout=120)
    if response.status_code == 200:
        return response.json()
    return {"error": "Impossible to get info (Tool: keyword community)"}
