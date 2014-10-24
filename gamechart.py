from __future__ import print_function

import csv
import os
import re
import sys
import time

import requests
from bs4 import BeautifulSoup

import drive_upload


def get_normalized(string_):
    string_ = string_.lower()
    return ''.join(e for e in string_ if e.isalnum())


def get_sortable_time(time):
    time = time.replace(u'\xbd', u'.5')
    if 'Mins' in time:
        time_mins = int(time.replace(' Mins', ''))
        return str(time_mins/60.0)
    return time.replace(' Hours', '').replace(' Hour', '')


def print_marker(title, iteration):
    print('{} - {} ...'.format(iteration, title).ljust(50), end='')
    sys.stdout.flush()
    time.sleep(1)


def query_howlongtobeat(title):
    url = (
        'http://www.howlongtobeat.com/search_main.php?'
        't=games&page=1&sorthead=&sortd=Normal&plat=&detail=0'
    )
    headers = {
        'referer': 'http://www.howlongtobeat.com/',
    }
    params = {
        't': 'games',
        'page': '1',
        'sorthead': '',
        'sortd': 'Normal',
        'plat': '',
        'detail': '0',
    }
    payload = {'queryString': title}
    return requests.post(url, data=payload, headers=headers, params=params)


def parse_tidbits(game_detail):
    tidbits = game_detail.findAll(
        'div',
        attrs={'class': 'gamelist_tidbit'}
    )
    main = ''
    main_extra = ''
    completion = ''
    combined = ''
    if len(tidbits) == 8:
        main        = get_sortable_time(tidbits[1].text)
        main_extra  = get_sortable_time(tidbits[3].text)
        completion  = get_sortable_time(tidbits[5].text)
        combined    = get_sortable_time(tidbits[7].text)
    elif len(tidbits) == 2:
        main        = get_sortable_time(tidbits[1].text)
        combined    = main
    return [main, main_extra, completion, combined]


def parse_howlongtobeat(response, title):
    soup = BeautifulSoup(response.text)
    game_details = soup.findAll('div', attrs={'class': 'gamelist_details'})
    for game_detail in game_details:
        links = game_detail.findAll('a')
        for link in links:
            if get_normalized(title) == get_normalized(link.text):
                print(link.text)
                return parse_tidbits(game_detail)
    print('Not Found')
    return ['Not found', '', '', '']


def format_title(title_text):
    return re.sub(r'[^\x00-\x7F]', '', title_text).strip()

title_lookup = {
    'LEGO Rock Band': 'Lego Rock Band (Console)',
    'Mortal Kombat': 'Mortal Kombat (2011)',
    'Microsoft Solitaire': 'Microsoft Solitaire Collection',
    'Batman:Arkham City PC': 'Batman: Arkham City',
    'SUPER STREETFIGHTER IV': 'Super Street Fighter IV',
    'SuperStreetFighter2THD': 'Super Street Fighter II Turbo HD Remix',
    'Monkey Island 2: SE': "Monkey Island 2: LeChuck's Revenge",
    'Monkey Island: SE': 'The Secret of Monkey Island',
    'Call of Duty 4': 'Call of Duty 4: Modern Warfare',
    "TC's RainbowSix Vegas": "Tom Clancy's Rainbow Six: Vegas",
    'LEGO Star Wars II': 'Lego Star Wars II: The Original Trilogy',
    'GTA IV': 'Grand Theft Auto IV',
    'Castlevania: SOTN': 'Castlevania: Symphony of the Night',
    'Sonic The Hedgehog 2': 'Sonic the Hedgehog 2 (16-bit)',
    'TMNT 1989 Arcade': 'Teenage Mutant Ninja Turtles II: The Arcade Game',
    'ORION: Dino Beatdown': 'ORION: Dino Horde',
    'Crysis 2 Maximum Edition': 'Crysis 2',
    'BIT.TRIP Presents... Runner2: Future Legend of Rhythm Alien': (
        'Bit.Trip Presents Runner 2: Future Legend of Rhythm Alien'
    ),
    'Ys I': 'Ys I Chronicles Plus',
    'Ys II': 'Ys II Chronicles Plus',
}
def parse_titles():
    titles = []
    parsed_titles = soup.findAll('h3', attrs={'class': 'game-db-title'})
    print('Alterations:')
    for title_html in parsed_titles:
        title = format_title(title_html.text)
        if title in title_lookup:
            new_title = title_lookup[title]
            print('{} --> {}'.format(title, new_title))
            title = new_title
        titles.append(title)
    print('')
    return titles


def parse_percentages():
    parsed_percentages = soup.findAll(
        'span', attrs={'class': 'percent-complete'})
    percentages = []
    for percentage in parsed_percentages:
        percentages.append(percentage.text[:-1])
    return percentages


def get_howlongtobeats(titles):
    print('Number of games from exophase: {}'.format(len(titles)))
    print('Retrieving HowLongToBeat.com data:')
    long_to_beats = []
    i = 1
    for title in titles:
        print_marker(title, i)
        response = query_howlongtobeat(title)
        parsed_data = parse_howlongtobeat(response, title)
        long_to_beats.append(parsed_data)
        i += 1
    return long_to_beats


def get_scores(titles):
    url = 'https://byroredux-metacritic.p.mashape.com/search/game'
    headers = {
        'X-Mashape-Key': os.getenv('METACRITIC_API_KEY'),
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    critic_scores = []
    user_scores = []
    for title in titles:
        params = {
            'retry': 4,
            'title': title,
        }
        import pdb; pdb.set_trace()
        response = requests.post(url, headers=headers, params=params)
        pass


if __name__ == '__main__':
    url = 'http://profiles.exophase.com/robotherapy/'
    response = requests.get(url)
    soup = BeautifulSoup(response.text)
    titles = parse_titles()
    percentages = parse_percentages()
    #long_to_beats = get_howlongtobeats(titles)
    scores = get_scores(titles)

    gameslist = [list(a) for a in zip(titles, percentages)]
    for i in range(0, len(gameslist)):
        gameslist[i].extend(long_to_beats[i])

    sorted_gameslist = sorted(gameslist, key=lambda x: int(x[1]), reverse=True)

    with open('games.csv', 'w') as file_:
        csv_file = csv.writer(file_)
        csv_file.writerow([
            'Name',
            'Completion Percentage',
            'Main Time',
            'Main + Extras Time',
            'Completionist Time',
            'Combined Time',
        ])
        for game in sorted_gameslist:
            csv_file.writerow(game)

    drive_upload.run()
