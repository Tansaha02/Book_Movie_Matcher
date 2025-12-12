"""
Book–Movie Matcher Project
--------------------------
This program suggests books based on movies a user likes. It checks a local CSV
dataset first, and if fewer than four books are found, it tries to pull a couple
of suggestions from Goodreads. Search activity is stored in an SQLite database,
and a small analysis summary is shown at the end of the session.

Key concepts used:
- OOP (Movie and Book classes)
- CSV reading
- Lists & dictionaries
- Regular expressions for input cleaning
- SQLite for saving search history
- Web scraping (BeautifulSoup)
- Basic data analysis with Counter
"""

import csv
import re
import sqlite3
import requests
import os
from collections import Counter
from bs4 import BeautifulSoup


#Models

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
        self.source = source   # "csv" or "web"

    def short(self):
        """Return a shorter version of long descriptions."""
        return self.description[:120] + "..." if len(self.description) > 120 else self.description


#here Regex is used in input cleaning

def tidy(txt):
    """Normalize spacing and remove unwanted characters."""
    txt = txt.strip()
    txt = re.sub(r"\s+", " ", txt)
    txt = re.sub(r"[^A-Za-z0-9\s\-\'\"!?.,]", "", txt)
    return txt


def valid(txt):
    """Check if title contains only allowed characters."""
    return bool(re.match(r"^[A-Za-z0-9\s\-\'\"!?.,]+$", txt))


#Here CSV File is loaded
def load_csv(file="books_movies.csv"):
    """Load dataset into dictionary {movie_title: [Book, Book, ...]}."""

    data = {}

    # Always load CSV from the same folder as this script
    dir = os.path.dirname(os.path.abspath(__file__))
    f_path = os.path.join(dir, file)

    try:
        with open(full_path, newline="", encoding="utf-8") as f:
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
        print(f"\nCSV file not found at: {f_path}\n")

    return data


def from_local(movie, dataset, minimum=4):
    """Return up to 'minimum' books from CSV for the requested movie."""
    return dataset.get(movie.lower(), [])[:minimum]


#   In this Function Data is fetch from web using bs4 

def fetch_data_from_web(movie, genre, count=5):
    """Fetch additional book suggestions from Goodreads if CSV suggestions are fewer."""
    url = f"https://www.goodreads.com/search?q={movie.replace(' ', '+')}"
    collected = []

    try:
        pg = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=7)
        soup = BeautifulSoup(pg.text, "html.parser")
    except:
        return []   # No internet / website blocked it will return this

    links = soup.select("a.bookTitle")[:8]   # get several to filter quality

    for ln in links:
        title = ln.get_text(strip=True)

        # it will ignore results unrelated to books
        skip_words = ["colour", "coloring", "diary", "activity", "guide"]
        if any(w in title.lower() for w in skip_words):
            continue

        #it is trying to locate the author
        row = ln.find_parent("tr")
        author = "Unknown"

        if row:
            candidate = row.select_one("span.authorName span") or row.select_one("a.authorName span")
            if candidate:
                author = candidate.get_text(strip=True)

        if author == "Unknown":
            continue

        collected.append(Book(title, author, genre, "Found via Goodreads lookup", "web"))
        if len(collected) >= count:
            break

    return collected


#DB_Setup

def db_setup(db="project.db"):
    """Create database tables if they don't exist."""
    con = sqlite3.connect(db)
    cur = con.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS history(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT, movie TEXT, genre TEXT,
        time TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS books(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sid INTEGER,
        title TEXT, author TEXT, source TEXT)
    """)

    con.commit()
    con.close()


def save(user, movie, book_list, db="project.db"):
    """Save search entry and its corresponding book results."""
    con = sqlite3.connect(db)
    cur = con.cursor()

   
    db_setup(db)

    cur.execute("INSERT INTO history(user,movie,genre) VALUES(?,?,?)",
                (user, movie.title, movie.genre))
    sid = cur.lastrowid

    for b in book_list:
        cur.execute("INSERT INTO books(sid,title,author,source) VALUES (?,?,?,?)",
                    (sid, b.title, b.author, b.source))

    con.commit()
    con.close()


def show_records(db="project.db"):
    """Display past search history from database."""
    con = sqlite3.connect(db)
    cur = con.cursor()

    print("\n========= Saved Search History =========\n")

    cur.execute("SELECT id,user,movie,genre,time FROM history")
    rows = cur.fetchall()

    if not rows:
        print("No past searches saved.\n")
        return

    for sid, user, movie, genre, t in rows:
        print(f"{sid}) {user} searched '{movie}' ({genre}) on {t}")
        cur.execute("SELECT title,author,source FROM books WHERE sid=?", (sid,))
        for bk, auth, src in cur.fetchall():
            print(f"   → {bk} - {auth} [{src}]")
        print("---------------------------------------")

    con.close()


#Data analysis is done here

def analysis_of_data(data):
    """Show simple statistics based on the session results."""
    if not data:
        print("\nNo session statistics to show.\n")
        return

    genre_freq = Counter(m.genre for m, _ in data)
    author_freq = Counter(b.author for _, lst in data for b in lst)

    print("\n========== SESSION ANALYSIS ==========")
    print("\nGenres searched this session:")
    for g, c in genre_freq.items():
        print(f" {g}: {c} time(s)")

    print("\nMost suggested authors:")
    for a, c in author_freq.most_common(3):
        print(f" {a}: {c}")
    print("======================================\n")


#Main block
def main():

    db_setup()
    dataset = load_csv()

    print("\n------ BOOK SUGGESTION SYSTEM ------")

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

    user = input("\nEnter your name: ").strip() or "Guest"
    session_memory = []

    while True:
        raw = input("\nMovie Name (q to quit): ")

        if raw.lower() == "q":
            break

        cleaned = tidy(raw)
        if not valid(cleaned):
            print("Please avoid unsupported special characters.")
            continue

        genre = input("Movie Genre (optional): ").strip() or "Unknown"
        movie_obj = Movie(cleaned, genre)

        recs = from_local(movie_obj.title, dataset)

        if len(recs) < 4:
            recs += fetch_data_from_web(movie_obj.title, genre, count=2)

        if not recs:
            print("No suggestions found.\n")
            continue

        print("\n--- Recommended Books ---\n")
        for i, b in enumerate(recs, start=1):
            print(f"{i}. {b.title} | {b.author} [{b.source}]")
            print("    ", b.short())

        save(user, movie_obj, recs)
        session_memory.append((movie_obj, recs))

    analysis_of_data(session_memory)
    print("\nThank you for using the system!\n")


if __name__ == "__main__":
    main()
