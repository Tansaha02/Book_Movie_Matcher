"""
BOOK–MOVIE MATCHER (My Final Python Project)

Idea:
A user enters a movie they liked, and I try to recommend books related to it.
First I match from a CSV dataset. If book suggestions are too few,
I try to pull some from Goodreads using requests + bs4.
I also store every search into a local sqlite database,
and at the end of the program I generate a mini analysis report
showing genres and most suggested authors in this session.

Concepts Covered:
1) Python Basics
2) OOP (Movie + Book classes)
3) File Handling (CSV dataset)
4) Lists + Dictionaries (container usage)
5) Regex for cleaning movie input
6) SQLite (Database + SQL operations)
7) Web Scraping (BeautifulSoup)
8) Data Analysis Summary (Counter)
9) Testing Ready Functions
"""

import csv
import re
import sqlite3
import requests
from collections import Counter
from bs4 import BeautifulSoup


"""OOPS CLASSES"""

class Movie:
    def __init__(self, title, genre="Unknown"):
        self.title = title
        self.genre = genre


class Book:
    def __init__(self, title, author, genre, description, source):
        self.title = title
        self.author = author
        self.genre = genre
        self.description = description
        self.source = source    # "csv" or "web"

    def short(self):
        # It trims the long description for clean and smoooth display
        return self.description[:120] + "..." if len(self.description) > 120 else self.description


"""THIS FUNCTION CLEAN THE OUTPUT USING REGEX"""
def tidy(txt):
    txt = txt.strip()                            #  it removes left-right whitespace
    txt = re.sub(r"\s+", " ", txt)               # it compresses multiple spaces
    txt = re.sub(r"[^A-Za-z0-9\s\-\'\"!?.,]", "", txt)   # it manually allows characters only
    return txt


def valid(txt):
    return bool(re.match(r"^[A-Za-z0-9\s\-\'\"!?.,]+$", txt))


"""This function is loading the data from csv file"""

def load_csv(file="books_movies.csv"):
    data = {}
    try:
        with open(file, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                key = row["movie_title"].lower()
                data.setdefault(key, []).append(
                    Book(
                        row["book_title"],
                        row["book_author"],
                        row["book_genre"],
                        row["book_description"],
                        "csv"
                    )
                )
    except FileNotFoundError:
        print("\n CSV file is  missing.\n")
    return data


def from_local(movie, dataset, minimum=4):
    return dataset.get(movie.lower(), [])[:minimum]



"""this function is fetching data from web using beautifulsoup """

def fetch_data_from_web(movie, genre, count=2):
    """Pull book suggestions from Goodreads using search page scraping."""
    url = f"https://www.goodreads.com/search?q={movie.replace(' ', '+')}"
    collected = []

    try:
        pg = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=7)
        soup = BeautifulSoup(pg.text, "html.parser")
    except:
        return []     

    #   it is scrapping the book title
    links = soup.select("a.bookTitle")[:8]

    for ln in links:
        title = ln.get_text(strip=True)

        # It is filtering the junk results
        bad_words = ["colour", "coloring", "diary", "activity", "guide"]
        if any(b in title.lower() for b in bad_words):
            continue

        # It is fetching the authors name
        row = ln.find_parent("tr")
        author = "Unknown"

        if row:
            tag = row.select_one("span.authorName span") or row.select_one("a.authorName span")
            if tag:
                author = tag.get_text(strip=True)

        if author == "Unknown":     # If no author is found then it is skipping those records
            continue

        collected.append(Book(title, author, genre, "Found via Goodreads lookup", "web"))
        if len(collected) >= count:
            break

    return collected


"""This function is for SQLlite DB Setup"""

def db_setup(db="project.db"):
    connection = sqlite3.connect(db)
    con = connection.cursor()

    # search log
    con.execute("""
        CREATE TABLE IF NOT EXISTS history(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT, movie TEXT, genre TEXT,
        time TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
    """)

    # books returned in that search
    con.execute("""
        CREATE TABLE IF NOT EXISTS books(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sid INTEGER,
        title TEXT, author TEXT, source TEXT)
    """)

    connection.commit()
    connection.close()

"""This function is saving the record in database"""
def save(user, movie, book_list, db="project.db"):
    connnection = sqlite3.connect(db)
    con = connnection.cursor()

    con.execute("INSERT INTO history(user,movie,genre) VALUES(?,?,?)",
              (user, movie.title, movie.genre))
    sid = con.lastrowid

    for b in book_list:
        con.execute("INSERT INTO books(sid,title,author,source) VALUES (?,?,?,?)",
                  (sid, b.title, b.author, b.source))

    connnection.commit()
    connnection.close()


"""This function helps to show the Database search records"""

def show_records(db="project.db"):
    con = sqlite3.connect(db)
    c = con.cursor()

    print("\n========= Saved Search History =========\n")

    c.execute("SELECT id,user,movie,genre,time FROM history")
    history = c.fetchall()

    if not history:
        print("No past searches saved.\n")
        return

    for sid, user, movie, genre, t in history:
        print(f"{sid}) {user} searched '{movie}' ({genre}) on {t}")
        c.execute("SELECT title,author,source FROM books WHERE sid=?", (sid,))
        for t2, a2, src in c.fetchall():
            print(f"   ↳ {t2} - {a2} [{src}]")
        print("---------------------------------------")

    con.close()


""""This function helps to analyse the data which is previously stored"""

def analysis_of_data(data):
    if not data:
        print("\nNo of session statistics to show.\n")
        return

    g = Counter(obj.genre for obj, _ in data)
    a = Counter(b.author for _, lst in data for b in lst)

    print("\n========== SESSION ANALYSIS ==========")
    print("\nGenres are searched in this session:")
    for genre, count in g.items():
        print(f" {genre}: {count} time(s)")

    print("\nMost frequent authors are suggested:")
    for auth, count in a.most_common(3):
        print(f" {auth}: {count}")   
    print("======================================\n")


"""The main module where all the procedures are maintaned"""
def main():

    db_setup()
    dataset = load_csv()

    print("\n------ BOOK SUGGESTION IS GIVEN BASED ON MOVIES ------")

    while True:
        print("\n1) Recommend Books")
        print("2) View Search History")
        print("3) Exit\n")

        choice = input("Select an option: ")

        if choice == "1":
            break
        elif choice == "2":
            show_records()
        elif choice == "3":
            print("\nClosing Program...\n")
            return
        else:
            print("Invalid choice, try again.")

    user = input("\nEnter your Name: ").strip() or "Guest"

    session_memory = []     #This storing the history to analysis the data at the end

    while True:
        raw = input("\nMovie Name (q to quit): ")

        if raw.lower() == "q":
            break

        cleaned = tidy(raw)

        if not valid(cleaned):
            print(" Please avoid symbols and special characters except alphabets, numbers & ,.!?'")
            continue

        genre = input("Movie Genre (optional): ").strip() or "Unknown"

        m_obj = Movie(cleaned, genre)

        # source1 = CSV first
        recs = from_local(m_obj.title, dataset)

        # if less than 4 books → pull some data fro
        # m the web
        if len(recs) < 4:
            recs += fetch_data_from_web(m_obj.title, genre, count=2)

        if not recs:
            print("No suggestions are found anywhere.\n")
            continue

        print("\n--- Recommended Books ---\n")
        for i, b in enumerate(recs, 1):
            print(f"{i}. {b.title}  | {b.author}  [{b.source}]")
            print("    ", b.short())

        save(user, m_obj, recs)
        session_memory.append((m_obj, recs))

    analysis_of_data(session_memory)
    print("\nThank you for using the program!\n")


if __name__ == "__main__":
    main()
