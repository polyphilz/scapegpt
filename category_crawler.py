import requests

from bs4 import BeautifulSoup

OSRS_WIKI_CATEGORY_CATALOG = "https://oldschool.runescape.wiki/w/Category:Content"
OSRS_WIKI_URL_BASE = "https://oldschool.runescape.wiki"
SLUGS_FILE = "slugs.txt"


def main():
    res = requests.get(OSRS_WIKI_CATEGORY_CATALOG)
    yummysoup = BeautifulSoup(res.text, "html.parser")
    categories = {}
    for child in yummysoup.find("div", class_="mw-category").findChildren():
        if child.name == "a":
            categories[child.text.strip()] = child["href"]

    scenery_slug = categories["Scenery"]
    url = OSRS_WIKI_URL_BASE + scenery_slug
    slugs = []
    while True:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")

        a_tags = soup.select("div.mw-category.mw-category-columns a")

        # Append the links to the list
        slugs.extend([a["href"] for a in a_tags])

        # Find the "next page" link
        has_next_page = False
        for child in soup.find("div", id="mw-pages").findChildren(recursive=False):
            if child.name != "a":
                continue
            if child.text.strip() == "next page":
                has_next_page = True
                url = OSRS_WIKI_URL_BASE + child["href"]
                break

        if not has_next_page:
            break

    with open("slugs.txt", "w") as f:
        for slug in slugs:
            f.write(slug + "\n")


if __name__ == "__main__":
    main()
