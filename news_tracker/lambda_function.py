from urllib import request
from urllib.request import urlopen
import urllib.error
import re
import os
from bs4 import BeautifulSoup
import datetime
import pymongo


def lambda_handler(event, context):
    # TODO implement
    db_string = os.environ["DB_URI"]
    client = pymongo.MongoClient(db_string)
    db = client.brasileirao
    collection = db["news_tracker"]
    news_date = datetime.datetime.today().strftime('%Y-%m-%d-%H:%M:%S')
    print("Running...")
    url = ("https://www.globo.com/")
    try:
        html = urlopen(url)
    except urllib.error.HTTPError as e:
        return e
    soup = BeautifulSoup(html, 'html.parser')
    type(soup)
    all_links = soup.find_all(href=re.compile(
        "https://ge.globo.com/futebol/times/"))
    for link in all_links:
        news_url = link.get("href")
        team = link.get("href").split("/")[5]
        existing_news = collection.find_one({"news_url": {"$eq": news_url}})
        if not(existing_news):
            collection.insert_one(
                {"team": team, "news_date": news_date, "news_url": news_url})
            print(f' {team} has been added to the database')
        else:
            print(f' Skipped teams: {team}')
