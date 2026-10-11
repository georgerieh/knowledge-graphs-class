# knowledge-graphs-class

Schema:
(:Article) ──[:WRITTEN_BY]──> (:Author)
   │
   └──────[:REFERENCES] -> (:Article)
   └──────[:PUBLISHED_IN] -> (:Venue)
   └──────[:HAS_KEYWORD]──────> (:Keyword)