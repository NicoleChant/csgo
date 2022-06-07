import sqlite3
import os
from datetime import datetime , timedelta
from typing import Callable

class SQL:


    def __init__(self , database : str , return_curs : bool = True) -> None:
        self.connection = None

        self.database = os.path.join(  '/'.join(__file__.split('/')[:-1]) , database )
        self.return_curs = return_curs

    def __enter__(self):
        self.connection = sqlite3.connect( self.database )
        return self.connection.cursor() if self.return_curs else self.connection

    def __exit__(self , *args) -> None:
        self.connection.commit()
        self.connection.close()
        self.connection = None


def validate(func) -> Callable:
    def wrapper(*args,**kwargs):
        try:
            return func(*args,**kwargs)
        except sqlite3.Error as e:
            print(e)
    return wrapper

@validate
def query(table:str):
        with SQL('csgo.db') as cursor:
            cursor.execute(f"SELECT * FROM {table};")
            for idx , result in enumerate(cursor.fetchall()):
                print(idx , result)

@validate
def display_tables():
    with SQL('csgo.db') as cursor:
        cursor.execute("SELECT * FROM sqlite_master;")
        for result in map(lambda x : x[2] , cursor.fetchall()):
            print(result)

@validate
def drop(table:str):
    with SQL('csgo.db') as cursor:
        cursor.execute(f"""DROP TABLE IF EXISTS {table};""")
    print(f"Table {table} has been succesfully dropped.")


def calculate_datetime(time_of_logging:str) -> str:
    return (datetime.now() - timedelta(minutes = int(time_of_logging.split(' ')[0])
                                                            )
                ).strftime('%Y-%m-%d %H:%M:%S')
