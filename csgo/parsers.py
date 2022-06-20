from termcolor import colored
from typing import Dict , Union , List , ClassVar
import attr
from attr.validators import instance_of
from csgo.utils import *

"""Custom Converters"""

custom_converters = {"player_name" : lambda x : x.strip('\n').strip(),
                                    "rank": lambda x : int(x.lstrip('#').rstrip(' ')),
                                    "kills": lambda x : int(x.strip()),
                                    "deaths" : lambda x : int(x.strip()),
                                    "hs" : lambda x : float(x.strip('%'))/1e2 ,
                                    "win_rate": lambda x : float(x.strip('\n').strip().strip('%'))/1e2 ,
                                    }


"""Player Class Converter"""


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
        print(colored(f"Table {Player.table_name} has been succesfully created!", "blue"))



"""Player Profile Parser"""

@attrs.s(slots = True , kw_only = True)
class PlayerProfile:

    player_id : int = attr.ib(validator = instance_of(int) , converter = int)
    player_name : str = attr.ib()
    total_games : int = attr.ib()
    victories : int
    defeats : int
    draws : int
    kills : int
    deaths : int
    assists : int
    headshots : int
    total_damage : int
    total_rounds : int
    primary_weapon : str
    onevsone : float
    onevstwo: float
    onevsthree: float
    onevsfour: float
    onevsfive : float
    table_name : ClassVar[str] = "playerProfiles"

    def __attrs_post_init__(self) -> None:
        self.insert()

    @validate
    def insert(self) -> None:
        with SQL("csgo.db") as curs:
            curs.execute(f"""INSERT INTO {PlayerProfile.table_name} () VALUES;""", [])


    @staticmethod
    @validate
    def create_table() -> None:
        with SQL("csgo.db") as curs:
            curs.execute(f"""CREATE TABLE IF NOT EXISTS {PlayerProfile.table_name} (
                                                                                                player_id INTEGER NOT NULL PRIMARY KEY,
                                                                                                player_name VARCHAR(50),
                                                                                                total_games INT,
                                                                                                victories INT,
                                                                                                defeats INT,
                                                                                                draws INT,
                                                                                                kills INT,
                                                                                                deaths INT,
                                                                                                assists INT,
                                                                                                headshots INT,
                                                                                                total_damage INT,
                                                                                                total_rounds INT,
                                                                                                primary_weapon VARCHAR(50),
                                                                                                onevsone REAL,
                                                                                                onevstwo REAL,
                                                                                                onevsthree REAL,
                                                                                                onevsfour REAL,
                                                                                                onevsfive REAL
            );""")
        print(colored(f"Table {table_name} has been succesfully created!", "blue"))


"""Match Class Converter"""



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
    table_name : ClassVar[str] = "matches"

    @players.validator
    def playersValidator(self , attr , val) -> None:
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
            curs.execute(f"INSERT INTO {Match.table_name} ({columns}) VALUES ({placeholders});" , list(attributes.values()))
        print(colored("Match has been added to the db." , "blue"))


    @staticmethod
    @validate
    def create_table():
        with SQL('csgo.db') as curs:
            curs.execute(f"""CREATE TABLE IF NOT EXISTS {Match.table_name} (
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
        print(colored(f"Table {Match.table_name} has been succesfully created!", "blue"))


"""Match Details Class Converter"""

def teamConverter(team : dict[str , Union[str , None]]) -> dict[str , Union[int , None]]:
    for key in team.keys():
        team[key] = int(team[key]) if team[key] else team[key]
    return team


@attr.s(slots = True , kw_only = True)
class MatchDetails:

    match_id : int = attr.ib(converter = int , validator = instance_of(int))
    teams : dict[str , str] = attr.ib(converter = teamConverter)
    table_name : ClassVar[str] = "teamMatches"

    @teams.validator
    def teamsValidator(self , attr , val) -> None:
        if any( not isinstance(id_ ,int) and id_ is not None for id_ in self.teams.values()) or not isinstance(self.teams , dict):
            raise ValueError("Invalid argument for team slot.")

    def __attrs_post_init__(self) -> None:
        self.insert()

    @validate
    def insert(self) -> None:
        with SQL("csgo.db") as cursor:
            cursor.executemany(f"""INSERT INTO {MatchDetails.table_name} (match_id, player_id)
                                         VALUES (?,?);""" , [ ( self.match_id , value , ) for value in self.teams.values()] )
        print(colored(f"Teams for match {self.match_id} have been appended to the database." , "blue"))

    @staticmethod
    @validate
    def create_table() -> None:
        with SQL("csgo.db") as cursor:
            cursor.execute(f"""CREATE TABLE IF NOT EXISTS {MatchDetails.table_name} (
                                            match_id INTEGER NOT NULL,
                                            player_id INTEGER,
                                            FOREIGN KEY (match_id)
                                                REFERENCES {Match.table_name} (match_id),
                                            FOREIGN KEY (player_id)
                                                REFERENCES {Player.table_name} (player_id)
            );""")
            print(colored(f"Table {MatchDetails.table_name} has been succesfully created!", "blue"))



"""Round Finance Class Converter"""

finance_custom_converters = {}

@attr.s(kw_only = True , slots = True)
class roundFinanceParser:

    match_id : int = attr.ib(converter = int , validator = instance_of(int))
    rounds : int = attr.ib(converter = int , validator = instance_of(int))
    equipment_value_t : int = attr.ib(validator = instance_of(int))
    cash_t : int = attr.ib(validator = instance_of(int))
    cash_spent_t : int = attr.ib(validator = instance_of(int))
    equipment_value_ct : int = attr.ib(validator = instance_of(int))
    cash_ct : int = attr.ib(validator = instance_of(int))
    cash_spent_ct : int = attr.ib(validator = instance_of(int))
    table_name : ClassVar[str] = "roundFinancial"

    def __attrs_post_init__(self) -> None:
        self.insert()

    @validate
    def insert(self):
        columns = ", ".join(attr.asdict(self).keys())
        placeholders = ", ".join(["?"]*len(columns))
        with SQL("csgo.db") as curs:
            curs.execute(f"""INSERT INTO {roundFinanceParser.table_name} ({columns}) VALUES ({placeholders});""" , list(attr.asdict(self).values()))

    @staticmethod
    @validate
    def create_table():
        with SQL("csgo.db") as curs:
            curs.execute(f"""CREATE TABLE IF NOT EXISTS {roundFinanceParser.table_name} (
                                                            match_id INTEGER NOT NULL,
                                                            rounds INTEGER NOT NULL,
                                                            equipment_value_t INTEGER
                                                            cash_t INTEGER
                                                            cash_spent_t INTEGER,
                                                            equipment_value_ct INTEGER,
                                                            cash_ct INTEGER,
                                                            cash_spent_ct INTEGER,
                                                            FOREIGN KEY (match_id)
                                                                REFERENCES {Match.table_name} (match_id)
            );""")
            print(colored(f"Table {roundFinanceParser.table_name} has been succesfully created!", "blue"))




"""Round Details Class Converter"""


@attr.s(kw_only = True , slots = True)
class roundDetailsParser:

    match_id : int = attr.ib(converter = int , validator = instance_of(int))
    rounds : int = attr.ib(converter = int , validator = instance_of(int))
    event_time : str = attr.ib(converter = str , validator = instance_of(str))
    actors : list[str] = attr.ib(validator = instance_of(list))
    target : str = attr.ib(converter = str , validator = instance_of(str))
    weapon : str = attr.ib(converter = str , validator = instance_of(str))
    hs : bool = attr.ib(converter = bool , validator = instance_of(bool))
    wallbang : bool = attr.ib(converter = bool , validator = instance_of(bool))
    table_name : ClassVar[str] = "roundDetails"

    def __attrs_post_init__(self) -> None:
        self.insert()

    @validate
    def insert(self):
        columns = ", ".join(attr.asdict(self).keys())
        placeholders = ", ".join(["?"]*len(attr.asdict(self)))
        with SQL("csgo.db") as curs:
            curs.execute(f"""INSERT INTO {roundDetailsParser.table_name} ({columns}) VALUES ({placeholders});""" , list(attr.asdict(self).values()))


    @staticmethod
    @validate
    def create_table():
        with SQL("csgo.db") as curs:
            curs.execute(f"""CREATE TABLE IF NOT EXISTS {roundDetailsParser.table_name} (
                                                                                            match_id INTEGER NOT NULL,
                                                                                            rounds INTEGER NOT NULL,
                                                                                            event_time TEXT NOT NULL,
                                                                                            target TEXT,
                                                                                            weapon TEXT,
                                                                                            hs BOOLEAN,
                                                                                            wallbang BOOLEAN,
                                                                                            FOREIGN KEY (match_id)
                                                                                                REFERENCES {Match.table_name} (match_id)
                                                                                                );""")
            print(colored(f"Table {roundDetailsParser.table_name} has been succesfully created!", "blue"))


"""Parser Factory"""


class ParserFactory:

    parsers = {"roundFinance" : roundFinanceParser ,
                     "roundDetails" : roundDetailsParser ,
                     "player" : Player ,
                     "match" : Match ,
                     "matchDetails" : MatchDetails}


    def get(self , parser : str):
        try:
            return ParserFactory.parsers.get(parser.strip())
        except KeyError:
            raise KeyError(f"Could not locate the specified parser {parser}.")

    def show_parsers(self) -> None:
        for key in ParserFactory.parsers.keys():
            print(key)

    def create_all_tables(self) -> None:
        print(colored("Creating tables..." , "blue"))
        for parser in ParserFactory.parsers.values():
            parser.create_table()




def remove_table(table_name:str) -> None:
    with SQL("csgo.db") as curs:
        curs.execute(f"DROP TABLE IF EXISTS {table_name};")
    print(colored(f"Table {table_name} has been succesfully dropped!" , "blue"))

"""Creates tables when .THIS script is run"""


if __name__ == "__main__":
    ParserFactory().create_all_tables()
