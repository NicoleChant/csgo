from csgo.chameleon import *
from csgo.leaderboard import *

def test_player_class():
    stats = {
            "player_id" : "123213213",
            "rank":"#124 ",
            "player_name": "Hello",
            "primary_weapon":"g23@32",
            "secondary_weapon":"glob231@!!$#1",
            "kills":" 233 ",
            "deaths": " 223  ",
            "hs":"45%",
            "win_rate":"84.5%",
            "onevx":"23",
            "rating":"5.4"
     }
    player = Player(**stats)
    assert len(attr.asdict(player)) == 11
    assert isinstance(player.rating,float) == True
    assert isinstance(player.deaths,int) == True
    assert isinstance(player.kills,int) == True
    assert isinstance(player.hs,float) == True
    assert isinstance(player.onevx,int) == True
    assert isinstance(player.rating,float) == True
    assert isinstance(player.win_rate,float) == True
    assert isinstance(player.rank , int) == True

def test_database():
    assert len(get_players_by_name("r")) > 10
    assert len(get_players_by_rank(5)) == 5
