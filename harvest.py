import os

import pandas as pd
import seaborn as sns
from typing import *
from datetime import datetime
from dateutil.parser import parse
import requests

BOARD_ID = "5a8606d16fa75ce590950255"
TRELLO_URL = "https://api.trello.com/1"

TRELLO_KEY = os.getenv("TRELLO_KEY")
TRELLO_TOKEN = os.getenv("TRELLO_TOKEN")

assert TRELLO_KEY and TRELLO_TOKEN, "Missing Trello credentials"

query = {"key": TRELLO_KEY, "token": TRELLO_TOKEN}

clean_list = lambda l: list(map(str.strip, l))

genre_list = lambda l: sorted(list(map(str.lower, clean_list(l))))

def year_from_name(list_name: str):
    s = clean_list(list_name.split(" "))
    return s[1]


typo_authors = {
    "Jo Nesbø": "Jo Nesbo",
    "A.G Riddle": "A.G. Riddle",
    "HG Wells": "H.G. Wells",
    "H G Wells": "H.G. Wells",
    "Brooke Mcalary": "Brooke McAlary",
}

typo_titles = {
    "The Subtle Art of Not Giving a F#ck": "The Subtle Art of Not Giving a F*ck"
}


def title_and_author(card_name: str):
    s = clean_list(card_name.split(" - "))
    author = s.pop(-1)
    title = "-".join(s)
    return {
        "title": typo_titles.get(title, title),
        "author": typo_authors.get(author, author),
    }


ratings = {"Bad": 1, "Ok": 2, "Good": 3, "Excellent": 4}


def labels(card_labels: List[str]):
    return {"rating": sum([ratings[c["name"]] for c in card_labels]) / len(card_labels)}


def date_and_genres(description: str):
    if not description:
        return {"date": None, "genres": None}

    split_fields = description.split("\n")
    date = split_fields[0]
    genres = split_fields[1]
    return {"date": parse(date), "genres": genre_list(genres.split(","))}


def create_df_from(raw):

    books = [
        {
            **title_and_author(b["name"]),
            **labels(b["labels"]),
            **date_and_genres(b["desc"]),
        }
        for b in raw
    ]
    return pd.DataFrame.from_dict(sorted(books, key=lambda d: d["date"]))


if __name__ == "__main__":
    response = requests.get(f"{TRELLO_URL}/boards/{BOARD_ID}/lists", params=query)

    bob_lists = [
        (d["id"], year_from_name(d["name"]))
        for d in response.json()
        if d["name"].lower().startswith("bob")
    ]
    print(f"Got {len(bob_lists)} Book of Books Lists")
    raw_books = []
    books_per_year = {}
    for bob_list, year in bob_lists:
        response = requests.get(f"{TRELLO_URL}/lists/{bob_list}/cards", params=query)
        all_books = [d for d in response.json()]
        print(f"Got {len(all_books)} books for {year}")
        raw_books.extend(all_books)
        books_per_year[year] = len(all_books)

    print("Creating data frames and saving locally")
    df = create_df_from(raw_books)
    df.to_csv("books.csv")

    bpy = pd.DataFrame.from_dict(books_per_year, orient="index", columns=['total'])
    bpy.to_csv("books_per_year.csv")

    # pd.DataFrame.from_dict(raw_books).to_csv("raw_books.csv")
