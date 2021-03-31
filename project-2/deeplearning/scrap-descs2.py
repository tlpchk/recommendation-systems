#!/usr/bin/env python3
#
# Alternative version of IMDb movie description straper for movielens dataset.
# It's using links.csv provided by movielens:latest dataset
#
# This version is also using asyncio to speed up information retrieval.
#

from bs4 import BeautifulSoup
from tqdm import tqdm
from aiohttp import ClientSession

import asyncio
import sys
import csv
import json
import time

HOST = 'http://www.imdb.com'
LANG_HEADERS = {'Accept-Language': 'en'}
# global semaphore to prevent IP blocks
semaphore = asyncio.Semaphore(10)

def parse_movie_description(html):
    dom = BeautifulSoup(html, 'html.parser')
    try:
        storyline_container = dom.find(id='titleStoryLine')
        paragraph = storyline_container.div.p.span
        descritpion_text = paragraph.get_text().strip()
        return descritpion_text
    except AttributeError as e:
        return None    


async def fetch(url, session):
    async with semaphore:
        async with session.get(url) as response:
            html = await response.read()
            description = parse_movie_description(html)
            return description
    

async def download_and_parse(rows, limit, output_json_fp):
    tasks = []
    async with ClientSession(headers=LANG_HEADERS) as session:
        ids = []
        pbar = tqdm(total=min(limit, len(rows)))
        for row in rows[:limit]:
            movielens_id = row['movieId']
            imdb_id = row['imdbId']
            detail_url = HOST + '/title/tt' + imdb_id
            
            task = asyncio.ensure_future(fetch(detail_url, session))
            task.add_done_callback(lambda t: pbar.update(1))
            ids.append(movielens_id)
            tasks.append(task)
        descriptions = await asyncio.gather(*tasks)
        output_dict = {i: d for i, d in zip(ids, descriptions)}
        with open(output_json_fp, 'w') as fo:
            json.dump(output_dict, fo)
            print(f"Done. Output dumped into {output_json_fp}")


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <path-to-u-links> <output-file> <limit?>")
        exit(1)

    csv_fp = sys.argv[1]
    output_json_fp = sys.argv[2]
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else sys.maxsize
    
    rows = None
    with open(csv_fp, 'r') as fi:
        reader = csv.DictReader(fi, delimiter=',')
        rows = list(reader)
    
    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(download_and_parse(rows, limit, output_json_fp))
    loop.run_until_complete(future)
