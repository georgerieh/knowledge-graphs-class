from dotenv import dotenv_values
from neo4j import GraphDatabase
import pandas as pd
import ast

config = dotenv_values(".env") 

url = config['url']
username = config['graphs-user']
password = config['graps-pass']


driver = GraphDatabase.driver(url, auth=(username, password))


entities_map = {
    "author": {
        "entity_name": "Author",
        "relationship_type": "WRITTEN_BY"
    },
    "venue": {
        "entity_name": "Venue",
        "relationship_type": "PUBLISHED_IN"
    },
    "keyword": {
        "entity_name": "Keyword",
        "relationship_type": "HAS_KEYWORD"
    },
    "article": {
        "entity_name": "Article",
        "relationship_type": "REFERENCES"
    }
}

def run_query(query, parameters=None):
    with driver.session() as session:
        result = session.run(query, parameters)
        return [r.data() for r in result]
    
def create_constraints():
    run_query("CREATE CONSTRAINT IF NOT EXISTS FOR (u:Author) REQUIRE u.id IS UNIQUE;")
    run_query("CREATE CONSTRAINT IF NOT EXISTS FOR (t:Article) REQUIRE t.id IS UNIQUE;")
    run_query("CREATE CONSTRAINT IF NOT EXISTS FOR (v:Venue) REQUIRE v.id IS UNIQUE;")
    run_query("CREATE CONSTRAINT IF NOT EXISTS FOR (k:Keyword) REQUIRE k.id IS UNIQUE;")
        
def load_data_venue(csv_data):
    records = csv_data.to_dict(orient="records")
    query = '''
    UNWIND $rows AS row
    MERGE (u:Venue {id:row.VenueId})
    ON CREATE SET u.name = row.VenueRaw
    '''
    run_query(query, {"rows": records})
def load_data_keyword(csv_data):
    records = csv_data.to_dict(orient="records")
    query = '''
    UNWIND $rows AS row
    MERGE (u:Keyword {id:row.keyword})
    '''
    run_query(query, {"rows": records})    
def load_data_author(csv_data):
    records = csv_data.to_dict(orient="records")
    query = '''
    UNWIND $rows AS row
    MERGE (u:Author {id:row.AuthorId})
    ON CREATE SET u.name = row.AuthorName,
        SET u.Institution = row.AuthorInsititution
    '''
    run_query(query, {"rows": records}) 
def load_data_articles(csv_data):
    query = '''
    UNWIND $rows AS row
    MERGE (a:Article {id: row.ArticleId})
    ON CREATE SET a.title = row.title,
                a.year = row.year,
                a.doi = row.doi,
                a.publisher = row.publisher,
                a.rebuilt_abstract = row.rebuilt_abstract
    
    FOREACH (authorId IN row.AuthorIds |
        MATCH (auth:Author {id: authorId})
        MERGE (a)-[:WRITTEN_BY]->(auth)
    )
    
    FOREACH (venueId IN row.VenueIds |
        MATCH (ven:Venue {id: venueId})
        MERGE (a)-[:PUBLISHED_IN]->(ven)
    )
    
    FOREACH (kw IN row.Keywords |
        MATCH (k:Keyword {id: kw})
        MERGE (a)-[:HAS_KEYWORD]->(k)
    )
    
    FOREACH (refId IN row.ReferenceIds |
        MERGE (ref:Article {id: refId})
        MERGE (a)-[:REFERENCES]->(ref)
    )
    '''
    run_query(query, {"rows": csv_data})


df = pd.read_csv('output.csv')
print('Input file has been identified')
df_subset_author = df['author_list'].apply(ast.literal_eval).explode().drop_duplicates()
df_subset_author['AuthorName'] = df_subset_author.apply(lambda x: x[0])
df_subset_author['AuthorId'] = df_subset_author.apply(lambda x: x[1])
df_subset_author['AuthorInsititution'] = df_subset_author.apply(lambda x: x[2])
load_data_author(df_subset_author)
print('Loaded author nodes')
df_subset_Venue = df['venue_list'].apply(ast.literal_eval).explode().drop_duplicates()
df_subset_Venue['VenueId'] = df_subset_Venue.apply(lambda x: x[0])
df_subset_Venue['VenueRaw'] = df_subset_Venue.apply(lambda x: x[1])
load_data_venue(df_subset_Venue)
print('Loaded venues nodes')
df_subset_keyword = df['keyword'].str.split(';').explode().drop_duplicates()
load_data_keyword(df_subset_keyword)
print('Loaded keywords nodes')
print('Processing and loading Article nodes and relationships...')
article_records = []

for _, row in df.iterrows():
    author_ids = []
    if pd.notna(row.get('author_list')):
        for a in ast.literal_eval(row['author_list']):
            author_ids.append(a[1])
            
    venue_ids = []
    if pd.notna(row.get('venue_list')):
        for v in ast.literal_eval(row['venue_list']):
            venue_ids.append(v[0])
            
    keywords = []
    if pd.notna(row.get('keyword')):
        keywords = [k.strip() for k in str(row['keyword']).split(';') if k.strip()]
        
    references = []
    if pd.notna(row.get('references')):
        references = [r.strip() for r in str(row['references']).split(';') if r.strip()]

    article_records.append({
        "ArticleId": row.get('id'),         
        "Title": row.get('title'),           
        "AuthorIds": author_ids,
        "VenueIds": venue_ids,
        "Keywords": keywords,
        "ReferenceIds": references,
        "year": row.get('year'),
        "doi": row.get('doi'),
        "publishher": row.get('publishher'),
        "rebuilt_abstract": row.get('rebuilt_abstract')
        
        
    })

load_data_articles(article_records)
print(f'Loaded {len(article_records)} article nodes with all relationships.')
