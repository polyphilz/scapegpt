from bs4 import NavigableString
from collections import OrderedDict
from enum import Enum


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


class CombatStatsState(Enum):
    COMBAT_STATS = 1
    AGGRESSIVE_STATS = 2
    DEFENSIVE_STATS = 3


def get_infobox(soup, title):
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
                            combat_stats_header_title = "Monster defensive stab bonus"
                        elif combat_stats_header_title == "Slash":
                            combat_stats_header_title = "Monster defensive slash bonus"
                        elif combat_stats_header_title == "Crush":
                            combat_stats_header_title = "Monster defensive crush bonus"
                        elif combat_stats_header_title == "Magic":
                            combat_stats_header_title = "Monster defensive magic bonus"
                        elif combat_stats_header_title == "Ranged":
                            combat_stats_header_title = "Monster defensive ranged bonus"

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
