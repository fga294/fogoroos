import datetime
import os
import re
import sys
from urllib.request import urlopen

import pymysql
from bs4 import BeautifulSoup


def lambda_handler(event, context):
    news_date = datetime.datetime.today().strftime('%Y-%m-%d-%H:%M:%S')
    url = ("https://www.globo.com/")
    html = urlopen(url)
    soup = BeautifulSoup(html, 'html.parser')
    type(soup)
    all_links = soup.find_all(href=re.compile(
        "https://ge.globo.com/futebol/times/"))

    try:
        conn = pymysql.connect(
            user=os.environ["DB_USERNAME"],
            password=os.environ["DB_SECRET"],
            host=os.environ["DB_HOST"],
            port=3306,
            database=os.environ["DATABASE"]

        )
    except pymysql.Error as e:
        print(f"Error connecting to FogoroosDB Platform: {e}")
        sys.exit(1)

    cur = conn.cursor()

    for link in all_links:
        news_url = link.get("href")
        team = link.get("href").split("/")[5]
        cur.execute(
            "SELECT news_url FROM news_tracker WHERE news_url=%s", (news_url,))
        existing_record = cur.fetchone()
        if existing_record is not None:
            print(f' News already captured: {team} | {news_date}')
        else:
            try:
                cur.execute(
                    "INSERT INTO news_tracker (team, news_date, news_url) VALUES (%s, %s, %s)", (team, news_date, news_url))
            except pymysql.Error as e:
                print(f"Error adding team: {e}")

            conn.commit()
            print(f"Last Inserted news: {team} | {news_date}")
        conn.close()
