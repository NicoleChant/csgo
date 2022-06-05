from datetime import datetime , timedelta
import attr
import cloudscraper
from attr import validators
from collections import defaultdict
from urllib.parse import urljoin
from typing import Dict , Union , List , ClassVar
from utils import *
from bs4 import BeautifulSoup
import re
from attr.validators import instance_of
from time import sleep
from itertools import count
from abc import abstractmethod
from termcolor import colored
import logging
import os
import argparse

class Chameleon:

    def __init__(self , url : str) -> None:
        self.url = str(url)
        self.scraper = cloudscraper.create_scraper()
        self.soup = None

    def observe(self , store : bool = False, **kwargs) -> bool:
        try:
            endpoint = self.get_endpoint(**kwargs)
            page = int(endpoint.split('=')[-1])
            print(colored(f"Observing {page=}", "blue"))
            url = urljoin(self.url , endpoint )
            content =self.scraper.get(url).text
            self.soup = BeautifulSoup( content, 'html.parser')

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
        pass


class CSGOChameleon(Chameleon):

    endpoints = {'MatchesChameleon':'matches',
                        'PlayersChameleon':'leaderboards',
                         'MatchesDetailsChameleon':''}

    def __init__(self):
        super().__init__('https://csgostats.gg')

    def get_endpoint(self) -> str:
        return CSGOChameleon.endpoints.get(type(self).__name__)


class MatchesChameleon(CSGOChameleon):

    def parse(self) -> Dict[str, Union[str , List[str] , int]]:
        all_matches = []

        for soupie in self.soup.find_all('tr', {'class':'p-row js-link'}):
            match_id = re.findall( r'match/(\d+)' , soupie.attrs['onclick'])[0]

            csmap = soupie.find('img' , {'title':re.compile(r'de_*')}).attrs['title']

            rank = soupie.find('img', {'src':re.compile(r'ranks')}).attrs['title']

            teams = list(map(lambda x : x.attrs['title'] ,
                             soupie.find_all('img',{'src':re.compile(r'avatars')})
                            )
                        )
            t_team , ct_team = teams[:5] , teams[5:]

            date = calculate_datetime(soupie.find('td',{'class':'nowrap'}).string.strip())

            matches['match_id'] = match_id
            matches['map'] = csmap
            matches['date'] = date
            matches['rank'] = rank
            matches['players'] = {'ct_team': ct_team,
                                              't_team': t_team}
            yield matches

@attr.s(slots=True , kw_only = True)
class Match:

    match_id:str = attr.ib(validator = instance_of(str))
    csmap:str = attr.ib(validator = instance_of(str))
    rank:int = attr.ib(validator = instance_of(int))
    t_team: List[str] = attr.ib(validator = instance_of(list))
    ct_team : List[str] = attr.ib(validator = instance_of(list))
    date : str = attr.ib(validator = instance_of(str))

    def insert(self):
        pass

    @validate
    @staticmethod
    def create_table():
        with SQL('csgo.db') as curs:
            curs.execute("""CREATE TABLE IF NOT EXISTS matches (
                                      match_id INT NOT NULL PRIMARY KEY,
                                      csmap TEXT,
                                      rank INTEGER,
                                      date TEXT);""")




class PlayersChameleon(CSGOChameleon):

    def get_endpoint(self , page : int = 1) -> str:
        return super().get_endpoint() + f'?page={page}'

    def observe_many(self):
        page = count()
        next(page)
        max_iter = 10000
        while True:
            cur_page = next(page)
            print(colored(f"Retrieving page {cur_page}..." , "blue"))
            sleep(0.5)
            self.observe(page = cur_page)

            if not self.soup.find('a' , {'href' :True , 'rel' : 'next'}):
                break

            if cur_page > max_iter:
                break


            for player_data in self.parse():
                Player( **player_data )
            print(colored(f"Finished page {cur_page}." , "blue"))


    def parse(self) -> Dict[str , str]:
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

converters = {"player_name" : lambda x : x.strip('\n').strip(),
                      "rank": lambda x : int(x.lstrip('#').rstrip(' ')),
                      "kills": lambda x : int(x.strip()),
                       "deaths" : lambda x : int(x.strip()),
                       "hs" : lambda x : float(x.strip('%'))/1e2 ,
                       "win_rate": lambda x : float(x.strip('\n').strip().strip('%'))/1e2 ,
                       }

@attr.s(slots = True , frozen = True , kw_only = True)
class Player:

    player_id:int = attr.ib(converter=int , validator = instance_of(int))
    rank: int = attr.ib(converter = converters.get("rank") , validator = instance_of(int))
    player_name: str = attr.ib(converter = converters.get("player_name") , validator = instance_of(str))
    primary_weapon:str = attr.ib(validator = instance_of(str))
    secondary_weapon:str = attr.ib(validator = instance_of(str))
    kills:int = attr.ib(converter = converters.get("kills") , validator = instance_of(int))
    deaths: int = attr.ib(converter = converters.get("deaths")  , validator = instance_of(int))
    hs: float = attr.ib(converter = converters.get("hs") , validator = instance_of(float))
    win_rate:str = attr.ib(converter = converters.get("win_rate") , validator = instance_of(float))
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


class MatchesDetailsChameleon(Chameleon):

    def parse(self):
        rounds = {'round_id' : ''}

        for round_ , soupie in enumerate(soup.find_all('div', class_ = 'round-info-side')):
            if not round_%2:
                continue

            round_stats = defaultdict(list)

            for cake in soupie.find_all('div', class_ = 'tl-inner'):
                ##get time
                time = cake.find('span', {'title': re.compile(r'Tick*')}).string
                round_stats["Times"].append(time)

                ##killing team
                killer_team = cake.find('span' , {'class': re.compile(r'team')})\
                                  .attrs['class'][0].split('-')[-1]

                ##actors
                actors = list(map( lambda x : x.string ,
                            cake.find_all('span' , {'class': re.compile(r'team-')})))

                killers = ', '.join(actors[:-1])
                dead = actors[-1]
                round_stats["Actors"].append(killers)
                round_stats["Target"].append(dead)

                ##weapon
                weapon_headshot = cake.find_all('img')
                round_stats['Weapon'].append(weapon_headshot[0].attrs['title'])

                ##headshot
                headshot = len(weapon_headshot) > 1
                round_stats["Headshot"].append(headshot)

            ##winner
            winner = soupie.find('span',class_ = 'attacker').string.strip('\n').strip()
            round_stats['Winner'].append(winner)


            rounds.update({round_: round_stats})
        return rounds


def main():
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




if __name__ == "__main__": main()
