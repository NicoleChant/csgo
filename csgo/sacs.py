from parsers import *
from utils import *
from chameleon import *
import argparse
from itertools import count
from bs4 import BeautifulSoup
from time import sleep
import sys


def observe_leaderboards():
    chameleon = ChameleonFactory().get("leaderboard")
    page = count()
    next(page)

    while True:
        cur_page = next(page)
        print(colored(f"Retrieving page {cur_page}..." , "blue"))
        sleep(0.5)
        chameleon.observe(page = cur_page)

        if not chameleon.soup.find('a' , {'href' :True , 'rel' : 'next'}):
            break

        if cur_page > PlayersChameleon.max_iter:
            break

        for player_data in chameleon.parse():
            Player( **player_data )
        print(colored(f"Finished page {cur_page}." , "blue"))


def observe_matches():
    chameleon = ChameleonFactory().get("match_overall")
    chameleon.observe()
    for match_data in chameleon.parse():
        try:
            Match( **match_data )
        except ValueError as e:
            print(e)
            print("This match is ignored and won't be added to the database. Continuing to the next match.")
            continue


@validate
def get_match_ids() -> list[int]:
    with SQL('csgo.db') as curs:
        curs.execute("SELECT match_id FROM matches;")
        return list(map(lambda x : x[0] , curs.fetchall()))

def get_match_data(match_id : int) -> dict[str , str]:
    match_chameleon = MatchDetailsChameleon()
    match_chameleon.observe(match_id = match_id)
    return match_chameleon.parse()

def observe_teams():
    chameleon = ChameleonFactory().get("match_players")
    match_ids = get_match_ids()

    for id_ in match_ids:
        chameleon.observe(match_id = id_)
        try:
            MatchDetails( teams = chameleon.parse() , match_id = id_)
        except Exception as e:
            print(e)
            print("Continuing to the next team.")
            continue

    event_time : str = attr.ib(converter = str , validator = instance_of(str))
    actors : list[str] = attr.ib(validator = instance_of(list))
    target : str = attr.ib(converter = str , validator = instance_of(str))
    weapon : str = attr.ib(converter = str , validator = instance_of(str))
    hs : bool = attr.ib(converter = bool , validator = instance_of(bool))
    wallbang : bool = attr.ib(converter = bool , validator = instance_of(bool))

def observe_round_details():
    chameleon = ChameleonFactory().get("round_details")

    match_ids = get_match_ids()
    for id_ in match_ids:
        chameleon.observe(match_id = id_)
        for round_ , items in chameleon.parse().items():
            roundFinanceParser(**{"match_id": id_,
                                                 "rounds": round_ ,
                                                  "equipment_value_t": items["t"]["equipment_value"],
                                                  "equipment_value_ct": items["ct"]["equipment_value"],
                                                  "cash_t" : items["t"]["cash"] ,
                                                  "cash_ct": items["ct"]["cash"],
                                                  "cash_spent_t": items["t"]["cash_spent"],
                                                  "cash_spent_ct":items["ct"]["cash_spent"]}
                                                  )

            for event in items["events"]:
                roundDetailsParser(**{"match_id" : id_,
                                                "rounds": round_,
                                                "event_time": event["event_time"],
                                                "actors": event["killers"],
                                                "target": event["target"],
                                                "weapon" : event["weapon"],
                                                "hs" : event["hs"],
                                                "wallbang" : event["wallbang"]})


        break


def main():

    actions = {"players": observe_leaderboards ,
                    "matches" : observe_matches,
                    "teams" : observe_teams ,
                    "round_finance": observe_round_details,
                    None: lambda : sys.exit() }

    parser = argparse.ArgumentParser()
    parser.add_argument("gather" , help = "scrapes a specific endpoint of csgo.stats website." , nargs='?')
    args = parser.parse_args()

    try:
        actions.get(args.gather)()
    except KeyError:
        print("Invalid argument!")




if __name__ == "__main__": main()
