import os
import requests

from bs4 import BeautifulSoup
from typing import Dict


OSRS_WIKI_URL_BASE = "https://oldschool.runescape.wiki"
# The "main" category page that contains links to all other sub-categories.
OSRS_WIKI_CATEGORY_CATALOG = "https://oldschool.runescape.wiki/w/Category:Content"

# Categories containing pages that (probably) aren't worth indexing.
SKIPPED_CATEGORIES = [
    "Calculators",
    "Discontinued content",
    "Events",  # TODO(rbnsl): Ensure this should be skipped.
    "Future content",
    "Nonexistent content",
    "Unofficially named content",
    "Updates",
    "2013 Midsummer event",
    "2013 Thanksgiving event",
    "2014 Birthday event",
    "2014 Easter event",
    "2014 Goblin Invasion",
    "2014 Thanksgiving event",
    "2015 Birthday event",
    "2016 April Fools",
    "2016 Birthday event",
    "2017 Birthday event",
    "2018 Birthday event",
    "2019 Birthday event",
    "2020 Birthday event",
    "2021 Birthday event",
    "2022 Birthday event",
    "2023 Birthday event",
    "Midsummer events",
    "Languages",
]
# Wiki pages for these categories don't have a separate section for all the
# individual articles recursively listed under them; instead, they just have
# links to sub-categories (that in turn, DO have articles listed under them).
CATEGORIES_REQUIRING_SUBCATEGORY_EXPLORATION = [
    "Inhabitants",
    "Languages",  # This is skipped anyway; included here for completeness.
    "Old School-exclusive content",
]


def collect_category_slugs(url, categories_to_slugs: Dict[str, str]):
    """Maps category names to their respective slugs.

    Arguments:
    - url (str): The URL of the category page to scrape.
    - categories_to_slugs (dict): A dictionary of category names to category
        slugs.

    Raises:
    - Exception: If no categories are found in the category page.

    Returns:
    - None
    """
    res = requests.get(url)
    soup = BeautifulSoup(res.text, "html.parser")

    page_categories = soup.find("div", class_="mw-category")
    if not page_categories:
        # This state would only be reachable if:
        #   - The wiki category catalog HTML has changed
        #   - The URL for the category catalog has changed
        raise Exception(f"No categories found\nURL - {url}")

    for child in page_categories.findChildren():
        # We're only interested in anchor tags with both "title" and "href"
        # attributes; we can skip everything else.
        if child.name != "a" or "title" not in child.attrs or "href" not in child.attrs:
            continue

        category = child["title"].replace("Category:", "")
        if category in SKIPPED_CATEGORIES:
            continue
        category_slug = child["href"]

        if category in CATEGORIES_REQUIRING_SUBCATEGORY_EXPLORATION:
            collect_category_slugs(
                OSRS_WIKI_URL_BASE + category_slug, categories_to_slugs
            )
        else:
            categories_to_slugs[category] = category_slug


def generate_slug_file(category: str, slug: str):
    """
    Generate a text file containing slugs for all articles listed under a given
    category on the Old School RuneScape Wiki.

    Args:
        category (str): The name of the category to generate slugs for.
        slug (str): The slug of an article in the category to start with.

    Raises:
        Exception: If no articles are found for the given category.

    Returns:
        None
    """
    url = OSRS_WIKI_URL_BASE + slug

    slugs_for_category = []
    while True:
        # In this loop, we gather all the articles' slugs listed under the
        # category. However, the wiki uses pagination such that only 200
        # articles are shown at any given time. As a result, we need to
        # continually "fetch" the next page of articles until there are no
        # more articles (i.e. the "next page" link is not present).
        res = requests.get(url)
        soup = BeautifulSoup(res.text, "html.parser")

        a_tags = soup.select("div#mw-pages div.mw-category a")
        if len(a_tags) == 0:
            raise Exception(f"No articles found for category: {category}")

        slugs_for_category.extend([a["href"] for a in a_tags])

        has_next_page = False
        for child in soup.find("div", id="mw-pages").findChildren(recursive=False):
            if child.name != "a":
                continue

            # Because we're guaranteed to have a child that's an anchor tag at
            # this point, if the anchor tag has the text "next page", we know
            # that there's a next page (as the "next page" text is clickable).
            if child.text.strip() == "next page":
                has_next_page = True
                url = OSRS_WIKI_URL_BASE + child["href"]
                break

        # No pages left; exit the loop.
        if not has_next_page:
            break

    # Creates the slugs/ directory at the root of the project if it doesn't
    # already exist, and then for each category, creates a txt file for that
    # category containing slugs for each page listed within that category.
    current_dir = os.path.dirname(os.path.abspath(__file__))
    three_dirs_up = os.path.join(current_dir, "..", "..", "..")
    slugs_dir = os.path.join(three_dirs_up, "slugs")
    os.makedirs(slugs_dir, exist_ok=True)
    filename = os.path.join(slugs_dir, f"{category}.txt")
    with open(filename, "w") as f:
        for slug in slugs_for_category:
            f.write(slug + "\n")

    print(f"Generated slug file for category: {category}.")


def main():
    categories_to_slugs = {}
    collect_category_slugs(OSRS_WIKI_CATEGORY_CATALOG, categories_to_slugs)
    for category, slug in categories_to_slugs.items():
        generate_slug_file(category, slug)


if __name__ == "__main__":
    main()
