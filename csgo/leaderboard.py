from csgo.utils import SQL , validate
from typing import List

@validate
def get_players_by_name(player_name:str) -> List[str]:
    with SQL("csgo.db") as curs:
        curs.execute("""SELECT player_name FROM leaderboard
                                WHERE LOWER(player_name) LIKE (?);""" ,
                                 [f"{player_name.lower()}%"])
        return list(map(lambda x : x[0] , curs.fetchall()))

@validate
def get_players_by_rank(rank : int) -> List[str]:
    with SQL("csgo.db") as curs:
        curs.execute("""SELECT player_name FROM leaderboard
                                WHERE rank <= (?);""" ,
                                 [ rank] )
        return list(map(lambda x : x[0] , curs.fetchall()))
