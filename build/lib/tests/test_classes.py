def test_player_class():
    stats = {
            "player_id" : 123213213,
            "player_name": "Hello",
            "primary_weapon":"2323",
            "secondary_weapon":"342352",
            "kd":"213123",
            "hs":"45%",
            "win_rate":"100%",
            "rating":5.4
     }
    player = Player(**stats)
    assert isinstance(player.get_stats() , dict)
