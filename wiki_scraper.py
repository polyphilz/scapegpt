import os
import requests

from bs4 import BeautifulSoup
from collections import OrderedDict


OSRS_WIKI_URL_BASE = "https://oldschool.runescape.wiki/w/"
SLUGS_FILE = "slugs.txt"
SUMMARIES_DIR = "summaries/"


def get_url_slugs():
    url_slugs = []
    with open(SLUGS_FILE, "r") as file:
        for line in file:
            url_slugs.append(line.strip())
    return url_slugs


def main():
    url_slugs = get_url_slugs()

    for slug in url_slugs:
        url = OSRS_WIKI_URL_BASE + slug
        res = requests.get(url)

        # Parse HTML content of article using BeautifulSoup
        soup = BeautifulSoup(res.content, "html.parser")

        # Get the article title
        title = soup.find("h1", id="firstHeading").text.strip()

        # Get the article content
        content_section = soup.find("div", id="bodyContent").find(
            "div", id="mw-content-text"
        )
        description = (
            content_section.find("div", class_="mw-parser-output")
            .find("p")
            .text.strip()
        )

        # Get the article info box
        infobox_table = soup.find("table", {"class": "infobox"})
        rows = infobox_table.find_all("tr")
        info = OrderedDict()
        for row in rows:
            cols = row.find_all(["th", "td"])

            # Skip rows that don't have heading labels with information. For
            # example, the first and second rows of the infobox table contain
            # the article title and associated image; those can be skipped.
            if len(cols) < 2:
                continue

            row_label = cols[0].text.strip()
            row_content = cols[1].text.strip()
            if row_label == "Map icon":
                continue
            if row_label == "Released":
                row_content = row_content.replace(" (Update)", "").replace(
                    "(Update)", ""
                )
            info[row_label] = row_content

        infobox_info = ""
        for info_label, info_content in info.items():
            infobox_info += f"{info_label}: {info_content}\n"

        # Create the output via concatenation of the article subcomponent
        output = f"# {title}\n\n## Content\n\n{description}\n\n## Information\n\n{infobox_info}"

        # Save the output to a file
        if not os.path.exists(SUMMARIES_DIR):
            os.makedirs(SUMMARIES_DIR)
        filename = title.lower().replace(" ", "-").replace("'", "") + ".md"
        with open(SUMMARIES_DIR + filename, "w", encoding="utf-8") as f:
            f.write(output)

        print(f"Output saved to {filename}")


if __name__ == "__main__":
    main()
