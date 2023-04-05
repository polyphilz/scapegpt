import copy
import os
import requests

from bs4 import BeautifulSoup, NavigableString
from collections import OrderedDict
from enum import Enum
from tabulate import tabulate


class CombatStatsState(Enum):
    COMBAT_STATS = 1
    AGGRESSIVE_STATS = 2
    DEFENSIVE_STATS = 3


OSRS_WIKI_URL_BASE = "https://oldschool.runescape.wiki"
SLUGS_FILE = "slugs.txt"
SUMMARIES_DIR = "summaries/"

KNOWN_INFOBOX_LABELS = [
    "Map icon",
    "Released",
    "Removal",
    "AKA",
    "Members",
    "Quest",
    "Location",
    "Options",
    "Examine",
    "Object ID",
    "Combat level",
    "Size",
    "Max hit",
    "Aggressive",
    "Poisonous",
    "Attack style",
    "Attack speed",
    "Poison",
    "Venom",
    "Monster ID",
    "NPC ID",
    "Respawn time",
    "Respawn Time",
    "Attribute",
    "XP bonus",
]
# TODO(rbnsl): Ignore case.
KNOWN_HEADLINES = [
    "Access",
    "Achievement gallery",
    "Achievement Gallery",
    "Additional drops",
    "Additional Drops",
    "Agility info",
    "Armour sets",
    "Assembly",
    "Attack info",
    "Attack Info",
    "Banking",
    "Basement",
    "Brewing process",
    "Brewing Process",
    "Burn Level",
    "Burn level",
    "Capes",
    "Castle Wars armour",
    "Changes",
    "Combat Achievements",
    "Combat achievements",
    "Common cannon spots",
    "Comparison between other ranged weapons",
    "Contribution experience",
    "Contribution Experience",
    "Costumes",
    "Creation Menu",
    "Creatures",
    "Cut chance",
    "Cut Chance",
    "Dialogue",
    "Differences in Deadman Mode",
    "Dining Room, Combat Room, Throne Room, and Treasure Room",
    "Drops",
    "Experience",
    "Farming",
    "Farming info",
    "Farming Info",
    "Fire pits",
    "Firemaking info",
    "Firemaking Info",
    "Fishing info",
    "Fishing Info",
    "Flower patches",
    "Flower Patches",
    "Formal Garden",
    "Formal garden",
    "Gallery",
    "Gallery (historical)",
    "Garden",
    "Getting there",
    "Getting There",
    "Getting to them",
    "Getting To them",
    "Getting To Them",
    "Getting to Them",
    "Growth stages",
    "Growth Stages",
    "Herbs",
    "High-tier loot table",
    "History",
    "Hitpoints info",
    "How to use the Fractionalising still",
    "HP scaling in different team sizes",
    "Hunter info",
    "Hunter Info",
    "Inside the castle",
    "Inside the Castle",
    "Interactions",
    "Interface",
    "Items",
    "Lighting",
    "Linking holes",
    "Location",
    "Location of ingredients",
    "Locations",
    "Log pile locations",
    "Log pile Locations",
    "Log Pile Locations",
    "Loot",
    "Loot mechanics",
    "Loot Mechanics",
    "Loot table",
    "Looting the chest",
    "Looting the Chest",
    "Lore",
    "Low-tier loot table",
    "Magical armour",
    "Magical Armour",
    "Magical armor",
    "Magical Armor",
    "Mechanics",
    "Mid-tier loot table",
    "Mining granite",
    "Mining Granite",
    "Mining info",
    "Mining Info",
    "Multiple traps",
    "Multiple Traps",
    "Notes",
    "NPCs",
    "Offering fish",
    "Oubliette, Dungeon, and Treasure Room",
    "Oubliette",
    "Passing the gate",
    "Permanent fires",
    "Portal Chamber",
    "Portal chamber",
    "Possible loot",
    "Possible Loot",
    "Possible rewards",
    "Possible Rewards",
    "Power-mining Locations",
    "Praying-at",
    "Pre-release",
    "Pre-Release",
    "Products",
    "Products of rotting",
    "Prohibited areas",
    "Reanimation spells",
    "Reanimation Spells",
    "Recharging dragonstone jewellery",
    "Related shops",
    "Related Shops",
    "Rewards calculator",
    "Reward mechanics",
    "Reward possibilities",
    "Reward Possibilities",
    "Rewards possibilities",
    "Rewards Possibilities",
    "Rewards",
    "See also",
    "Shattered Relics",
    "Shattered relics",
    "Shop",
    "Skill info",
    "Skilling info",
    "Smashing the barrels",
    "Smithing armour",
    "Stock",
    "Storage",
    "Strategy",
    "Strength info",
    "Strength Info",
    "Success chance",
    "Success Chance",
    "The Forsaken Tower",
    "Thieving",
    "Thieving info",
    "Thieving Info",
    "Throne room",
    "Throne Room",
    "Trailblazer",
    "Trailblazers",
    "Transportation",
    "Treasure Trails",
    "Treasure trails",
    "Trivia",
    "Training",
    "Transcipt",  # Intentional; see "Ancient Plaque"
    "Transcript",
    "Tree locations",
    "Tree Locations",
    "Twisted",
    "Upper",
    "Usage",
    "Uses",
    "Woodcutting",
    "Woodcutting info",
    "Yield",
]
EXCLUDED_HEADLINES = [
    "References",
]
SKILLS = [
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


def get_url_slugs():
    url_slugs = []
    with open(SLUGS_FILE, "r") as file:
        for line in file:
            url_slugs.append(line.strip())
    return url_slugs


def main():
    url_slugs = get_url_slugs()

    starter = z = 3150
    # starter = z = 0
    for slug in url_slugs[starter:]:
        url = OSRS_WIKI_URL_BASE + slug
        res = requests.get(url)

        # Parse HTML content of article using BeautifulSoup
        soup = BeautifulSoup(res.content, "html.parser")

        # Get the article title
        title = soup.find("h1", id="firstHeading").text.strip()
        print(f"{z}: {title}")

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
            if child.name == "h3":
                headline = child.find("span", class_="mw-headline").text.strip()
                content += f"#### {headline}\n\n"
            if child.name == "h4":
                headline = child.find("span", class_="mw-headline").text.strip()
                content += f"##### {headline}\n\n"
            if child.name == "p":
                # Skip mathematical formulas; they screw up formatting majorly.
                if child.find("span", class_="mwe-math-element"):
                    continue
                # Removes [1], [c 1] etc annotations from the paragraph content.
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
                content += f"{child.text.strip()}\n\n"
            if child.name == "ul":
                for li in child.find_all("li", recursive=False):
                    ul = li.find("ul")
                    if ul:
                        copy_ul = copy.copy(ul)
                        ul.clear()
                        content += f"* {li.text.strip()}\n"
                        for sub_li in copy_ul.find_all("li"):
                            content += f"  * {sub_li.text.strip()}\n"
                        continue
                    content += f"* {li.text.strip()}\n"
                content += "\n"
            # Numbered lists are sometimes <dl>s
            if child.name == "dl" or child.name == "ol":
                for i, li in enumerate(child.find_all("li")):
                    content += f"{i + 1}. {li.text.strip()}\n"
                content += "\n"
            if (
                child.name == "table"
                and "class" in child.attrs
                and "wikitable" in child["class"]
            ):
                # TODO(rbnsl): Figure out how to properly handle tables with
                # merged cells. Until then, just skip them.
                # cells = child.find_all(["th", "td"])
                # has_merged_cells = False
                # for cell in cells:
                #     if "rowspan" in cell.attrs and int(cell["rowspan"]) > 1:
                #         has_merged_cells = True
                #         break
                #     elif "colspan" in cell.attrs and int(cell["colspan"]) > 1:
                #         has_merged_cells = True
                #         break
                # if has_merged_cells:
                #     continue

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
                    if skill and "title" in skill.attrs and skill["title"] in SKILLS:
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
                                    plinkp_content += plinkp_anchor_tag["title"] + ", "
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
                            row.append("Available for free-to-play (F2P) players")
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
                            if "data-skill" in scp.attrs and "data-level" in scp.attrs:
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
                        row_content = row_content.replace(" (update | poll)", "")
                        row_content = row_content.replace("\n(update | poll)", "")
                        row_content = row_content.replace("(update | poll)", "")

                        row.append(row_content)
                    rows.append(row)

                # Convert the table to Markdown using the tabulate library
                markdown_table = tabulate(rows, headers=headers, tablefmt="pipe")
                content += markdown_table + "\n\n"
            if (
                child.name == "table"
                and "class" in child.attrs
                and "infobox" in child["class"]
                and "skill-info" in child["class"]
            ):
                trs = child.find_all("tr")
                if len(trs) < 4:
                    continue
                for tr in trs[2 : len(trs) - 1]:
                    th = tr.find("th")
                    if th:
                        content += th.text.strip()
                    skills_and_levels = tr.find_all("span", class_="scp")
                    if len(skills_and_levels) > 0:
                        content += " - "
                        for skl_lvl in skills_and_levels:
                            if (
                                "data-skill" in skl_lvl.attrs
                                and "data-level" in skl_lvl.attrs
                            ):
                                content += (
                                    skl_lvl["data-level"]
                                    + " "
                                    + skl_lvl["data-skill"]
                                    + ", "
                                )
                        content = content[:-2]
                    else:
                        td = tr.find("td")
                        if td and td.text.strip():
                            content += " - " + td.text.strip()
                    content += "\n"
                content += "\n"

        # Get the article info box
        infobox_table = soup.find("table", {"class": "infobox"})
        infobox_info = ""
        if infobox_table:
            rows = infobox_table.find_all("tr")
            info = OrderedDict()
            combat_stats_state = CombatStatsState.COMBAT_STATS
            most_recent_combat_stats_headers = []
            for row in rows:
                # From within "Combat Stats" section, check to see if we are now
                # analyzing a different portion of combat stats (e.g.
                # aggressive, or defensive). This impacts some of the English
                # used.
                combat_stats_subheader = row.find("th", class_="infobox-subheader")
                if combat_stats_subheader:
                    combat_stats_subheader = combat_stats_subheader.text.strip()
                    if "Aggressive stats" in combat_stats_subheader:
                        combat_stats_state = CombatStatsState.AGGRESSIVE_STATS
                    if "Defensive stats" in combat_stats_subheader:
                        combat_stats_state = CombatStatsState.DEFENSIVE_STATS
                    continue

                combat_stats_headers = row.find_all("th", class_="infobox-nested")
                if len(combat_stats_headers) > 0:
                    for combat_stats_header in combat_stats_headers:
                        csh_anchor = combat_stats_header.find("a")
                        if "title" in csh_anchor.attrs:
                            csh_stat_title = csh_anchor["title"]
                            if combat_stats_state == CombatStatsState.AGGRESSIVE_STATS:
                                if csh_stat_title == "Magic":
                                    csh_stat_title = "Monster magic bonus"
                                if csh_stat_title == "Ranged":
                                    csh_stat_title = "Monster ranged bonus"
                            if combat_stats_state == CombatStatsState.DEFENSIVE_STATS:
                                if csh_stat_title == "Stab":
                                    csh_stat_title = "Monster defensive stab bonus"
                                if csh_stat_title == "Slash":
                                    csh_stat_title = "Monster defensive slash bonus"
                                if csh_stat_title == "Crush":
                                    csh_stat_title = "Monster defensive crush bonus"
                                if csh_stat_title == "Magic":
                                    csh_stat_title = "Monster defensive magic bonus"
                                if csh_stat_title == "Ranged":
                                    csh_stat_title = "Monster defensive ranged bonus"
                            most_recent_combat_stats_headers.append(csh_stat_title)
                    continue

                combat_stats_values = row.find_all("td", class_="infobox-nested")
                if len(combat_stats_values) > 0:
                    # This state shouldn't be reachable, but just in case
                    if len(most_recent_combat_stats_headers) != len(
                        combat_stats_values
                    ):
                        continue
                    for i, combat_stats_value in enumerate(combat_stats_values):
                        info[most_recent_combat_stats_headers[i]] = (
                            combat_stats_value.text.strip()
                            .replace(" (edit)", "")
                            .replace("(edit)", "")
                        )
                    most_recent_combat_stats_headers = []
                    combat_stats_state = CombatStatsState.COMBAT_STATS
                    continue

                cols = row.find_all(["th", "td"])

                # Skip rows that don't have heading labels with information. For
                # example, the first and second rows of the infobox table contain
                # the article title and associated image; those can be skipped.
                if len(cols) < 2:
                    continue

                row_label = cols[0].text.strip()

                # If a infobox value has a <br>, replace it with a ", ".
                # https://oldschool.runescape.wiki/w/Fermenting_vat as an
                # example, with the "Keldagrim" and "Port Phasmatys".
                for br in cols[1].find_all("br"):
                    br.replace_with(NavigableString(", "))

                row_content = (
                    cols[1].text.strip().replace(" (edit)", "").replace("(edit)", "")
                )

                # TODO(rbnsl): Clean this up. Use
                # https://oldschool.runescape.wiki/w/Galvek as an example.
                if (
                    cols[1].find("img")
                    and "alt" in cols[1].find("img").attrs
                    and "onster attack speed" in cols[1].find("img")["alt"]
                ):
                    row_content = cols[1].find("img")["alt"].replace(".png", "")[-1]

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
        filename = (
            title.lower().replace(" ", "-").replace("'", "").replace("/", "|") + ".md"
        )
        with open(SUMMARIES_DIR + filename, "w", encoding="utf-8") as f:
            f.write(output)

        z += 1


if __name__ == "__main__":
    main()
