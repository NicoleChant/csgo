from fastapi import FastAPI
from csgo.leaderboard import *
from typing import Union

app = FastAPI()


@app.get('/')
async def greet():
    return {"Prologue": "Welcome to CSGO prediction api!"}

@app.get('/author')
async def get_author():
    return {"Author" : "Nicole Chan"}



@app.get('/name/{player_name}')
async def get_data(player_name: str , limit : Union[int , None] = None):
    if limit:
        return {"players": get_players_by_name(player_name)[:limit] }
    return {"players": get_players_by_name(player_name)}


@app.get('/rank/{rank}')
async def get_player_by_rank(rank : int , limit : Union[int , None] = None):
    if limit:
        return {"players": get_players_by_rank(rank)[:limit] }
    return {"players": get_players_by_rank(rank)}
