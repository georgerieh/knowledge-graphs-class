# knowledge-graphs-class

Schema:
```
(:Article) ──[:WRITTEN_BY]──> (:Author) ──────[:WORKS_AT]──────> (:Institution)
   │
   └──────[:REFERENCES] -> (:Article)
   └──────[:PUBLISHED_IN] -> (:Venue)
   └──────[:HAS_KEYWORD]──────> (:Keyword)
   └──────[:WORKS_AT]──────> (:Institution)
```

Project schema
```
project-name/
├── docker-compose.yml
├── .env.example
├── README.md
├── Makefile
├── app/
│   ├── main.py
│   ├── models/
│   ├── routers/
│   ├── services/
│   ├── agent/
│   │   ├── graph.py
│   │   ├── tools.py
│   │   └── guardrails.py
│   └── database/
├── tests/
├── scripts/
│   └── seed_data.py
├── demo.ipynb
└── requirements.txt
```