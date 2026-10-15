# knowledge-graphs-class
## Intro
This project aims to track academic communities, and also networks across researchers, research articles and keywords. There are 4,894,081 papers and 45,564,149 citation relationships, which is extended by graph relations across venues, institutions, articles, researchers and keywords

## Badges

[![linting: pylint](https://img.shields.io/badge/linting-pylint-yellowgreen)](https://github.com/pylint-dev/pylint)


## Schema:
```
(:Article) ──[:WRITTEN_BY]──> (:Author)
   └──────[:REFERENCES] -> (:Article)
   └──────[:PUBLISHED_IN] -> (:Venue)
   └──────[:HAS_KEYWORD]──────> (:Keyword)
 (:Author) ──────[:WORKS_AT]──────> (:Institution)
```

### 2 Projections 
are available

- Networking: (:Author)-[:CO_AUTHORED_WITH]->(:Author)
- KeywordNetwork (:Keyword)-[:SHARED_ARTICLE]->(:Keyword)

## Make commands (for convenience)

```
Commands:
  make venv           Create local virtualenv (.venv)
  make install        Install requirements into .venv
  make run            Run FastAPI (uvicorn) on :8000
  make docker-build   Build Docker image (TAG=graph-api:dev)
  make docker-run     Start the Docker Compose stack
  make test           Run pytest suite
  make lint           Run pylint
  make format         Run black code formatter
  make clean          Remove caches and temp files
  make tree           Show project tree (depth 3)
```

## Project structure

```
├── app
│   ├── agent
│   │   ├── graph.py
│   │   └── tools.py
│   ├── demo.ipynb
│   ├── load.py
│   └── main.py
├── csv-conversion-all-fields.ipynb
├── docker-compose.yml
├── dockerfile
├── docs
├── makefile
├── neo4j
│   ├── data
│   │   ├── databases
│   │   ├── dbms
│   │   ├── server_id
│   │   └── transactions
│   └── import
├── output.csv
├── pyproject.toml
├── README.md
└── uv.lock
```

## Available API endpoints
![API](docs/API_Definition.png)

## Dataset provenance
Taken from: https://www.kaggle.com/datasets/mathurinache/citation-network-dataset under CC BY-NC-SA 4.0


Sources
https://www.aminer.org/citation

Collection Methodology
The data set is designed for research purpose only. The citation data is extracted from DBLP, ACM, MAG (Microsoft Academic Graph), and other sources. The first version contains 629,814 papers and 632,752 citations. Each paper is associated with abstract, authors, year, venue, and title. The data set can be used for clustering with network and side information, studying influence in the citation network, finding the most influential papers, topic modeling analysis, etc.

## How to start

```
docker compose up
```
then navigate to [demo](app/demo.ipynb)