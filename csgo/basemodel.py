from typing import Dict , Union , List , ClassVar
import attr
from attr.validators import instance_of
from urllib.parse import urljoin
from abc import abstractmethod
import cloudscraper
from bs4 import BeautifulSoup
from termcolor import colored


@attr.s
class Chameleon:

    url : str = attr.ib(converter = str , validator = instance_of(str))
    scraper = attr.ib(init = False , repr = False)
    soup : str = attr.ib(init = False , default = None , repr = False)

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
            content = self.scraper.get(url).text
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
        """Fetches endpoint from corresponding url to be parsed."""
        pass

    @abstractmethod
    def parse(self) -> dict:
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
