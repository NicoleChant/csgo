from datetime import datetime , timedelta
from collections import defaultdict , namedtuple
import re
from time import sleep
from itertools import count
import os
import argparse
from csgo.parsers import *
from csgo import basemodel
from bs4 import BeautifulSoup



class MatchChameleon(basemodel.CSGOChameleon):

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

            yield matches




class PlayersChameleon(basemodel.CSGOChameleon):

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


class MatchDetailsChameleon(basemodel.CSGOChameleon):

    def get_endpoint(self , match_id : int) -> str:
        return super().get_endpoint() + f"/{match_id}"

    def parse(self) -> dict[str, str]:
        return dict(zip( map(lambda x : x.find("span").string ,
                   self.soup.find_all("td" , {"width":"120" , "style":"white-space:nowrap;"})),
                    map(lambda x : x.find("a").attrs["href"].split('/')[-1] if x.find("a") else None,
                    self.soup.find_all("td" , {"width":"120" , "style":"white-space:nowrap;"}))))



class MatchRoundDetailsChameleon(MatchDetailsChameleon):

    def __init__(self) -> None:
        super().__init__()

    def get_endpoint(self , match_id : str) -> str:
        return super().get_endpoint(match_id) + "#/rounds"

    @staticmethod
    def get_match_round_finance(soupie) -> dict[str , dict[str , str]]:
        t_team = list(map(lambda x : x.string.strip("\n").strip() ,
                                                          soupie.find_all("div",{"style":"float:left; width:16%; font-size:12px;"})))

        ct_team = list(map(lambda x : x.string.strip("\n").strip() ,
                                            soupie.find_all("div",{"style": "float:left; width:16%; font-size:12px; text-align:right;"})))

        return {"t_team":    {"equipment_value": t_team[0],
                                        "cash" :                       t_team[1],
                                        "cash_spent" :            t_team[2] } ,
                    "ct_team":  {"equipment_value": ct_team[0] ,
                                        "cash" :                   ct_team[1] ,
                                        "cash_spent" :        ct_team[2] }}


    @staticmethod
    def get_match_round_kill_events(cake) -> dict[str , Union[str , bool , list[str]]]:
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

        return { "event_time" : event_time,
                    "killing_team" : killing_team,
                    "killers" : killers,
                    "target" : target ,
                    "weapon" : weapon,
                    "hs" : hs,
                    "wallbang": wallbang}



    def parse(self) -> dict[str,str]:
        match_stats = dict()
        for round_ , stuff in enumerate(self.soup.find_all("div" , style = "padding:7px 0;")):
            round_ += 1
            match_stats.update({f"round {round_}" : dict() })
            match_stats[f"round {round_}"]["events"] = []

            for idx , soupie in enumerate(stuff.find_all('div', class_ = 'round-info-side')):
                match not not idx%2:
                    case False:
                        match_stats[f"round {round_}"].update(MatchRoundDetailsChameleon.get_match_round_finance(soupie))

                    case True:
                        round_winner = soupie.find("span" , class_ = "attacker").string.strip("\n").strip()
                        match_stats[f"round {round_}"].update({"round_winner" : round_winner})

                        for cake in soupie.find_all("div" , class_ = "tl-inner"):
                            match_stats[f"round {round_}"]["events"].append(MatchRoundDetailsChameleon.get_match_round_kill_events(cake))
        return match_stats



class ChameleonFactory:

    chameleons = {"leaderboard" : PlayersChameleon() ,
                            "match" :       MatchChameleon() ,
                            "round_details" : MatchRoundDetailsChameleon(),
                            "details" : MatchDetailsChameleon()
                        }

    def show_chameleons(self):
        for chameleon in ChameleonFactory.chameleons.keys():
            print(chameleon)

    def get(self , chameleon: str) -> basemodel.Chameleon:
        try:
            return ChameleonFactory.chameleons.get(chameleon.strip())
        except KeyError:
            raise KeyError(f"Invalid chameleon type {chameleon=}.")


if __name__ == "__main__":
    pass
