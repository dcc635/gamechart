import csv
import json
import os
import re
import sys
import time
from decimal import Decimal
from pprint import pprint
import matplotlib.pyplot as plt
import numpy as np

import requests
from bs4 import BeautifulSoup


# import drive_upload


class Game:

    def __init__(self, title=None, percentage=None, platform=None, score=None, main=None, main_extra=None, completionist=None):
        self.title = title
        self.percentage = percentage
        self.platform = platform
        self.score = score
        self.main = main
        self.main_extra = main_extra
        self.completionist = completionist

    def __str__(self):
        return '(' \
               f'title={self.title}, ' \
               f'percentage={self.percentage}, ' \
               f'platform={self.platform}, ' \
               f'score={self.score}, ' \
               f'main={self.main}, ' \
               f'main_extra={self.main_extra}, ' \
               f'completionist={self.completionist})'


def get_normalized(string_):
    string_ = string_.lower()
    return ''.join(e for e in string_ if e.isalnum())


def get_sortable_time(time):
    time = time.replace(u'\xbd', u'.5')
    if 'Mins' in time:
        time_mins = int(time.replace(' Mins', ''))
        return str(time_mins / 60.0)
    return time.replace(' Hours', '').replace(' Hour', '')


def print_marker(title, iteration):
    print('{} - {} ...'.format(iteration, title).ljust(50), end='')
    sys.stdout.flush()
    time.sleep(1)


def query_howlongtobeat(title):
    url = (
        'https://howlongtobeat.com/search_results?page=1'
    )
    # headers = {
    #     'referer': 'http://www.howlongtobeat.com/',
    # }
    # params = {
    #     'queryString':
    #     't': 'games',
    #     'page': '1',
    #     'sorthead': '',
    #     'sortd': 'Normal',
    #     'plat': '',
    #     'detail': '0',
    # }
    payload = {
        'queryString': title,
        't': games,
        'sorthead': 'popular',
        'sortd': 'Normal Order',
        'plat': '',
        'length_type': 'main',
        'length_min': '',
        'length_max': ''
    }
    return requests.post(url, data=payload)


def parse_tidbits(game, game_detail):
    tidbits = game_detail.findAll(
        'div',
        attrs={'class': 'search_list_tidbit'}
    )
    if len(tidbits) == 6:
        game.main = get_sortable_time(tidbits[1].text[:-1])
        game.main_extra = get_sortable_time(tidbits[3].text[:-1])
        game.completionist = get_sortable_time(tidbits[5].text[:-1])
    elif len(tidbits) == 2:
        game.main = get_sortable_time(tidbits[1].text)
    return


def parse_howlongtobeat(response, game, translated_title):
    soup = BeautifulSoup(response.text, features='html.parser')
    game_details = soup.findAll('div', attrs={'class': 'search_list_details'})
    for game_detail in game_details:
        links = game_detail.findAll('a')
        for link in links:
            if get_normalized(translated_title) == get_normalized(link.text):
                print(link.text)
                parse_tidbits(game, game_detail)
                return
    print('Not Found')
    return ['Not found', '', '', '']


def format_title(title_text):
    return re.sub(r'[^\x00-\x7F]', '', title_text).strip()


skipped_games = [
    'Awesomenauts',
    'Dota 2'
]


def parse_games(soup):
    games = []
    parsed_titles = soup.findAll('h3', attrs={'class': 'game-db-title'})
    for title_html in parsed_titles:
        game = Game()

        formatted_title = format_title(title_html.text)

        if formatted_title in skipped_games:
            continue

        game.title = title_translate(formatted_title, metacritic_title_lookup)

        parent = title_html.parent.parent

        # percentage = parent.find('span', attrs={'class': 'percent-complete'})
        percentage_parent = parent.find('div', attrs={'class': 'progress-bar'})
        if percentage_parent is None:
            game.percentage = ''
        else:
            percentage_span = percentage_parent.find('span')
            game.percentage = percentage_span.text[:-1] if percentage_span else ''

        platform = parent.find('div', attrs={'class': 'inline-pf'})
        game.platform = platform.text if platform else ''

        if game.platform not in ('Xbox 360', 'Xbox One', 'Vita'):
            games.append(game)
    return games


def parse_percentages(soup):
    parsed_percentages = soup.findAll(
        'span', attrs={'class': 'percent-complete'})
    percentages = []
    for percentage in parsed_percentages:
        percentages.append(percentage.text[:-1])
    return percentages


def title_translate(title, title_lookup):
    if title not in title_lookup:
        return title
    new_title = title_lookup[title]
    print('{} --> {}'.format(title, new_title))
    return new_title


how_long_title_lookup = {
    'Shadow of the Colossus': 'Shadow of the Colossus (2018)'
}
# how_long_title_lookup = {
#     'LEGO Rock Band': 'Lego Rock Band (Console)',
#     'Mortal Kombat': 'Mortal Kombat (2011)',
#     'Microsoft Solitaire': 'Microsoft Solitaire Collection',
#     'Batman:Arkham City PC': 'Batman: Arkham City',
#     'SUPER STREETFIGHTER IV': 'Super Street Fighter IV',
#     'SuperStreetFighter2THD': 'Super Street Fighter II Turbo HD Remix',
#     'Monkey Island 2: SE': "Monkey Island 2: LeChuck's Revenge",
#     'Monkey Island: SE': 'The Secret of Monkey Island',
#     'Call of Duty 4': 'Call of Duty 4: Modern Warfare',
#     "TC's RainbowSix Vegas": "Tom Clancy's Rainbow Six: Vegas",
#     'LEGO Star Wars II': 'Lego Star Wars II: The Original Trilogy',
#     'GTA IV': 'Grand Theft Auto IV',
#     'Castlevania: SOTN': 'Castlevania: Symphony of the Night',
#     'Sonic The Hedgehog 2': 'Sonic the Hedgehog 2 (16-bit)',
#     'TMNT 1989 Arcade': 'Teenage Mutant Ninja Turtles II: The Arcade Game',
#     'ORION: Dino Beatdown': 'ORION: Dino Horde',
#     'Crysis 2 Maximum Edition': 'Crysis 2',
#     'BIT.TRIP Presents... Runner2: Future Legend of Rhythm Alien': (
#         'Bit.Trip Presents Runner 2: Future Legend of Rhythm Alien'
#     ),
#     'Ys I': 'Ys I Chronicles Plus',
#     'Ys II': 'Ys II Chronicles Plus',
# }


def get_howlongtobeats(games):
    print('Retrieving HowLongToBeat.com data:')
    for (index, game) in enumerate(games):
        title = title_translate(game.title, how_long_title_lookup)
        print_marker(title, index)
        response = query_howlongtobeat(title)
        parse_howlongtobeat(response, game, title)
    return


metacritic_title_lookup = {
    'BioShock Remastered': 'BioShock'
}
# metacritic_title_lookup = {
#     'Batman:Arkham City PC': 'Batman: Arkham City',
#     'SuperStreetFighter2THD': 'Super Street Fighter II Turbo HD Remix',
#     'Monkey Island 2: SE': "Monkey Island 2 Special Edition: LeChuck's Revenge",
#     'Monkey Island: SE': 'The Secret of Monkey Island: Special Edition',
#     'Call of Duty 4': 'Call of Duty 4: Modern Warfare',
#     'Marvel vs Capcom 2': 'Marvel vs. Capcom 2',
#     "TC's RainbowSix Vegas": "Tom Clancy's Rainbow Six: Vegas",
#     'LEGO Star Wars II': 'Lego Star Wars II: The Original Trilogy',
#     'GTA IV': 'Grand Theft Auto IV',
#     'Castlevania: SOTN': 'Castlevania: Symphony of the Night',
#     'TMNT 1989 Arcade': 'Teenage Mutant Ninja Turtles (2007)',
#     'ORION: Dino Beatdown': 'ORION: Dino Horde',
#     'Crysis 2 Maximum Edition': 'Crysis 2',
#     'BIT.TRIP Presents... Runner2: Future Legend of Rhythm Alien': (
#         'Bit.Trip Presents...Runner2: Future Legend of Rhythm Alien'
#     ),
#     'Ys I': 'Ys I & II Chronicles',
#     'Ys II': 'Ys I & II Chronicles',
# }

PLATFORM_MAPPING = {
    'PS3': 'playstation-3',
    'PS4': 'playstation-4',
    'Xbox 360': 'xbox-360',
    'Steam': 'pc',
    'Xbox One': 'xbox-one',
    'Vita': 'playstation-vita'
}


def get_scores(games):
    print('Retrieving scores:')
    headers = {
        'x-rapidapi-host': "chicken-coop.p.rapidapi.com",
        'x-rapidapi-key': os.getenv('RAPID_API_KEY')
    }
    for game in games:
        url = f'https://chicken-coop.p.rapidapi.com/games/{game.title}'
        params = {'platform': PLATFORM_MAPPING[game.platform]}
        response = requests.get(url, headers=headers, params=params, timeout=20)
        response_json = json.loads(response.text)

        result_ = response_json['result']
        game.score = None if result_ == 'No result' else result_['score']
        pprint(str(game))
    return


if __name__ == '__main__':
    print('Getting exophase')
    url = 'http://profiles.exophase.com/robotherapy/'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, features="html.parser")
    games = parse_games(soup)
    print('Number of Games: {}'.format(len(games)))
    print('Getting scores')
    get_scores(games)
    print('Getting howlongtobeats')
    get_howlongtobeats(games)

    # with open('games.csv', 'w') as file_:
    #     csv_file = csv.writer(file_)
    #     csv_file.writerow([
    #         'Name',
    #         'Completion Percentage',
    #         'Critics Score',
    #         'Main Time',
    #         'Main + Extras Time',
    #         'Completionist Time'
    #     ])
    #     for game in games:
    #         csv_file.writerow([
    #             game.title,
    #             game.percentage,
    #             game.score,
    #             game.main,
    #             game.main_extra,
    #             game.completionist
    #         ])

    # games = [
    #     Game(title='Bastion', score=86, main=7),
    #     Game(title='Halo 4', score=87, main=8),
    #     Game(title='Bastion', score=86, main=7),
    #     Game(title='The Jackbox Party Pack 2', score=0, main=0),
    #     Game(title='Red Dead Redemption 2', score=94, main=47)
    # ]
    games = [game for game in games if game.score not in [None, 0]]

    scores = [game.score for game in games]
    y = [(0 if game.main is None else Decimal(game.main)) for game in games]

    plt.figure(num=None, figsize=(10, 10), dpi=80, facecolor='w', edgecolor='k')
    plt.scatter(scores, y)
    plt.xlabel('Score')
    plt.ylabel('Main hours')

    for i, game in enumerate(games):
        plt.annotate(game.title, (scores[i], y[i]))

    plt.show()


    # drive_upload.run()
