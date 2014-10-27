from __future__ import print_function

import csv
import json
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

def parse_titles_and_percentages(soup):
    titles = []
    percentages = []
    parsed_titles = soup.findAll('h3', attrs={'class': 'game-db-title'})
    for title_html in parsed_titles:
        title_formatted = format_title(title_html.text)
        titles.append(title_formatted)
        parent = title_html.parent.parent
        percentage = parent.find('span', attrs={'class': 'percent-complete'})
        if percentage:
            percentages.append(percentage.text[:-1])
        else:
            percentages.append('')
    return titles, percentages


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
def get_howlongtobeats(titles):
    print('Number of games from exophase: {}'.format(len(titles)))
    print('Retrieving HowLongToBeat.com data:')
    long_to_beats = []
    i = 1
    for title in titles:
        title = title_translate(title, how_long_title_lookup)
        print_marker(title, i)
        response = query_howlongtobeat(title)
        parsed_data = parse_howlongtobeat(response, title)
        long_to_beats.append(parsed_data)
        i += 1
    return long_to_beats


def parse_score_json(response_json, title):
    print("""\
Looking For:
    {}""".format(title))
    for response in response_json['results']:
        # print(response)
        response_title = response['name']
        if get_normalized(title) == get_normalized(response_title):
            platform = response['platform']
            if platform != 'iOS':
                score = response['score']
                print("""\
Found:
    {response_title}
    Platform: {platform}
    Score: {score}
""".format(**locals()))
                return score
    print('Not Found\n')
    return 'Not Found'


metacritic_title_lookup = {
    'Batman:Arkham City PC': 'Batman: Arkham City',
    'SuperStreetFighter2THD': 'Super Street Fighter II Turbo HD Remix',
    'Monkey Island 2: SE': "Monkey Island 2 Special Edition: LeChuck's Revenge",
    'Monkey Island: SE': 'The Secret of Monkey Island: Special Edition',
    'Call of Duty 4': 'Call of Duty 4: Modern Warfare',
    'Marvel vs Capcom 2': 'Marvel vs. Capcom 2',
    "TC's RainbowSix Vegas": "Tom Clancy's Rainbow Six: Vegas",
    'LEGO Star Wars II': 'Lego Star Wars II: The Original Trilogy',
    'GTA IV': 'Grand Theft Auto IV',
    'Castlevania: SOTN': 'Castlevania: Symphony of the Night',
    'TMNT 1989 Arcade': 'Teenage Mutant Ninja Turtles (2007)',
    'ORION: Dino Beatdown': 'ORION: Dino Horde',
    'Crysis 2 Maximum Edition': 'Crysis 2',
    'BIT.TRIP Presents... Runner2: Future Legend of Rhythm Alien': (
        'Bit.Trip Presents...Runner2: Future Legend of Rhythm Alien'
    ),
    'Ys I': 'Ys I & II Chronicles',
    'Ys II': 'Ys I & II Chronicles',
}
def get_scores(titles):
    print('Retrieving scores:')
    url = 'https://byroredux-metacritic.p.mashape.com/search/game'
    headers = {
        'X-Mashape-Key': os.getenv('METACRITIC_API_KEY'),
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    scores = []
    for title in titles:
        title = title_translate(title, metacritic_title_lookup)
        params = {
            'retry': 4,
            'title': title,
        }
        try:
            response = requests.post(url, headers=headers, params=params, timeout=20)
        except:
            try:
                response = requests.post(url, headers=headers, params=params, timeout=20)
            except:
                print('Timeout on {}'.format(title))
                scores.append('Timeout')
                continue
        response_json = json.loads(response.text)
        scores.append(parse_score_json(response_json, title))
    return scores


if __name__ == '__main__':
    url = 'http://profiles.exophase.com/robotherapy/'
    response = requests.get(url)
    soup = BeautifulSoup(response.text)
    # titles = parse_titles(soup)
    titles, percentages = parse_titles_and_percentages(soup)
    print('Titles: {}'.format(len(titles)))
    print('Percentages: {}'.format(len(percentages)))
    scores = get_scores(titles)
    print('Scores: {}'.format(len(scores)))
    long_to_beats = get_howlongtobeats(titles)

    gameslist = [list(a) for a in zip(titles, percentages, scores)]
    for i in range(0, len(gameslist)):
        gameslist[i].extend(long_to_beats[i])

    with open('games.csv', 'w') as file_:
        csv_file = csv.writer(file_)
        csv_file.writerow([
            'Name',
            'Completion Percentage',
            'Critics Score',
            'Main Time',
            'Main + Extras Time',
            'Completionist Time',
            'Combined Time',
        ])
        for game in gameslist:
            csv_file.writerow(game)

    drive_upload.run()
