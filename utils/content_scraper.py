import copy

from bs4 import NavigableString
from tabulate import tabulate


EXCLUDED_HEADLINES = set(
    [
        "changes",
        "references",
        "gallery",
        "gallery (historical)",
        "trivia",
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


def get_content(soup, title):
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
                            output += x.text.strip() + "\n\n"

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
                            row_content = row_content.replace(" (update | poll)", "")
                            row_content = row_content.replace("\n(update | poll)", "")
                            row_content = row_content.replace("(update | poll)", "")

                            row.append(row_content)
                        rows.append(row)

                    # Convert the table to Markdown using the tabulate library
                    markdown_table = tabulate(rows, headers=headers, tablefmt="pipe")
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
