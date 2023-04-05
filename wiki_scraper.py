import os
import requests
import sys

from bs4 import BeautifulSoup

from utils.content_scraper import get_content
from utils.infobox_scraper import get_infobox


OSRS_WIKI_URL_BASE = "https://oldschool.runescape.wiki"
SLUGS_DIR = "slugs/"
SLUGS_DEV_FILE = "test_slugs.txt"
SUMMARIES_DIR = "summaries/"
# This is just for dev purposes. It allows for only scraping specific
# categories.
SCRAPE_CATEGORIES = [
    "A Night at the Theatre",
    # "Achievement diaries",
    # "Scenery",
]


def get_slugs(dev=False):
    slugs = []

    if dev:
        with open(SLUGS_DEV_FILE) as file:
            for line in file:
                slugs.append(line.strip())
        return slugs

    for filename in os.listdir(SLUGS_DIR):
        if not filename.endswith(".txt"):
            continue

        if filename.replace(".txt", "") not in SCRAPE_CATEGORIES:
            continue

        with open(SLUGS_DIR + filename, "r") as file:
            for line in file:
                slugs.append(line.strip())
    return slugs


def generate_article_summary(slug, slug_number):
    """Generates a summary of the article.

    Scraping any article is broken down into 3 sections:
      1. The article title
      2. The article's infobox (right-hand side metadata/information)
      3. The article's core content
    """

    def _get_title():
        title = soup.find("h1", id="firstHeading")
        if not title:
            raise Exception(f"No title found for slug: {slug}")
        return title.text.strip()

    url = OSRS_WIKI_URL_BASE + slug
    res = requests.get(url)

    soup = BeautifulSoup(res.content, "html.parser")

    # ~~~ ~~~ ~~~ ~~~
    # 1. ARTICLE TITLE
    # ~~~ ~~~ ~~~ ~~~
    title = _get_title()
    print(f"{slug_number}: {title} in progress...")

    # ~~~ ~~~ ~~~ ~~~
    # 2. ARTICLE INFOBOX
    # ~~~ ~~~ ~~~ ~~~
    infobox = get_infobox(soup, title)

    # ~~~ ~~~ ~~~ ~~~
    # 3. ARTICLE CONTENT
    # ~~~ ~~~ ~~~ ~~~
    content = get_content(soup, title)

    # ~~~ ~~~ ~~~ ~~~
    # SUMMARY GENERATION
    # ~~~ ~~~ ~~~ ~~~
    summary = f"{title}\n\n{infobox}\n{content}"

    # Save the output to a file
    if not os.path.exists(SUMMARIES_DIR):
        os.makedirs(SUMMARIES_DIR)
    filename = (
        title.lower().replace(" ", "-").replace("'", "").replace("/", "|") + ".txt"
    )
    with open(SUMMARIES_DIR + filename, "w", encoding="utf-8") as f:
        f.write(summary)


def main():
    args = sys.argv[1:]
    dev = False
    if len(args) > 0 and args[0] == "dev":
        dev = True
    all_slugs = get_slugs(dev)
    for i, slug in enumerate(all_slugs):
        generate_article_summary(slug, i)


if __name__ == "__main__":
    main()
