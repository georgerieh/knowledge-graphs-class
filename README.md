# knowledge-graphs-class

## Schema:
```
(:Article) ──[:WRITTEN_BY]──> (:Author)
   └──────[:REFERENCES] -> (:Article)
   └──────[:PUBLISHED_IN] -> (:Venue)
   └──────[:HAS_KEYWORD]──────> (:Keyword)
 (:Author) ──────[:WORKS_AT]──────> (:Institution)
   └──────[:CO_AUTHORED_WITH] -> (:Author)
```

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