from fastapi import FastAPI, Query
from neo4j import GraphDatabase
from dotenv import dotenv_values
config = dotenv_values(".env")

app = FastAPI()

URI = "neo4j+s://5898a234.databases.neo4j.io"
AUTH = (config['graphs-username'], config['graphs-pass'])


@app.on_event("startup")
async def startup_event():
    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        driver.verify_connectivity()
        print("Connection established.")
        
@app.get("/")
async def root():
    #TODO: Add main page
    return {"message": "Hello World"}

#TODO: function to call database based on api

# GET /api/routes/shortest?from={iata_a}&to={iata_b
@app.get("/api/routes/shortest")
async def get_shortest_from_to(from_location: str = Query(..., alias="from"), to: str = ""):
    path = []
    #TODO: call database, populate list
    return 404

# Most central airports
# GET /api/airports/central?metric=degree
@app.get("/api/airports/central")
async def get_airports_by_metric(metric: str):
    #TODO: call database, populate list
    return 404


# Connected components by continent
# GET /api/network/components?continent={c}
@app.get("/api/network/components")
async def get_components_by_continent(continent: str):
    #TODO: call database, populate list
    return 404


# Reachability within k hops
# GET /api/airports/{iata}/reachable?hops={k}
@app.get("/api/airports/{iata}/reachable/hops")
async def reachable_hops_from(iata, hops: str):
    #TODO: call database, populate list
    return 404