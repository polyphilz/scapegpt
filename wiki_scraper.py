import os
import requests

from bs4 import BeautifulSoup
from collections import OrderedDict
from tabulate import tabulate


OSRS_WIKI_URL_BASE = "https://oldschool.runescape.wiki"
SLUGS_FILE = "test_slugs.txt"
SUMMARIES_DIR = "summaries/"

KNOWN_INFOBOX_LABELS = [
    "Map icon",
    "Released",
    "Removal",
    "Members",
    "Quest",
    "Location",
    "Options",
    "Examine",
    "Object ID",
]
KNOWN_HEADLINES = [
    "Additional drops",
    "Changes",
    "Creation Menu",
    "Gallery",
    "Location",
    "Locations",
    "Mechanics",
    "Trivia",
    "Transcript",
    "Tree locations",
    "Woodcutting info",
]
EXCLUDED_HEADLINES = [
    "References",
]


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
        print(title)

        # Get the article content
        content_section = soup.find("div", id="bodyContent").find(
            "div", id="mw-content-text"
        )
        content = ""
        for child in content_section.find(
            "div", class_="mw-parser-output"
        ).findChildren(recursive=False):
            if child.name == "div":
                for childs_child in child.findChildren(recursive=False):
                    if (
                        childs_child.name == "div"
                        and "class" in childs_child.attrs
                        and "transcript" in childs_child["class"]
                    ):
                        for x in childs_child.findChildren(recursive=False):
                            if x.name == "hr":
                                continue
                            content += x.text.strip() + "\n\n"
            if child.name == "h2":
                headline = child.find("span", class_="mw-headline").text.strip()
                if headline in EXCLUDED_HEADLINES:
                    continue
                if headline not in KNOWN_HEADLINES:
                    print(f"\n***UNKNOWN HEADLINE: {headline}\nFOR TITLE: {title}***\n")
                content += f"### {headline}\n\n"
            if child.name == "p":
                content += f"{child.text.strip()}\n\n"
            if child.name == "ul":
                for li in child.find_all("li"):
                    content += f"* {li.text.strip()}\n"
                content += "\n"
            if child.name == "table" and "wikitable" in child["class"]:
                # Extract the table headers and rows as lists
                headers = [th.text.strip() for th in child.select("tr th")]
                rows = []
                for tr in child.select("tr"):
                    if not tr.select("td"):
                        continue
                    row = []
                    for td in tr.select("td"):
                        # Ignore cells containing just images as this messes up
                        # the table formatting.
                        if td.find("span", class_="plinkt-template"):
                            continue

                        members_img = td.find(
                            "img", src="/images/Member_icon.png?1de0c"
                        )
                        if members_img:
                            row.append(True)
                            continue

                        f2p_img = td.find(
                            "img", src="/images/Free-to-play_icon.png?628ce"
                        )
                        if f2p_img:
                            row.append(False)
                            continue

                        row_content = td.text.strip()
                        row_content = row_content.replace("(update)", "")
                        row_content = row_content.replace(" (update)", "")
                        row_content = row_content.replace(" (update | poll)", "")
                        row_content = row_content.replace("(update | poll)", "")

                        row.append(row_content)

                    rows.append(row)

                # Convert the table to Markdown using the tabulate library
                markdown_table = tabulate(rows, headers=headers, tablefmt="pipe")
                content += markdown_table + "\n\n"

        # Get the article info box
        infobox_table = soup.find("table", {"class": "infobox"})
        infobox_info = ""
        if infobox_table:
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
                if row_label == "Released" or row_label == "Removal":
                    row_content = row_content.replace(" (Update)", "").replace(
                        "(Update)", ""
                    )
                if row_label not in KNOWN_INFOBOX_LABELS:
                    print(
                        f"\n***UNKNOWN INFO BOX LABEL: {row_label}\nFOR TITLE: {title}***\n"
                    )
                info[row_label] = row_content

            for info_label, info_content in info.items():
                infobox_info += f"{info_label}: {info_content}\n"

        # Create the output via concatenation of the article subcomponent
        if infobox_table:
            output = (
                f"# {title}\n\n## Content\n\n{content}## Information\n\n{infobox_info}"
            )
        else:
            output = f"# {title}\n\n## Content\n\n{content}"

        # Save the output to a file
        if not os.path.exists(SUMMARIES_DIR):
            os.makedirs(SUMMARIES_DIR)
        filename = title.lower().replace(" ", "-").replace("'", "") + ".md"
        with open(SUMMARIES_DIR + filename, "w", encoding="utf-8") as f:
            f.write(output)


if __name__ == "__main__":
    main()
