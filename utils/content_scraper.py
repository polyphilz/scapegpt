import copy

from bs4 import NavigableString
from enum import Enum


EXCLUDED_HEADLINES = set(
    [
        "changes",
        "references",
        "gallery",
        "gallery (historical)",
        "trivia",
        "history",
        "see also",
        "combat style",
        "combat styles",
        "creation",
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
        "combat skills",
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
        "other factors",
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
        "agility",
        "artisan",
        "attack",
        "construction",
        "cooking",
        "crafting",
        "defense",
        "defence",
        "farming",
        "firemaking",
        "fishing",
        "fletching",
        "herblore",
        "hitpoints",
        "hunter",
        "magic",
        "mining",
        "prayer",
        "ranged",
        "runecraft",
        "sailing",
        "slayer",
        "smithing",
        "strength",
        "summoning",
        "thieving",
        "warding",
        "woodcutting",
    ]
)


def _parse_wikitable(wikitable):
    def _get_headers():
        headers = []
        for th in wikitable.select("tr th"):
            header_content = ""

            # TODO(rbnsl): Abstract this out.
            # Removes annotations ([1], [c 1] etc.).
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

            # Some tables have long enough headers that have <br>s; these need to be
            # replaced with whitespace.
            for br in th.find_all("br"):
                br.replace_with(NavigableString(" "))

            # Some table headers have images of skills; these need to be parsed in a
            # way that actually adds the name of the skill.
            skill = th.find("a")
            if skill and "title" in skill.attrs and skill["title"].lower() in SKILLS:
                header_content += skill["title"] + " "

            # There are some "hidden" column headers on the wiki, such as high
            # alch on drop tables. Remove these to save token space (they don't)
            # add any meaningful information.
            if "class" in th.attrs and "alch-column" in th["class"]:
                continue

            header_content += th.text.strip()

            # Some headers may be empty, in which case we want to ignore them.
            # For example, in any of the drops tables in
            # https://oldschool.runescape.wiki/w/Zulrah, the first column header
            # is a cog with no text; we can ignore it.
            if header_content:
                headers.append(header_content)
        return headers

    def _get_rows():
        rows = []
        for tr in wikitable.select("tr"):
            tds = tr.select("td")
            if len(tds) == 0:
                continue

            row = []
            for td in tds:
                # Remove all mathematical formulas/elements as these mess up
                # formatting.
                for math_element in td.select("span.mwe-math-element"):
                    math_element.clear()

                # Ignore cells containing just images as this messes up
                # the table formatting. For example, consider the
                # "Creation Menu" table under the
                # "Dining Room, Combat Room, Throne Room, and Treasure Room"
                # headline in
                # https://oldschool.runescape.wiki/w/Decoration_space. Under
                # the "Decoration" column, the first column containing just the
                # images should be ignored. All of these have nested under them
                # a `span.plinkt-template` element, so these are filtered below.
                if td.find("span", class_="plinkt-template"):
                    continue

                # Alternatively, some cells containing just images are necessary
                # to parse. For example, consider the table under the
                # "Armour sets" headline in
                # https://oldschool.runescape.wiki/w/Armour_case_space. Under
                # the "Pieces" column, each row contains only images. Without
                # metadata from these images, there would be no row content. As
                # a result, these need to be parsed. These types of images we
                # need to parse *usually* have a `span.plinkp-template` element
                # nested under them, so we filter on that below.
                parsable_imgs = td.find_all("span", class_="plinkp-template")
                if len(parsable_imgs) > 0:
                    parsable_img_content = ""
                    for parsable_img in parsable_imgs:
                        parsable_img_a = parsable_img.find("a")
                        if "title" not in parsable_img_a.attrs:
                            continue
                        parsable_img_content += parsable_img_a["title"] + ", "
                    row.append(parsable_img_content[:-2])
                    continue

                # TODO(rbnsl): Abstract this out.
                # Removes annotations ([1], [c 1] etc.).
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

                # Some table data cells contain just a gold or silver star
                # indicating whether a piece of content is members-only or
                # available for free-to-play (F2P) players. Replace these images
                # with text with semantic meaning.
                members_img = td.find("img", src="/images/Member_icon.png?1de0c")
                f2p_img = td.find("img", src="/images/Free-to-play_icon.png?628ce")
                if members_img:
                    row.append("Members-only")
                    continue
                elif f2p_img:
                    row.append("Free-to-play (F2P)")
                    continue

                # Some table data cells contain a list.
                if "class" in td.attrs and "plainlist" in td["class"]:
                    row_content = ""
                    at_least_one_li = False
                    for li in td.find_all("li"):
                        row_content += li.text.strip()
                        skill = li.find("span", class_="scp")
                        if skill and "data-skill" in skill.attrs:
                            row_content += " " + skill["data-skill"]
                        row_content += " / "
                        at_least_one_li = True
                    row_content = row_content[:-3] if at_least_one_li else row_content
                    row.append(row_content)
                    continue

                # Some table data cells contain a skill icon with some text
                # representing a level requirement for that skill. We can pull
                # the two pieces of information we need (skill name + level) off
                # of `span.scp`.
                scps = td.find_all("span", class_="scp")
                if len(scps) > 0:
                    row_content = ""
                    at_least_one_scp = False
                    for scp in scps:
                        if "data-skill" in scp.attrs and "data-level" in scp.attrs:
                            at_least_one_scp = True
                            row_content += (
                                scp["data-skill"] + " " + scp["data-level"] + " / "
                            )
                    row_content = row_content[:-3] if at_least_one_scp else row_content
                    row.append(row_content)
                    continue

                # Some table data cells contain <br>s. These should be replaced
                # such that table data is comma-delimited.
                for br in td.find_all("br"):
                    br.replace_with(NavigableString(" / "))

                # Same as with headers, we don't want to consider the high alch
                # information.
                if "class" in td.attrs and "alch-column" in td["class"]:
                    continue

                # At this point, we can just parse the row content normally.
                row_content = td.text.strip()
                row_content = row_content.replace("(update)", "")
                row_content = row_content.replace(" (update)", "")
                # TODO(rbnsl): These below 3 aren't working; fix them.
                row_content = row_content.replace(" (update | poll)", "")
                row_content = row_content.replace("\n(update | poll)", "")
                row_content = row_content.replace("(update | poll)", "")

                # We might have no row content. This usually happens when the
                # table data cell just had an image that did _not_ have a
                # `.plinkt-template` class or `.plinkp-template` somewhere
                # inside it. An example of this is the "Products" table in
                # https://oldschool.runescape.wiki/w/Air_Altar. That very first
                # column with the rune/staff images needs to be ignored.
                #
                # In this case, we can just skip this row content.
                #
                # In some cases, we may have no row content BUT there is no
                # image; the cell is simply empty. We _do_ want to keep this
                # as without it, formatting of the table will be broken. For
                # example, consider the "Farming" table in:
                # https://oldschool.runescape.wiki/w/Closest... Some of the
                # cells under "Distance" are empty. If we skipped them, there
                # would be formatting issues with "Requirements" cells.
                if row_content or not td.select("a img"):
                    row.append(row_content)

            rows.append(row)

        return rows

    output = ""
    headers = _get_headers()
    rows = _get_rows()

    for row in rows:
        for i in range(len(headers)):
            header = headers[i]
            cell = row[i] if i < len(row) else ""
            output += f"{header}: {cell}, "
        output = output[:-2] + "\n"

    output += "\n"
    return output


def _parse_skill_infobox(skill_infobox):
    output = ""

    rows = skill_infobox.find_all("tr")
    for row in rows:
        # Skip header/padding rows.
        if row.find("td", class_="infobox-padding") or row.find(
            "th", class_="infobox-header"
        ):
            continue

        row_label = row.find("th")
        if row_label:
            output += row_label.text.strip()

        # For the "Level required" row, we need to extract the skill name and
        # and value. These can both be gotten off `span.scp`.
        skills_and_levels = row.find_all("span", class_="scp")
        if len(skills_and_levels) > 0:
            output += " - "
            for skl_lvl in skills_and_levels:
                if "data-skill" in skl_lvl.attrs and "data-level" in skl_lvl.attrs:
                    output += skl_lvl["data-level"] + " " + skl_lvl["data-skill"] + ", "
            output = output[:-2] + "\n"
            continue

        row_value = row.find("td")
        if row_value and row_value.text.strip():
            output += " - " + row_value.text.strip()
        output += "\n"

    output += "\n"
    return output


def _parse_unordered_list(ul):
    output = ""
    for li in ul.find_all("li", recursive=False):
        sub_ul = li.find("ul")
        if sub_ul:
            copy_ul = copy.copy(sub_ul)
            sub_ul.clear()
            output += f"* {li.text.strip()}\n"
            for sub_li in copy_ul.find_all("li"):
                output += f"  * {sub_li.text.strip()}\n"
            continue
        output += f"* {li.text.strip()}\n"
    return output + "\n"


def _parse_tabber(tabber):
    """Parses tabber <div>s.

    For example, the table under "Quests" in
    https://oldschool.runescape.wiki/w/Combat_only_pure is a tabber as it has
    multiple, clickable tabs with different information depending on which tab
    is selected.
    """
    tabs = tabber.select("div.tabbertab")
    if len(tabs) == 0:
        return ""

    output = ""
    for tab in tabs:
        # Append the tab's title before adding the tab content.
        if "data-title" in tab.attrs:
            output += tab["data-title"] + ":\n\n"

        wikitable = tab.select("table.wikitable")
        if len(wikitable) > 0:
            output += _parse_wikitable(wikitable[0])
            continue

        ul = tab.select("ul")
        if len(ul) > 0:
            output += _parse_unordered_list(ul[0])
            continue
    return output


# TODO(rbnsl): Abstract this out with how you do this in right-hand side
# infoboxes (as per `infobox_scraper.py`).
def _parse_combat_bonuses(infobox, title):
    """Parses combat bonus tables found on equipment pages."""

    class CombatBonusesState(Enum):
        ATTACK = 1
        DEFENCE = 2
        OTHER = 3
        ATTACK_SPEED_AND_RANGE = 4

    rows = infobox.find_all("tr")
    if len(rows) == 0:
        return ""

    output = ""
    cur_state = CombatBonusesState.ATTACK
    cur_bonus_headers = []
    for row in rows:
        section_header = row.find("th", class_="infobox-subheader")
        if section_header:
            section_header = section_header.text.strip()
            if "defence" in section_header.lower():
                cur_state = CombatBonusesState.DEFENCE
            elif "other" in section_header.lower():
                cur_state = CombatBonusesState.OTHER
            elif "speed" in section_header.lower():
                # Special case; handle separately as it has a different format
                cur_state = CombatBonusesState.ATTACK_SPEED_AND_RANGE
                output += "Additional weapon info" + ":\n\n"
                cur_bonus_headers.extend(["Base attack speed", "Weapon range"])
                continue
            output += section_header + ":\n\n"
            continue

        # Rows that have padding typically *just* have padding. Skip them.
        has_padding = row.find("td", class_="infobox-padding")
        if has_padding:
            continue

        bonus_types = row.find_all("th", class_="infobox-nested")
        for bonus_type in bonus_types:
            bonus_type_a = bonus_type.find("a")
            if "title" not in bonus_type_a.attrs:
                continue
            bonus_type_title = bonus_type_a["title"]
            if cur_state == CombatBonusesState.ATTACK:
                bonus_type_title += " (attack bonus)"
            elif cur_state == CombatBonusesState.DEFENCE:
                bonus_type_title += " (defence bonus)"
            elif (
                cur_state == CombatBonusesState.OTHER
                and "slot" in bonus_type_title.lower()
            ):
                bonus_type_title = "Slot"

            cur_bonus_headers.append(bonus_type_title)
            continue

        bonus_values = row.find_all("td", class_="infobox-nested")
        if len(bonus_values) != len(cur_bonus_headers):
            print(f"Oddly formatted combat bonus table in article: {title}")
            continue

        for i, bonus_value in enumerate(bonus_values):
            for br in bonus_value.find_all("br"):
                br.replace_with(NavigableString(" "))

            bv = bonus_value.text.strip()

            bv_a = bonus_value.find("a")
            if bv_a and "title" in bv_a.attrs and "slot" in bv_a["title"].lower():
                # Handle "slot"
                bv = bv_a["title"]
            elif bv_a and "title" in bv_a.attrs and "speed" in bv_a["title"].lower():
                # Handle attack speed
                attack_speed_img = bv_a.find("img")
                if (
                    attack_speed_img
                    and "alt" in attack_speed_img.attrs
                    and "speed" in attack_speed_img["alt"].lower()
                ):
                    bv = attack_speed_img["alt"].replace(".png", "")[-1]

            output += f"{cur_bonus_headers[i]}: {bv}\n"

        cur_bonus_headers = []
        output += "\n"

    return output + "\n"


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
            if (
                headline.lower() not in KNOWN_HEADLINES
                and headline.lower() not in EXCLUDED_HEADLINES
            ):
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
                if "class" in child.attrs and "tabber" in child["class"]:
                    output += _parse_tabber(child)
                    continue

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
                output += _parse_unordered_list(child)

            case numbered_list_tag if numbered_list_tag in ["dl", "ol"]:
                for i, li in enumerate(child.find_all("li")):
                    output += f"{i + 1}. {li.text.strip()}\n"
                output += "\n"

            case "table":
                if "class" not in child.attrs:
                    continue
                # Constitutes the majority of tables in the wiki. An example is
                # the "Drops" tables in:
                # https://oldschool.runescape.wiki/w/Zulrah.
                if "wikitable" in child["class"]:
                    output += _parse_wikitable(child)
                    continue
                # "Skill boxes" usually denoting 1+ skill levels required to
                # do or make something. An example is:
                # https://oldschool.runescape.wiki/w/A_wooden_log, which has an
                # Agility skill box.
                if "infobox" in child["class"] and "skill-info" in child["class"]:
                    output += _parse_skill_infobox(child)
                    continue
                # "Infobox bonuses" are tables depicting the combat bonuses for
                # equipment. https://oldschool.runescape.wiki/w/Abyssal_bludgeon
                # for an example; the infobox bonus table appears near the top.
                if "infobox" in child["class"] and "infobox-bonuses" in child["class"]:
                    output += _parse_combat_bonuses(child, title)
                    continue

    return output.strip()
