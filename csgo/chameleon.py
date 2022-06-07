from datetime import datetime , timedelta
import attr
from attr.validators import instance_of
import cloudscraper
from collections import defaultdict , namedtuple
from urllib.parse import urljoin
from typing import Dict , Union , List , ClassVar
from csgo.utils import *
from bs4 import BeautifulSoup
import re
from time import sleep
from itertools import count
from abc import abstractmethod
from termcolor import colored
import logging
import os
import argparse

@attr.s(slots = True)
class Chameleon:

    url : str = attr.ib(converter = str , validator = instance_of(str))
    scraper = attr.ib(init = False)
    soup = attr.ib(init = False , default = None)

    def __attrs_post_init__(self) -> None:
        self.scraper = cloudscraper.create_scraper()

    @property
    def observing(self) -> bool:
        return self.soup is not None

    def observe(self , store : bool = False, verbose : bool = True ,**kwargs) -> bool:
        try:
            page = None
            endpoint = self.get_endpoint(**kwargs)
            if "=" in endpoint:
                page = int(endpoint.split('=')[-1])

            url = urljoin(self.url , endpoint )
            content =self.scraper.get(url).text
            self.soup = BeautifulSoup( content, 'html.parser')

            if verbose:
                print(colored(f"Observing page {url=}", "blue"))

            if store:
                with open( os.path.join( 'data' , url + ".html") , "w+") as data:
                    data.write(self.soup)
            return True
        except Exception as e:
            print(e)
            return False

    @abstractmethod
    def get_endpoint(self) -> str:
        pass

    @abstractmethod
    def parse(self):
        if not self.observing:
            raise Exception("Chameleon is not observing anything.")

class Nullified:

    def __new__(self , attribute):
        return type( type(self).__name__ , () , { attribute: {"title" : None}})


class CSGOChameleon(Chameleon):

    endpoints = {'MatchChameleon':'match',
                        'PlayersChameleon':'leaderboards',
                         'MatchDetailsChameleon':'match',
                         'MatchRoundDetailsChameleon' : 'match'}

    def __init__(self):
        super().__init__('https://csgostats.gg')

    def get_endpoint(self) -> str:
        return CSGOChameleon.endpoints.get(type(self).__name__)


class MatchChameleon(CSGOChameleon):

    def parse(self) -> Dict[str, str]:
        super().parse()
        for soupie in self.soup.find_all('tr', {'class':'p-row js-link'}):
            match_id = re.findall( r'match/(\d+)' , soupie.attrs['onclick'])[0]

            league_tag = soupie.find("td").find("img").attrs
            match list(filter(lambda key : key in league_tag , ["src" , "data-cfsrc"])):
                case ["data-cfsrc"]:
                    league_tag = league_tag["data-cfsrc"]
                case ["src"]:
                    league_tag = league_tag["src"]
                case _:
                    raise AttributeError("Something went wrong with the beautiful soup html parsing. It was unable to locate src or data-cfsrc in image tag.")

            league = re.findall(r'/([\w-]+).png' , league_tag)[0]

            csmap = soupie.find('img' , {'title':re.compile('(?:de_|cs_)')}).attrs['title']

            rank =(soupie.find('img', {'src':re.compile(r'ranks')}) or Nullified("attrs")).attrs['title']

            t_team , ct_team = soupie.find_all("td" , {"class" : "team-td" , "width":"70"})
            t_team = list(map(lambda player : player.attrs["title"] , t_team.find_all("img" , {"width" : "28" , "height":"28" , "data-cfsrc": False})))
            ct_team = list(map(lambda player : player.attrs["title"] , ct_team.find_all("img", {"width" : "28" , "height":"28" , "data-cfsrc" : False})))

            t_score , ct_score = soupie.find_all("td" , {"class" : "team-score" , "align":"center"})
            t_score = t_score.string
            ct_score = ct_score.string


            misc_statistics = list(map(lambda x : x.string.strip() ,
                                           soupie.find_all("td" , {"class": re.compile("col-stats") , "align":"center" , "style" : False})
                                        )
                              )
            misc_statistics = {
                                      "kills" :  misc_statistics[0] ,
                                       "deaths" : misc_statistics[1] ,
                                       "assists" : misc_statistics[2] ,
                                       "fivek" : misc_statistics[3] ,
                                       "fourk" : misc_statistics[4],
                                       "threek": misc_statistics[5] ,
                                       "onevsfive" : misc_statistics[6],
                                       "onevsfour": misc_statistics[7],
                                       "onevsthree": misc_statistics[8] ,
                                       "onevstwo" : misc_statistics[9],
                                       "onevsone": misc_statistics[10]
                                       }

            #TODO
            #Revise Team Construction
            # teams = list(map(lambda x : x.attrs['title'] ,
            #                     soupie.find_all('img',{'src':re.compile(r'avatars')})
            #                 )
            #             )
            # t_team , ct_team = teams[:5] , teams[5:]

            date = calculate_datetime(soupie.find('td',{'class':'nowrap'}).string.strip())

            matches = {  'match_id' :  match_id ,
                                'csmap': csmap ,
                                'date' : date ,
                                'league' : league ,
                                'rank': rank ,
                                "ct_score" : ct_score ,
                                "t_score":t_score ,
                                'players' : {'ct_team': ct_team ,
                                                    't_team': t_team}
                            }
            matches.update(misc_statistics)
            print(matches)

            yield matches


@attr.s(slots=True ,  kw_only = True)
class Match:

    match_id:str = attr.ib(validator = instance_of(str))
    csmap:str = attr.ib(validator = instance_of(str))
    rank: str = attr.ib()
    players : Dict[str , List[str]] = attr.ib( validator = instance_of(dict))
    league : str = attr.ib(converter = lambda x : x.split('-')[0] if '-' in x else x, validator = instance_of(str))
    t_team: str = attr.ib(init = False)
    ct_team : str = attr.ib(init = False)
    t_score : int = attr.ib(converter = int, validator = instance_of(int))
    ct_score : int = attr.ib(converter = int , validator = instance_of(int))
    kills : int = attr.ib(converter = int , validator = instance_of(int))
    deaths : int = attr.ib(converter = int , validator = instance_of(int))
    assists : int = attr.ib(converter = int , validator = instance_of(int))
    fivek : int = attr.ib(converter = int , validator = instance_of(int))
    fourk : int = attr.ib(converter = int , validator = instance_of(int))
    threek : int = attr.ib(converter = int , validator = instance_of(int))
    onevsfive : int = attr.ib(converter = int , validator = instance_of(int))
    onevsfour : int = attr.ib(converter = int , validator = instance_of(int))
    onevsthree : int = attr.ib(converter = int , validator = instance_of(int))
    onevstwo : int = attr.ib(converter = int , validator = instance_of(int))
    onevsone : int = attr.ib(converter = int , validator = instance_of(int))
    date : str = attr.ib(validator = instance_of(str))

    @players.validator
    def playersValidator(self , attr , val):
        if "ct_team" not in val.keys() or "t_team" not in val.keys():
            raise ValueError("Invalid keys.")

        if len(val["ct_team"]) != 5 or len(val["t_team"]) != 5:
            print(colored(val , "red"))
            raise ValueError("Invalid list lengths.")

    def __attrs_post_init__(self) -> None:
        self.t_team = "|".join(self.players["t_team"])
        self.ct_team ="|".join(self.players["ct_team"])
        self.insert()

    @validate
    def insert(self):
        attributes = {key: value for key , value in attr.asdict(self).items() if key != "players"}
        columns = ", ".join(attributes.keys())
        placeholders = ", ".join(["?"]*len(attributes))
        with SQL("csgo.db") as curs:
            curs.execute(f"INSERT INTO matches ({columns}) VALUES ({placeholders});" , list(attributes.values()))


    @staticmethod
    @validate
    def create_table():
        with SQL('csgo.db') as curs:
            curs.execute("""CREATE TABLE IF NOT EXISTS matches (
                                      match_id INT NOT NULL PRIMARY KEY,
                                      csmap TEXT,
                                      league TEXT,
                                      rank TEXT,
                                      date TEXT,
                                      t_team TEXT,
                                      ct_team TEXT,
                                      t_score INT,
                                      ct_score INT,
                                      kills INT,
                                      deaths INT,
                                      assists INT,
                                      fivek INT,
                                      fourk INT,
                                      threek INT,
                                      onevsfive INT,
                                      onevsfour INT,
                                      onevsthree INT,
                                      onevstwo INT,
                                      onevsone INT
                                      );""")
        print(colored(f"Table {Player.table_name} has been succesfully created!", "blue"))


class PlayersChameleon(CSGOChameleon):

    max_iter = 10000

    def get_endpoint(self , page : int = 1) -> str:
        return super().get_endpoint() + f'?page={page}'

    def observe_many(self) -> None:
        page = count()
        next(page)
        while True:
            cur_page = next(page)
            print(colored(f"Retrieving page {cur_page}..." , "blue"))
            sleep(0.5)
            self.observe(page = cur_page)

            if not self.soup.find('a' , {'href' :True , 'rel' : 'next'}):
                break

            if cur_page > PlayersChameleon.max_iter:
                break


            for player_data in self.parse():
                Player( **player_data )
            print(colored(f"Finished page {cur_page}." , "blue"))


    def parse(self) -> dict[str , str]:
            super().parse()
            for soupie in self.soup.find_all('div',{'onclick':re.compile(r'player')}):
                rank = soupie.find('div' , style="float:left; width:4%; padding-top:9px; color:#fff;").next_element

                player_id = re.findall( r'player/(\d+)' , soupie.attrs['onclick'])[0]

                player_name = soupie.find('a').text

                weapons = soupie.find_all('img',    {'src':  re.compile('weapons|') ,
                                                                        'style': 'max-width:60px; max-height:24px;'})
                primary_weapon = weapons[0].attrs['title']
                secondary_weapon = weapons[1].attrs['title']

                cake = soupie.find_all('div' , {'style':'float:left; width:10%;text-align:center;'})[2:]
                kills , deaths= cake[0].find('span').string.split('/')

                hs = cake[1].string
                win_rate = cake[2].next_element
                onevx = cake[3].string
                rating = cake[4].string

                player_data = {'player_id' : player_id,
                                        'rank': rank,
                                        'player_name': player_name,
                                        'primary_weapon' : primary_weapon,
                                        'secondary_weapon': secondary_weapon,
                                        'kills': kills,
                                        'deaths':deaths,
                                        'hs':hs,
                                        'win_rate':win_rate,
                                        'onevx': onevx,
                                        'rating':rating
                                        }
                yield player_data

custom_converters = {"player_name" : lambda x : x.strip('\n').strip(),
                      "rank": lambda x : int(x.lstrip('#').rstrip(' ')),
                      "kills": lambda x : int(x.strip()),
                       "deaths" : lambda x : int(x.strip()),
                       "hs" : lambda x : float(x.strip('%'))/1e2 ,
                       "win_rate": lambda x : float(x.strip('\n').strip().strip('%'))/1e2 ,
                       }

@attr.s(slots = True , frozen = True , kw_only = True)
class Player:

    player_id:int = attr.ib(converter=int , validator = instance_of(int))
    rank: int = attr.ib(converter = custom_converters.get("rank") , validator = instance_of(int))
    player_name: str = attr.ib(converter = custom_converters.get("player_name") , validator = instance_of(str))
    primary_weapon:str = attr.ib(validator = instance_of(str))
    secondary_weapon:str = attr.ib(validator = instance_of(str))
    kills:int = attr.ib(converter = custom_converters.get("kills") , validator = instance_of(int))
    deaths: int = attr.ib(converter = custom_converters.get("deaths")  , validator = instance_of(int))
    hs: str = attr.ib(converter = custom_converters.get("hs") , validator = instance_of(float))
    win_rate: str= attr.ib(converter = custom_converters.get("win_rate") , validator = instance_of(float))
    onevx : int = attr.ib(converter = int , validator = instance_of(int))
    rating:float = attr.ib(converter = float)
    table_name : ClassVar[str] = 'leaderboard'

    def __attrs_post_init__(self) -> None:
        self.insert()

    @validate
    def insert(self):
        columns = ', '.join(attr.asdict(self).keys())
        placeholders = ', '.join(['?']*len(attr.asdict(self)))
        query = f"""INSERT INTO {Player.table_name} ({columns})
                                     VALUES ({placeholders});"""
        with SQL('csgo.db') as curs:
            curs.execute(query , list(attr.asdict(self).values()))

    @staticmethod
    @validate
    def create_table():
        with SQL('csgo.db') as cursor:
            cursor.execute(f"""CREATE TABLE IF NOT EXISTS {Player.table_name} (
                                       player_id INT NOT NULL PRIMARY KEY,
                                       rank INT,
                                       player_name TEXT NOT NULL,
                                       primary_weapon TEXT,
                                       secondary_weapon TEXT,
                                       kills INT,
                                       deaths INT,
                                       hs REAL,
                                       win_rate REAL,
                                       onevx INT,
                                       rating REAL);""")
        print(f"Table {Player.table_name} has been succesfully created!")


class MatchDetailsChameleon(CSGOChameleon):

    def get_endpoint(self , match_id : int) -> str:
        return super().get_endpoint() + f"/{match_id}"

    def parse(self) -> dict[str, str]:
        return dict(zip( map(lambda x : x.find("span").string ,
                   self.soup.find_all("td" , {"width":"120" , "style":"white-space:nowrap;"})),
                    map(lambda x : x.find("a").attrs["href"].split('/')[-1] if x.find("a") else None,
                    self.soup.find_all("td" , {"width":"120" , "style":"white-space:nowrap;"})))) | {"match_id" :"" }

@attr.s(slots = True , kw_only = True)
class MatchDetails:

    match_id : int

    def insert(self):
        pass

    @staticmethod
    @validate
    def create_table():
        with SQL("csgo.db") as cursor:
            cursor.execute("""CREATE TABLE IF NOT EXISTS match_details (
                                            match_id
            );""")



class MatchRoundDetailsChameleon(MatchDetailsChameleon):

    def get_endpoint(self , match_id : str) -> str:
        return super().get_endpoint(match_id) + "#/rounds"

    def parse(self) -> dict[str,str]:
        match_stats = dict()
        for round_ , stuff in enumerate(content.find_all("div" , style = "padding:7px 0;")):
            round_ += 1
            match_stats.update({f"round {round_}" : dict() })
            match_stats[f"round {round_}"]["events"] = []

            for idx , soupie in enumerate(stuff.find_all('div', class_ = 'round-info-side')):
                match idx%2:
                    case False:
                        t_team = list(map(lambda x : x.string.strip("\n").strip() ,
                                                          soupie.find_all("div",{"style":"float:left; width:16%; font-size:12px;"})))

                        ct_team = list(map(lambda x : x.string.strip("\n").strip() ,
                                                            soupie.find_all("div",{"style": "float:left; width:16%; font-size:12px; text-align:right;"})))

                        match_stats[f"round {round_}"].update({"t_team":    {"equipment_value": t_team[0],
                                                                                                        "cash" :                       t_team[1],
                                                                                                        "cash_spent" :            t_team[2] } ,
                                                                                        "ct_team":  {"equipment_value": ct_team[0],
                                                                                                            "cash" :                   ct_team[1],
                                                                                                            "cash_spent" :        ct_team[2] }})
                    case True:
                        round_winner = soupie.find("span" , class_ = "attacker").string.strip("\n").strip()
                        match_stats[f"round {round_}"].update({"round_winner" : round_winner})

                        for cake in soupie.find_all("div" , class_ = "tl-inner"):
                            killing_team = cake.find("span" , {"class": re.compile(r"team-")}).attrs["class"][0].split("-")[-1]
                            event_time = cake.find("span" , {"title": re.compile(r"Tick")}).string
                            world = cake.find('span' , {"class" : re.compile(r"team-") , "dir" : "ltr"}).next_sibling.strip() == "world"

                            actors = list(map(lambda x : x.string , cake.find_all('span', {"class": re.compile(r"team-"),"dir" : "ltr"})))

                            killers , target = actors[:-1] , actors[-1]

                            match world:
                                case False:
                                    weapon_headshot = cake.find_all("img")
                                    hs , wallbang = len(weapon_headshot) > 1 , len(weapon_headshot) > 2
                                    weapon = weapon_headshot[0].attrs["title"]
                                case True:
                                    hs , wallbang = False , False
                                    weapon = world

                        match_details = {
                                        "event_time" : event_time,
                                        "killing_team" : killing_team,
                                        "killers" : killers,
                                        "target" : target ,
                                        "weapon" : weapon,
                                        "hs" : hs,
                                        "wallbang": wallbang}
                        match_stats[f"round {round_}"]["events"].append(match_details)
        return match_stats


class ChameleonFactory:

    chameleons = {"leaderboard" : PlayersChameleon() ,
                            "match" :       MatchChameleon() ,
                            "round_details" : MatchRoundDetailsChameleon(),
                            "details" : MatchDetailsChameleon()
                        }

    def __init__(self) -> None:
        self.chameleon : Chameleon = None

    def get(self , chameleon: str) -> Chameleon:
        try:
            return ChameleonFactory.chameleons.get(chameleon.strip())
        except KeyError:
            raise KeyError(f"Invalid chameleon type {chameleon=}.")


def players_chameleon():
    #drop(table = 'leaderboard')
    #Player.create_table()
    display_tables()


    chameleon = PlayersChameleon()
    #chameleon.observe_many()
    # chameleon.observe(page = 15)
    # results = chameleon.parse()
    # print(colored("Retrieving Data", "blue"))
    # for result in results:
    #    Player(**result)
    # print(colored("Quering Database", "blue"))
    query(table = 'leaderboard')

def match_chameleon():
    #drop(table = "matches")
    #Match.create_table()

    chameleon = MatchChameleon()
    chameleon.observe()
    for matches in chameleon.parse():
            try:
                Match(**matches)
            except ValueError:
                continue


    #quering table
    query(table = "matches")



def main():
    match_chameleon()




if __name__ == "__main__": main()
