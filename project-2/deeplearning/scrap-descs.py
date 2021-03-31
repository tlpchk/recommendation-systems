#!/usr/bin/env python3
#
# IMDb movie description straper for movielens dataset 
#

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

import sys
import csv
import json
import time

HOST = 'http://www.imdb.com'
DELAY_IN_SECONDS = 0.1
LANG_HEADERS = {'Accept-Language': 'en'}


def parse_movie_list(html):
    dom = BeautifulSoup(html, 'html.parser')
    try: 
        href = dom.find('table', class_='findList').tr.a['href']
        path_components = href[1:].split('/')[:2]
        if len(path_components) == 2:
            imdb_id = path_components[1]
            imdb_url = '/'.join([HOST, *path_components])
            return (imdb_id, imdb_url)
        else:
            print("Error. Cannot parse href")
            return None
    except AttributeError as e:
        return None
    

def parse_movie_description(html):
    dom = BeautifulSoup(html, 'html.parser')
    try:
        storyline_container = dom.find(id='titleStoryLine')
        paragraph = storyline_container.div.p.span
        descritpion_text = paragraph.get_text().strip()
        return descritpion_text
    except AttributeError as e:
        return None 


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <path-to-u-items> <output-file>")
        exit(1)

    csv_fp = sys.argv[1]
    output_json_fp = sys.argv[2]

    output_dicts = []
    with open(csv_fp, 'r') as fi:
        reader = csv.DictReader(fi, delimiter='|')
        for row in tqdm(list(reader)):
            identifier = row['id']
            title = row['title']
            search_url = HOST + '/find?q=' + requests.utils.quote(title)

            search_response = requests.get(search_url, headers=LANG_HEADERS)
            result = parse_movie_list(search_response.text)
            if result is None:
                print(f'Could not parse movie with id: {identifier}, title: {title}')
                continue

            imdb_id, imdb_url = result
            detail_response = requests.get(imdb_url, headers=LANG_HEADERS)
            description = parse_movie_description(detail_response.text)
            if description is None:
                print(f'Could not parse movie description with id: {identifier}, title: {title}')
                continue

            row_copy = row.copy()
            row_copy['IMDb id'] = imdb_id
            row_copy['IMDb URL'] = imdb_url
            row_copy['storyline'] = description
            output_dicts.append(row_copy)
            
            time.sleep(DELAY_IN_SECONDS)

    with open(output_json_fp, 'w') as fo:
        json.dump(output_dicts, fo)
        print(f"Done. Output dumped into {output_json_fp}")