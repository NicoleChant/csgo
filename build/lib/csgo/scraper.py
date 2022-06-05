import os
import requests
import time
from bs4 import BeautifulSoup
import sqlite3
from sqlite3 import Error
from collections import defaultdict
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import datetime
from typing import Union , Callable , Dict

class Spider:

    def __init__(self) -> None:
        self.driver = webdriver.Chrome()
        self.base_url = "https://csgostats.gg"
        self.web_generator = Spider.create_web()

    def get_data(self, url : str , params ) -> Union[ str , int]:
        response = requests.get(url , params = params)
        if response.status_code == 200:
            return response.content.decode("utf-8")
        return response.status_code

    @staticmethod
    def create_web():
        web = 1
        while True:
            yield web
            web += 1

    def crawl_all(self) -> None:
        cnt = 1
        while True:
            try:
                self.crawl_page()
                print(f"Spider has crawled the page {cnt}.")
                cnt += 1
            except Exception as e:
                print(e)
                break
        print("Spider is tired and has stopped crawling...")


class PlayerSpider(Spider):

    def __init__(self) -> None:
        super().__init__()
        self.url = self.base_url + "/leaderboards"

    def crawl_page(self) -> None:
        url = self.url + f"?{next(self.web_generator)}"
        self.driver.get(url)

        soup = BeautifulSoup( self.driver.page_source ,  'html.parser')

        with open("data/sample.html" , "w+") as file:
            file.write(self.driver.page_source)

        for soupie in soup.find('div', class_ = "global-lb").find_all('div' , {"onclick":True}):
            user_id = soupie.find("div" , style = "float:left; width:25%;")\
                                      .find("a" , style = "color:#fff;")\
                                      .attrs["href"].split('/')[-1]

            user_name = soupie.find("div" , style = "float:left; width:25%;")\
                                            .find("a" , style = "color:#fff;")\
                                            .contents[-1].strip('\n').strip()

            elements = soupie.find_all("div" , style = "float:left; width:10%;text-align:center;")

            primary_weap = elements[0].find("img")\
                                    .attrs["title"]
            secondary_weap = elements[1].find("img")\
                                        .attrs["title"]
            kd = elements[2].find("span" , style = "color:#999;")\
                            .string.replace(' ','')
            hs = elements[3].string.strip('%')
            win_rate =elements[4].next_element.strip('\n').strip().strip('%')
            vx = elements[5].string
            rating = elements[6].string

            user_stats = { "user_id" : user_id ,
                                    "user_name" : user_name ,
                                    "primary_weap" :  primary_weap ,
                                    "secondary_weap" : secondary_weap ,
                                    "kd" :  kd ,
                                    "hs"  : hs ,
                                    "win_rate" : win_rate ,
                                    "vx": vx ,
                                    "rating" : rating }

            User(**user_stats)


class TeamSpider(Spider):

    def __init__(self) -> None:
        super().__init__()
        self.url = self.base_url + '/match'

    def crawl_page(self) -> None:
        url = self.url + f"{next(self.web_generator)}"
        self.driver.get(url)

        soup = BeautifulSoup( self.driver.page_source , 'html.parser').find('tbody')

        for soupie in soup.find_all('tr'):
            teams = tuple(map(lambda x : x.attrs['title'] , soupie.find_all('img' ,
                                                                            {"style":"margin:0 2px; border:2px solid rgba(255,255,255,0.5); border-radius:3px;"})))
            ctTeam , tTeam = teams[:5] , teams[5:]



class SQL:

    """csgo sqlite database connector"""

    def __init__(self) -> None:
        self.conn = None
        self.db_name = 'csgo.db'

    def __enter__(self):
        self.conn = sqlite3.connect( os.path.join( 'data' , self.db_name) )
        return self.conn.cursor()

    def __exit__(self , *args) -> None:
        self.conn.commit()
        self.conn.close()
        self.conn = None


def create_db() -> None:
    """Creates SQLite database"""

    conn = None
    try:
        with SQL():
            pass
    except Error as e:
        print(e)
    finally:
        if conn:
            conn.close()


def checker(func):
    try:
        return func
    except Error as e:
        print(e)


@checker
def show_tables():
    """Displays tables of a sqlite database"""

    with SQL() as curs:
        curs.execute("SELECT * FROM sqlite_master;")
        return curs.fetchall()


class UserParser(type):

    def __new__(cls , namespace , bases , dic) -> None:
        return super().__new__(cls , namespace , bases , dic)


class User(metaclass = UserParser):

    __slots__ =  ["date", "user_id" , "user_name" , "primary_weap" , "secondary_weap" , "kd" , "hs" , "win_rate" , "vx" , "rating" ]

    datatypes = {"date" : str,
                        "user_id" : str ,
                        "user_name" : str ,
                        "primary_weap" : str ,
                        "secondary_weap" : str ,
                        "kd" : str ,
                        "hs" : float ,
                        "win_rate" : float ,
                        "vx" : int ,
                        "rating" : float
                        }

    def __init__(self ,**kwargs) -> None:
        for key in User.__slots__:
            if key in kwargs.keys():
                try:
                    ###typecasting
                    setattr(self , key , User.datatypes.get(key)( kwargs.get(key) ) )
                except Exception as e:
                    print(e)
                    raise ValueError()
            else:
                setattr(self , key , None)
        self.date = datetime.datetime.now().strftime(r'%y-%m-%d')
        self.insert_user()

    def __str__(self) -> str:
        representation = "User\n"
        for key , value in self.__dict__.items():
            representation += f"{key}:{value}\n"
        return representation

    @property
    def __dict__(self) -> Dict[str , Union[str , int] ]:
        return {attr : getattr(self , attr) for attr in User.__slots__}

    @property
    def columns(self) -> str:
        return ', '.join(self.__dict__.keys())

    @checker
    def insert_user(self) -> None:
        placeholders = ', '.join( ['?']*len(self.__dict__))
        query = f"""INSERT INTO users ({self.columns})
                                      VALUES ({placeholders});"""

        with SQL() as curs:
            curs.execute(query , tuple(self.__dict__.values() ) )

    @checker
    def query_users() -> None:
        with SQL() as curs:
            curs.execute("SELECT * FROM users;")
            print(curs.fetchall())

    @checker
    @staticmethod
    def create_users_table() -> None:
        with SQL() as curs:
                curs.execute("""CREATE TABLE users
                                        (
                                        date VARCHAR(100) NOT NULL,
                                        user_id INTEGER NOT NULL PRIMARY KEY,
                                        user_name VARCHAR(50) NOT NULL,
                                        primary_weap VARCHAR(20),
                                        secondary_weap VARCHAR(20),
                                        kd VARCHAR(20),
                                        hs REAL,
                                        win_rate REAL,
                                        vX INTEGER,
                                        rating REAL
                                        )
                                        ;""")
        print("users table has been succesfully created!")

    @checker
    @staticmethod
    def create_matches_table() -> None:
        with SQL() as curs:
            curs.execute("""CREATE TABLE matches (
                                                                                date VARCHAR(100) NOT NULL,
                                                                                map VARCHAR(20) NOT NULL,
                                                                                 ct-team VARCHAR(250) NOT NULL,
                                                                                 t-team VARCHAR(250) NOT NULL,
                                                                                 duration REAL,
                                                                                 winningTeam VARCHAR(10) NOT NULL,
                                                                                 totalRounds INTEGER,
                                                                                 league VARCHAR(50),
                                                                                 tRoundsWon INTEGER,
                                                                                 cRoundsWon INTEGER
            );""")
            print("matches table has been succesfully created!")

    @checker
    @staticmethod
    def truncate_users_table() -> None:
        with SQL() as curs:
            curs.execute("""DROP TABLE IF EXISTS users;""")
        print("users table has been succesfully dropped!")


def main():
    User.truncate_users_table()
    User.create_users_table()
    #show_tables()

    datatypes = {
            "user_id" : 24324,
            "user_name" : "Nicole" ,
            "primary_weap" : "some" ,
            "secondary_weap" : "another" ,
            "kd" : "erer" ,
            "hs" : "0.8" ,
            "win_rate" : "80.0" ,
            "vx" : 10 ,
            "rating" : 4.5
            }

    user = User(**datatypes)
    spider = PlayerSpider()
    spider.crawl_all()
    User.query_users()



if __name__ == "__main__": main()
