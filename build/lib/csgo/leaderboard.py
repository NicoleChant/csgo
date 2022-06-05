from csgo.utils import SQL , validate

@validate
def get_players(player_name:str):
    with SQL("csgo.db") as curs:
        curs.execute("""SELECT player_name FROM leaderboard
                                WHERE LOWER(player_name) LIKE (?);""" ,
                                 [f"{player_name.lower()}%"])
        players = list(map(lambda x : x[0] , curs.fetchall()))
        return players
