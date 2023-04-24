import os
import requests
import sys

from bs4 import BeautifulSoup

from utils.wiki_content_scraper import get_content
from utils.wiki_infobox_scraper import get_infobox


OSRS_WIKI_URL_BASE = "https://oldschool.runescape.wiki"
SLUGS_DEV_FILE = "test_slugs.txt"
PROBLEM_PAGES = [
    "calc",
    "screenshots",
    "user:",
]
# This is just for dev purposes. It allows for only scraping specific
# categories. If you _don't_ want to scrape a category, comment it out.
SCRAPE_CATEGORIES = [
    "Combat",
    "Combat Achievements",
    "Community",
    "Content with player credits",
    "Distraction and Diversion",
    "Game info",
    "Glitches",
    "Guides",
    "Gods",
    "Monsters",
    "Non-player characters",
    "Organisations",
    "Pets",
    "Races",
    "Items",
]


def get_slugs(dev: bool = False):
    """Extracts slugs from the 'slugs' directory.

    Args:
        dev (bool): If True, only returns the slugs from the 'test_slugs.txt'
            file.

    Returns:
        list: A list of all slugs. The list may contain duplicate slugs, but
            this doesn't matter as generated summaries will simply be
            overwritten.

    Raises:
        FileNotFoundError: If the 'slugs' directory or 'test_slugs.txt' file is
            not found.
    """
    slugs = []
    current_dir = os.path.dirname(os.path.abspath(__file__))
    three_dirs_up = os.path.join(current_dir, "..", "..", "..")
    slugs_dir = os.path.join(three_dirs_up, "slugs")

    if dev:
        filename = os.path.join(slugs_dir, SLUGS_DEV_FILE)
        with open(filename) as file:
            for line in file:
                slugs.append(line.strip())
        return slugs

    for filename in os.listdir(slugs_dir):
        if not filename.endswith(".txt"):
            continue

        if filename.replace(".txt", "") not in SCRAPE_CATEGORIES:
            continue

        with open(os.path.join(slugs_dir, filename), "r") as file:
            for line in file:
                # Hacky way of skipping specific problem-pages.
                should_skip_slug = False
                for problem_page in PROBLEM_PAGES:
                    if problem_page in line.lower():
                        should_skip_slug = True
                        break
                if should_skip_slug:
                    continue
                slugs.append(line.strip())
    return slugs


def generate_article_summary(slug: str, slug_number: int):
    """Generate a summary of an article.

    Scraping any article is broken down into 3 sections:
        1. The article title
        2. The article's infobox (right-hand side metadata/information)
        3. The article's core content

    Args:
        slug (str): The slug of the article.
        slug_number (int): The number of the slug. Purely for dev purposes (for
            seeing how many articles have been scraped).

    Returns:
        None
    """

    def _get_title():
        title = soup.find("h1", id="firstHeading")
        if not title:
            raise Exception(f"No title found for slug: {slug}")
        return title.text.strip()

    url = OSRS_WIKI_URL_BASE + slug
    res = requests.get(url)

    soup = BeautifulSoup(res.content, "html.parser")

    title = _get_title()
    print(f"{slug_number}: {title} in progress...")
    infobox = get_infobox(soup, title)
    content = get_content(soup, title)

    summary = f"{title}\n\n{infobox}\n{content}"
    # Creates the summaries/ directory at the root of the project if it doesn't
    # already exist. Then, uses a cleaned version of the title of the article
    # to create the text file corresponding to the summary of that article
    # within the summaries/ directory.
    current_dir = os.path.dirname(os.path.abspath(__file__))
    three_dirs_up = os.path.join(current_dir, "..", "..", "..")
    summaries_dir = os.path.join(three_dirs_up, "summaries")
    os.makedirs(summaries_dir, exist_ok=True)
    filename = (
        title.lower().replace(" ", "-").replace("'", "").replace("/", "|") + ".txt"
    )
    filename = os.path.join(summaries_dir, filename)
    with open(filename, "w", encoding="utf-8") as f:
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
