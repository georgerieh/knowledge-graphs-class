from fastapi import FastAPI
from neo4j import GraphDatabase
from dotenv import dotenv_values
from load import main

config = dotenv_values(".env")

app = FastAPI()

URI = config['url']
AUTH = (config['graphs_username'], config['graphs_pass'])


@app.on_event("startup")
async def startup_event():
    with GraphDatabase.driver(URI, auth=AUTH) as driver:
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
        
@app.get("/")
async def root():
    #TODO: Add main page
    return {"message": "Hello World"}
# 
# @app.post('')
# #TODO: function to call database based on api

# # # GET /api/routes/shortest?from={iata_a}&to={iata_b
# # @app.get("/api/routes/shortest")
# # async def get_shortest_from_to(from_location: str = Query(..., alias="from"), to: str = ""):
# #     path = []
# #     #TODO: call database, populate list
# #     return 404

# # # Most central airports
# # # GET /api/airports/central?metric=degree
# # @app.get("/api/airports/central")
# # async def get_airports_by_metric(metric: str):
# #     #TODO: call database, populate list
# #     return 404


# # # Connected components by continent
# # # GET /api/network/components?continent={c}
# # @app.get("/api/network/components")
# # async def get_components_by_continent(continent: str):
# #     #TODO: call database, populate list
# #     return 404


# # # Reachability within k hops
# # # GET /api/airports/{iata}/reachable?hops={k}
# # @app.get("/api/airports/{iata}/reachable/hops")
# # async def reachable_hops_from(iata, hops: str):
# #     #TODO: call database, populate list
# #     return 404