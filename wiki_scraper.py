import copy
import os
import requests
import sys

from bs4 import BeautifulSoup, NavigableString
from collections import OrderedDict
from enum import Enum
from tabulate import tabulate


class CombatStatsState(Enum):
    COMBAT_STATS = 1
    AGGRESSIVE_STATS = 2
    DEFENSIVE_STATS = 3


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


# INFOBOX CONSTANTS:
VALID_COMBAT_STATS_TITLES = set(
    [
        "Hitpoints",
        "Attack",
        "Strength",
        "Defence",
        "Defense",
        "Magic",
        "Ranged",
        "Monster attack bonus",
        "Monster strength bonus",
        "Monster magic strength bonus",
        "Monster ranged strength bonus",
        "Stab",
        "Slash",
        "Crush",
    ]
)
VALID_COMBAT_STATS_DATA_ATTRS = set(
    [
        "hitpoints",
        "att",
        "str",
        "def",
        "mage",
        "range",
        "attbns",
        "strbns",
        "amagic",
        "mbns",
        "arange",
        "rngbns",
        "dstab",
        "dslash",
        "dcrush",
        "dmagic",
        "drange",
    ]
)
EXCLUDED_INFOBOX_LABELS = set(["map icon", "monster id", "npc id", "object id"])
KNOWN_INFOBOX_LABELS = set(
    [
        "released",
        "removal",
        "aka",
        "members",
        "quest",
        "location",
        "options",
        "examine",
        "combat level",
        "size",
        "max hit",
        "aggressive",
        "poisonous",
        "attack style",
        "attack speed",
        "poison",
        "venom",
        "respawn time",
        "attribute",
        "xp bonus",
        "slayer level",
        "slayer xp",
        "category",
        "assigned by",
        "cannons",
        "thralls",
    ]
)


# CONTENT CONSTANTS:
EXCLUDED_HEADLINES = set(
    [
        "changes",
        "references",
        "gallery",
        "gallery (historical)",
    ]
)
KNOWN_HEADLINES = set(
    [
        "access",
        "achievement gallery",
        "additional drops",
        "agility info",
        "armour sets",
        "assembly",
        "attack info",
        "banking",
        "basement",
        "brewing process",
        "burn level",
        "capes",
        "castle wars armour",
        "combat achievements",
        "common cannon spots",
        "comparison between other ranged weapons",
        "contribution experience",
        "costumes",
        "creation menu",
        "creatures",
        "cut chance",
        "dialogue",
        "differences in deadman mode",
        "dining room, combat room, throne room, and treasure room",
        "drops",
        "experience",
        "farming",
        "farming info",
        "fire pits",
        "firemaking info",
        "fishing info",
        "flower patches",
        "formal garden",
        "garden",
        "getting there",
        "getting to them",
        "growth stages",
        "herbs",
        "high-tier loot table",
        "history",
        "hitpoints info",
        "how to use the fractionalising still",
        "hp scaling in different team sizes",
        "hunter info",
        "inside the castle",
        "interactions",
        "interface",
        "items",
        "lighting",
        "linking holes",
        "location",
        "location of ingredients",
        "locations",
        "log pile locations",
        "loot",
        "loot mechanics",
        "loot table",
        "looting the chest",
        "lore",
        "low-tier loot table",
        "magical armour",
        "magical armor",
        "mechanics",
        "mid-tier loot table",
        "mining granite",
        "mining info",
        "multiple traps",
        "notes",
        "npcs",
        "offering fish",
        "oubliette, dungeon, and treasure room",
        "oubliette",
        "passing the gate",
        "permanent fires",
        "portal chamber",
        "possible loot",
        "possible rewards",
        "power-mining locations",
        "praying-at",
        "pre-release",
        "products",
        "products of rotting",
        "prohibited areas",
        "reanimation spells",
        "recharging dragonstone jewellery",
        "related shops",
        "rewards calculator",
        "reward mechanics",
        "reward possibilities",
        "rewards possibilities",
        "rewards",
        "see also",
        "shattered relics",
        "shop",
        "skill info",
        "skilling info",
        "smashing the barrels",
        "smithing armour",
        "stock",
        "storage",
        "strategy",
        "strength info",
        "success chance",
        "the forsaken tower",
        "thieving",
        "thieving info",
        "throne room",
        "trailblazer",
        "trailblazers",
        "transportation",
        "treasure trails",
        "trivia",
        "training",
        "transcipt",  # Intentional; see "Ancient Plaque"
        "transcript",
        "tree locations",
        "twisted",
        "upper",
        "usage",
        "uses",
        "woodcutting",
        "woodcutting info",
        "yield",
    ]
)
SKILLS = set(
    [
        "Agility",
        "Artisan",
        "Attack",
        "Construction",
        "Cooking",
        "Crafting",
        "Defense",
        "Defence",
        "Farming",
        "Firemaking",
        "Fishing",
        "Fletching",
        "Herblore",
        "Hitpoints",
        "Hunter",
        "Magic",
        "Mining",
        "Prayer",
        "Ranged",
        "Runecraft",
        "Sailing",
        "Slayer",
        "Smithing",
        "Strength",
        "Summoning",
        "Thieving",
        "Warding",
        "Woodcutting",
    ]
)


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

    def _get_infobox(title):
        # Although other elements in the page can have the class ".infobox",
        # it's always the case that the first element with ".infobox" is the
        # right-hand side table containing the metadata/information for whatever
        # the article pertains to.
        #
        # It *is* possible that an article has _no_ infobox. In that case,
        # hopefully there are no other tables with the class ".infobox" as that
        # could be messy (to my knowledge there is no way to differentiate
        # between the two).
        table = soup.find("table", class_="infobox")
        if not table:
            print(f"No infobox found for article: {title}")
            return ""

        # TODO(rbnsl): Use lists here instead of non-performant string
        # concatenation.
        output = ""

        # TODO(rbnsl): Handle the case where the infobox may have switchable
        # tabs. Example - https://oldschool.runescape.wiki/w/Zulrah.

        rows = table.find_all("tr")
        if len(rows) == 0:
            # This should (probably) never happen, hence the Exception.
            raise Exception(f"No rows found in infobox for article: {title}")

        # Maps the row headers in the infobox to the row values. For example,
        # given the row: "Released | 8 January 2015" in the infobox, `info`
        # would resemble:
        # {
        #   ...,
        #   "Released": "8 January 2015",
        #   ...,
        # }
        info = OrderedDict()
        # Monsters have 3 types of combat stats:
        #   1. Combat levels
        #   2. Aggressive stats (offensive bonuses)
        #   3. Defensive stats (defensive bonuses)
        #
        # `combat_stats_state` keeps track of which combat stats are currently
        # being analyzed, as the output needs to be slightly modified depending
        # on which combat stats the scraper is running through.
        #
        # This is specifically only relevant for monster infoboxes.
        combat_stats_state = CombatStatsState.COMBAT_STATS
        # Combat stats are structured in an annoying way that makes this var,
        # `cur_combat_stats_headers`, necessary. Consider the Zulrah page:
        # https://oldschool.runescape.wiki/w/Zulrah, and specifically the
        # "Combat stats" section in the infobox on the right-hand side. A whole
        # row is dedicated to just the icons (from which we need to pull) the
        # names of the combat skills. The _next_ row contains the actual values.
        # However, we iterate row by row. As a result, when we are analyzing
        # combat stats, we need to keep track of which combat "headers" are
        # currently relevant.
        cur_combat_stats_headers = []
        for row in rows:
            # If the subheader is a combat stat, progress the state of
            # `combat_stats_state` accordingly.
            subheader = row.find("th", class_="infobox-subheader")
            if subheader:
                subheader = subheader.text.strip()
                if "Aggressive stats" in subheader:
                    combat_stats_state = CombatStatsState.AGGRESSIVE_STATS
                elif "Defensive stats" in subheader:
                    combat_stats_state = CombatStatsState.DEFENSIVE_STATS
                continue

            # combat_stats_headers = row.find_all("th", class_="infobox-nested")
            # combat_stats_headers = row.select()
            # combat_stats_headers = soup.select("div#mw-pages div.mw-category a")
            combat_stats_headers = row.select("th.infobox-nested a")
            if len(combat_stats_headers) > 0:
                for combat_stats_header in combat_stats_headers:
                    if "title" not in combat_stats_header.attrs:
                        continue

                    combat_stats_header_title = combat_stats_header["title"]
                    if combat_stats_header_title not in VALID_COMBAT_STATS_TITLES:
                        # Guards against the possibility there are
                        # `th.infobox-nested` elements in infoboxes that are
                        # _not_ designated for combat stats.
                        continue

                    # Not all of the titles give us enough disambiguation
                    # between all combat stat types, so we need to manually
                    # manipulate this information.
                    match combat_stats_state:
                        case CombatStatsState.AGGRESSIVE_STATS:
                            if combat_stats_header_title == "Magic":
                                combat_stats_header_title = "Monster magic bonus"
                            elif combat_stats_header_title == "Ranged":
                                combat_stats_header_title = "Monster ranged bonus"
                        case CombatStatsState.DEFENSIVE_STATS:
                            if combat_stats_header_title == "Stab":
                                combat_stats_header_title = (
                                    "Monster defensive stab bonus"
                                )
                            elif combat_stats_header_title == "Slash":
                                combat_stats_header_title = (
                                    "Monster defensive slash bonus"
                                )
                            elif combat_stats_header_title == "Crush":
                                combat_stats_header_title = (
                                    "Monster defensive crush bonus"
                                )
                            elif combat_stats_header_title == "Magic":
                                combat_stats_header_title = (
                                    "Monster defensive magic bonus"
                                )
                            elif combat_stats_header_title == "Ranged":
                                combat_stats_header_title = (
                                    "Monster defensive ranged bonus"
                                )

                    cur_combat_stats_headers.append(combat_stats_header_title)
                continue

            combat_stats_values = row.find_all("td", class_="infobox-nested")
            if len(combat_stats_values) > 0:
                if len(cur_combat_stats_headers) != len(combat_stats_values):
                    # This state shouldn't be reachable, but just in case.
                    continue

                for i, combat_stats_value in enumerate(combat_stats_values):
                    if (
                        "data-attr-param" not in combat_stats_value.attrs
                        or combat_stats_value["data-attr-param"]
                        not in VALID_COMBAT_STATS_DATA_ATTRS
                    ):
                        continue
                    combat_stats_value = combat_stats_value.text.strip()
                    combat_stats_value = combat_stats_value.replace("(edit)", "")
                    combat_stats_value = combat_stats_value.replace(" (edit)", "")
                    info[cur_combat_stats_headers[i]] = combat_stats_value

                # Reset stored combat headers/state appropriately.
                cur_combat_stats_headers = []
                combat_stats_state = CombatStatsState.COMBAT_STATS
                continue

            # Process all NON-COMBAT infobox information from here on out.
            cols = row.find_all(["th", "td"])

            # Skip rows that don't have heading labels with information. For
            # example, the first and second rows of the infobox table contain
            # the article title and associated image; those can be skipped.
            if len(cols) < 2:
                continue

            row_label = cols[0].text.strip()
            if row_label.lower() in EXCLUDED_INFOBOX_LABELS:
                continue
            if row_label.lower() not in KNOWN_INFOBOX_LABELS:
                print(f"\nUNKNOWN *INFOBOX* LABEL: {row_label}\nFOR TITLE: {title}\n")

            # If a infobox value has a <br>, replace it with a ", ". Example -
            # https://oldschool.runescape.wiki/w/Fermenting_vat (see "Keldagrim"
            # and "Port Phasmatys").
            for br in cols[1].find_all("br"):
                br.replace_with(NavigableString(", "))

            row_content = (
                cols[1]
                .text.strip()
                .replace(" (edit)", "")
                .replace("(edit)", "")
                .replace("(Update)", "")
                .replace(" (Update)", "")
            )

            # Specifically handles scraping "Attack speed" data (it's an image)
            # in most articles.
            # TODO(rbnsl): Clean this up. Use
            # https://oldschool.runescape.wiki/w/Galvek as an example.
            if (
                cols[1].find("img")
                and "alt" in cols[1].find("img").attrs
                and "onster attack speed" in cols[1].find("img")["alt"]
            ):
                row_content = cols[1].find("img")["alt"].replace(".png", "")[-1]

            # Specifically handles the "Slayer info" "Assigned by" row.
            if (
                "data-attr-param" in cols[1].attrs
                and cols[1]["data-attr-param"] == "assignedby_pics"
            ):
                row_content = ""
                slayer_masters = cols[1].find_all("a")
                for slayer_master in slayer_masters:
                    if "title" not in slayer_master.attrs:
                        continue

                    row_content += slayer_master["title"] + ", "
                row_content = row_content[:-2]

            info[row_label] = row_content

        for info_label, info_content in info.items():
            output += f"{info_label}: {info_content}\n"

        return output

    def _get_content(title):
        content_section = soup.select(
            "div#bodyContent div#mw-content-text div.mw-parser-output"
        )
        if len(content_section) == 0:
            return ""
        content_section = content_section[0]

        # TODO(rbnsl): Use lists here instead of non-performant string
        # concatenation.
        output = ""
        cur_headline = ""
        for child in content_section.findChildren(recursive=False):
            if child.name == "h2":
                headline = child.find("span", class_="mw-headline")
                if not headline:
                    print(f"Unable to grab a main headline in article: {title}")
                    continue

                headline = headline.text.strip()
                if headline.lower() not in KNOWN_HEADLINES:
                    print(f"\nUNKNOWN *HEADLINE*: {headline}\nFOR TITLE: {title}\n")
                cur_headline = headline
                if cur_headline.lower() in EXCLUDED_HEADLINES:
                    continue

                output += f"{cur_headline}\n\n"
                continue

            # Currently in a "skipping section" state. Until `cur_headline` gets
            # updated, ignore all content.
            if cur_headline.lower() in EXCLUDED_HEADLINES:
                continue

            match child.name:
                case "div":
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

                case small_header if small_header in ["h3", "h4"]:
                    headline = child.find("span", class_="mw-headline")
                    if not headline:
                        print(
                            f"Unable to grab an {child.name} headline in article: {title}"
                        )
                        continue
                    headline = headline.text.strip()
                    output += f"{headline}\n\n"

                case "p":
                    # Skip mathematical formulas as they mess with formatting.
                    if child.find("span", class_="mwe-math-element"):
                        continue

                    # Removes (most) <sup> tags as they just add noise. Keep
                    # the ones for numbers (e.g. "2nd", "3rd", "4th") as well
                    # as the one providing disambiguation between floor
                    # numberings depending on the type of English (US vs UK).
                    # TODO(rbnsl): Abstract this out as it appears in multiple
                    # places.
                    sups = child.find_all("sup")
                    for sup in sups:
                        sup_text = sup.text.strip()
                        if (
                            "st" not in sup_text
                            and "nd" not in sup_text
                            and "rd" not in sup_text
                            and "US" not in sup_text
                            and "UK" not in sup_text
                        ):
                            sup.clear()
                    output += f"{child.text.strip()}\n\n"

                case "ul":
                    for li in child.find_all("li", recursive=False):
                        ul = li.find("ul")
                        if ul:
                            copy_ul = copy.copy(ul)
                            ul.clear()
                            output += f"* {li.text.strip()}\n"
                            for sub_li in copy_ul.find_all("li"):
                                output += f"  * {sub_li.text.strip()}\n"
                            continue
                        output += f"* {li.text.strip()}\n"
                    output += "\n"

                case numbered_list_tag if numbered_list_tag in ["dl", "ol"]:
                    for i, li in enumerate(child.find_all("li")):
                        output += f"{i + 1}. {li.text.strip()}\n"
                    output += "\n"

                case "table":
                    if "class" not in child.attrs:
                        continue

                    if "wikitable" in child["class"]:
                        # Extract the table headers and rows as lists
                        headers = []
                        for th in child.select("tr th"):
                            header_content = ""

                            # Removes [1], [c 1] etc annotations from the table headers.
                            sups = th.find_all("sup")
                            for sup in sups:
                                sup_text = sup.text.strip()
                                if (
                                    "st" not in sup_text
                                    and "nd" not in sup_text
                                    and "rd" not in sup_text
                                    and "US" not in sup_text
                                    and "UK" not in sup_text
                                ):
                                    sup.clear()

                            # Some tables have long enough headers that have <br>s;
                            # these need to be replaced with a space.
                            for br in th.find_all("br"):
                                br.replace_with(NavigableString(" "))

                            skill = th.find("a")
                            if (
                                skill
                                and "title" in skill.attrs
                                and skill["title"] in SKILLS
                            ):
                                header_content += skill["title"] + " "

                            header_content += th.text.strip()
                            headers.append(header_content)

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

                                # We need to get the text of the images. See:
                                # "Armour case space" as an example of this.
                                plinkps = td.find_all("span", class_="plinkp-template")
                                if len(plinkps) > 0:
                                    plinkp_content = ""
                                    for plinkp in plinkps:
                                        plinkp_anchor_tag = plinkp.find("a")
                                        if "title" in plinkp_anchor_tag.attrs:
                                            plinkp_content += (
                                                plinkp_anchor_tag["title"] + ", "
                                            )
                                    row.append(plinkp_content[:-2])
                                    continue

                                # Removes [1], [c 1] etc annotations from the table
                                # data.
                                sups = td.find_all("sup")
                                for sup in sups:
                                    sup_text = sup.text.strip()
                                    if (
                                        "st" not in sup_text
                                        and "nd" not in sup_text
                                        and "rd" not in sup_text
                                        and "US" not in sup_text
                                        and "UK" not in sup_text
                                    ):
                                        sup.clear()

                                members_img = td.find(
                                    "img", src="/images/Member_icon.png?1de0c"
                                )
                                if members_img:
                                    row.append("Members-only")
                                    continue

                                f2p_img = td.find(
                                    "img", src="/images/Free-to-play_icon.png?628ce"
                                )
                                if f2p_img:
                                    row.append(
                                        "Available for free-to-play (F2P) players"
                                    )
                                    continue

                                if "class" in td.attrs and "plainlist" in td["class"]:
                                    row_content = ""
                                    for li in td.find_all("li"):
                                        row_content += li.text.strip() + " "
                                        skill = li.find("span", class_="scp")
                                        if skill and "data-skill" in skill.attrs:
                                            row_content += skill["data-skill"]
                                        row_content += "\n"
                                    row.append(row_content)
                                    continue

                                scps = td.find_all("span", class_="scp")
                                row_content = ""
                                for scp in scps:
                                    if (
                                        "data-skill" in scp.attrs
                                        and "data-level" in scp.attrs
                                    ):
                                        row_content += (
                                            scp["data-skill"] + " " + scp["data-level"]
                                        )
                                    row_content += "\n"
                                if row_content:
                                    row.append(row_content)
                                    continue

                                for br in td.find_all("br"):
                                    br.replace_with(NavigableString("\n"))

                                row_content = td.text.strip()
                                row_content = row_content.replace("(update)", "")
                                row_content = row_content.replace(" (update)", "")
                                # TODO(rbnsl): These below 3 aren't working; fix them.
                                row_content = row_content.replace(
                                    " (update | poll)", ""
                                )
                                row_content = row_content.replace(
                                    "\n(update | poll)", ""
                                )
                                row_content = row_content.replace("(update | poll)", "")

                                row.append(row_content)
                            rows.append(row)

                        # Convert the table to Markdown using the tabulate library
                        markdown_table = tabulate(
                            rows, headers=headers, tablefmt="pipe"
                        )
                        output += markdown_table + "\n\n"
                    elif "infobox" in child["class"] and "skill-info" in child["class"]:
                        trs = child.find_all("tr")
                        if len(trs) < 4:
                            continue
                        for tr in trs[2 : len(trs) - 1]:
                            th = tr.find("th")
                            if th:
                                output += th.text.strip()
                            skills_and_levels = tr.find_all("span", class_="scp")
                            if len(skills_and_levels) > 0:
                                output += " - "
                                for skl_lvl in skills_and_levels:
                                    if (
                                        "data-skill" in skl_lvl.attrs
                                        and "data-level" in skl_lvl.attrs
                                    ):
                                        output += (
                                            skl_lvl["data-level"]
                                            + " "
                                            + skl_lvl["data-skill"]
                                            + ", "
                                        )
                                output = output[:-2]
                            else:
                                td = tr.find("td")
                                if td and td.text.strip():
                                    output += " - " + td.text.strip()
                            output += "\n"
                        output += "\n"

        return output

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
    infobox = _get_infobox(title)

    # ~~~ ~~~ ~~~ ~~~
    # 3. ARTICLE CONTENT
    # ~~~ ~~~ ~~~ ~~~
    content = _get_content(title)

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
