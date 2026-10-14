import ast
import gc
import pandas as pd
from dotenv import dotenv_values
from neo4j import GraphDatabase
from tqdm_loggable.auto import tqdm
import numpy as np
import sys
import math
import logging

config = dotenv_values(".env")
logging.basicConfig(level=logging.INFO)


def clean_val(val):
    if isinstance(val, float) and math.isnan(val):
        return None
    return val


def run_query(driver, query, parameters=None):
    with driver.session() as session:
        result = session.run(query, parameters)
        return [r.data() for r in result]


def main(driver):
    chunk_size = 5000
    i = 0

    def create_constraints():
        run_query(driver, "CREATE CONSTRAINT IF NOT EXISTS FOR (u:Author) REQUIRE u.id IS UNIQUE;")
        run_query(driver, "CREATE CONSTRAINT IF NOT EXISTS FOR (t:Article) REQUIRE t.id IS UNIQUE;")
        run_query(driver, "CREATE CONSTRAINT IF NOT EXISTS FOR (v:Venue) REQUIRE v.id IS UNIQUE;")
        run_query(driver, "CREATE CONSTRAINT IF NOT EXISTS FOR (k:Keyword) REQUIRE k.id IS UNIQUE;")
        run_query(driver, "CREATE CONSTRAINT IF NOT EXISTS FOR (i:Institution) REQUIRE i.id IS UNIQUE;")

    def load_data_venue(csv_data):
        # Drop rows where VenueId is missing/NaN/None
        csv_data = csv_data.dropna(subset=["VenueId"])
        csv_data = csv_data[csv_data["VenueId"].astype(str).str.lower() != "nan"]

        records = csv_data.to_dict(orient="records")
        if not records:
            return
        query = """
        UNWIND $rows AS row
        MERGE (u:Venue {id: row.VenueId})
        ON CREATE SET u.name = row.VenueRaw
        """
        run_query(driver, query, {"rows": records})

    def load_data_keyword(csv_data):
        csv_data = csv_data.dropna(subset=["keyword"])
        records = csv_data.to_dict(orient="records")
        if not records:
            return
        query = """
        UNWIND $rows AS row
        MERGE (u:Keyword {id: row.keyword})
        ON CREATE SET u.name = row.keyword
        """
        run_query(driver, query, {"rows": records})

    def load_data_institution(csv_data):
        csv_data = csv_data.dropna(subset=["AuthorInstitution"])
        records = csv_data.to_dict(orient="records")
        if not records:
            return
        query = """
        UNWIND $rows AS row
        MERGE (u:Institution {id: row.AuthorInstitution})
        ON CREATE SET u.name = row.AuthorInstitution
        """
        run_query(driver, query, {"rows": records})

    def load_data_author(csv_data):
        csv_data = csv_data.dropna(subset=["AuthorId"])
        csv_data = csv_data[csv_data["AuthorId"].astype(str).str.lower() != "nan"]

        records = csv_data.to_dict(orient="records")
        if not records:
            return
        query = """
        UNWIND $rows AS row
        MERGE (u:Author {id: row.AuthorId})
        ON CREATE SET u.name = row.AuthorName,
            u.Institution = row.AuthorInstitution
        WITH u, row
            MATCH (i:Institution {id: row.AuthorInstitution})
            MERGE (u)-[:WORKS_AT]->(i)
        """
        run_query(driver, query, {"rows": records})

    def load_data_articles(article_records):
        valid_records = []
        for r in article_records:
            art_id = r.get("ArticleId")
            if (
                art_id is not None
                and not (isinstance(art_id, float) and math.isnan(art_id))
                and str(art_id).lower() != "nan"
            ):
                cleaned_r = {k: clean_val(v) for k, v in r.items()}
                valid_records.append(cleaned_r)

        if not valid_records:
            return

        query = """
        UNWIND $rows AS row
        MERGE (a:Article {id: row.ArticleId})
        ON CREATE SET a.title = row.Title,
                    a.year = row.year,
                    a.doi = row.doi,
                    a.publisher = row.publisher,
                    a.rebuilt_abstract = row.rebuilt_abstract,
                    a.authorids = row.AuthorIds
        
        WITH a, row
        UNWIND CASE WHEN size(row.AuthorIds) = 0 THEN [null] ELSE row.AuthorIds END AS authorId
        OPTIONAL MATCH (auth:Author {id: authorId})
        FOREACH (_ IN CASE WHEN auth IS NOT NULL THEN [1] ELSE [] END |
            MERGE (a)-[:WRITTEN_BY]->(auth)
        )
        
        WITH a, row
        OPTIONAL MATCH (ven:Venue {id: row.VenueId})
        FOREACH (_ IN CASE WHEN ven IS NOT NULL AND row.VenueId IS NOT NULL THEN [1] ELSE [] END |
            MERGE (a)-[:PUBLISHED_IN]->(ven)
        )
        
        WITH a, row
        UNWIND CASE WHEN size(row.Keywords) = 0 THEN [null] ELSE row.Keywords END AS kw
        OPTIONAL MATCH (k:Keyword {id: kw})
        FOREACH (_ IN CASE WHEN k IS NOT NULL THEN [1] ELSE [] END |
            MERGE (a)-[:HAS_KEYWORD]->(k)
        )
        
        WITH a, row
        UNWIND CASE WHEN size(row.ReferenceIds) = 0 THEN [null] ELSE row.ReferenceIds END AS refId
        FOREACH (_ IN CASE WHEN refId IS NOT NULL THEN [1] ELSE [] END |
            MERGE (ref:Article {id: refId})
            MERGE (a)-[:REFERENCES]->(ref)
        )
        """
        run_query(driver, query, {"rows": valid_records})

    create_constraints()

    for chunk in pd.read_csv("output.csv", chunksize=chunk_size):
        chunk = chunk.replace({np.nan: None})
        chunk = chunk.fillna(np.nan).replace([np.nan], [None])
        if i > 20 and config["env"] != "prod":
            pass
        else:
            if "author_list" in chunk.columns:
                author_data = []
                author_institution = []
                for val in chunk["author_list"].dropna():
                    try:
                        parsed = ast.literal_eval(val)
                        for a in parsed:
                            if len(a) >= 3 and a[1] is not None:
                                author_data.append((a[0], a[1], a[2]))
                                author_institution.append(a[2])
                    except Exception:
                        continue
                if author_institution:
                    df_authors = pd.DataFrame(author_institution, columns=["AuthorInstitution"]).drop_duplicates(
                        subset=["AuthorInstitution"]
                    )
                    load_data_institution(df_authors)
                if author_data:
                    df_authors = pd.DataFrame(
                        author_data, columns=["AuthorName", "AuthorId", "AuthorInstitution"]
                    ).drop_duplicates(subset=["AuthorId"])
                    load_data_author(df_authors)
                    del df_authors

            if "venue_list" in chunk.columns:
                venue_data = []
                for val in chunk["venue_list"].dropna():
                    try:
                        v = ast.literal_eval(val)
                        if v and len(v) >= 2 and v[0] is not None:
                            venue_data.append((v[0], v[1]))
                    except Exception:
                        continue
                if venue_data:
                    df_venues = pd.DataFrame(venue_data, columns=["VenueId", "VenueRaw"]).drop_duplicates(
                        subset=["VenueId"]
                    )
                    load_data_venue(df_venues)
                    del df_venues

            if "keyword" in chunk.columns:
                keywords_list = []
                for val in chunk["keyword"].dropna():
                    for k in str(val).split(";"):
                        if k.strip():
                            keywords_list.append(k.strip())
                if keywords_list:
                    df_keywords = pd.Series(keywords_list).drop_duplicates().to_frame(name="keyword")
                    load_data_keyword(df_keywords)
                    del df_keywords

            article_records = []
            for _, row in chunk.iterrows():
                try:
                    author_ids = (
                        [a[1] for a in ast.literal_eval(row["author_list"]) if len(a) > 1 and a[1] is not None]
                        if pd.notna(row.get("author_list"))
                        else []
                    )
                except Exception:
                    author_ids = []

                try:
                    v_parsed = ast.literal_eval(row["venue_list"]) if pd.notna(row.get("venue_list")) else None
                    venue_ids = v_parsed[0] if v_parsed and len(v_parsed) > 0 else None
                except Exception:
                    venue_ids = None

                keywords = (
                    [k.strip() for k in str(row["keyword"]).split(";") if k.strip()]
                    if pd.notna(row.get("keyword"))
                    else []
                )
                references = (
                    [r.strip() for r in str(row["references"]).split(";") if r.strip()]
                    if pd.notna(row.get("references"))
                    else []
                )

                article_records.append(
                    {
                        "ArticleId": row.get("id"),
                        "Title": row.get("title"),
                        "AuthorIds": author_ids,
                        "VenueId": venue_ids,
                        "Keywords": keywords,
                        "ReferenceIds": references,
                        "year": row.get("year"),
                        "doi": row.get("doi"),
                        "publisher": row.get("publisher"),
                        "rebuilt_abstract": row.get("rebuilt_abstract"),
                    }
                )

            if article_records:
                load_data_articles(article_records)
                del article_records

            gc.collect()
            if i % 10 == 0:
                print(f"{i}th chunk has been processed", flush=True)
        i += 1

    # run_query(
    #     driver,
    #     """
    #         MATCH (auth1:Author)<-[:WRITTEN_BY]-(a:Article)-[:WRITTEN_BY]->(auth2:Author)
    #         WHERE auth1 <> auth2
    #         MERGE (auth1)-[:CO_AUTHORED_WITH]-(auth2)
    #         """,
    # )

    print("All data successfully processed")
