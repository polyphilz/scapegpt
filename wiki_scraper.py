import requests
from bs4 import BeautifulSoup
from datetime import datetime

# Send a GET request
url = "https://oldschool.runescape.wiki/w/Kourend_map_display_case"
res = requests.get(url)

# Parse HTML content using BeautifulSoup
soup = BeautifulSoup(res.content, "html.parser")

# Get the page title
title = soup.find("h1", id="firstHeading").text.strip()

# Get the content section
content_section = soup.find("div", id="bodyContent").find("div", id="mw-content-text")

# Get the text description of the item
description = (
    content_section.find("div", class_="mw-parser-output").find("p").text.strip()
)

# Find the table element
content_tables = soup.find_all('table', {'class': 'wikitable'})

# Extract the data from the table rows
rows = table.find_all('tr')
data = []
for row in rows[1:]:
    cols = row.find_all('td')
    badge_image = cols[0].find('img')['src']
    badge_name = cols[1].get_text().strip()
    badge_level = cols[2].get_text().strip()
    badge_xp = cols[3].get_text().strip()
    data.append((badge_image, badge_name, badge_level, badge_xp))

# Format the data as markdown and write to a file
with open('x.md', 'w') as f:
    f.write('# Badge Summary\n\n')
    f.write('| Badge | Level | Steam XP |\n')
    f.write('|-------|-------|----------|\n')
    for row in data:
        f.write(f'| ![badge]({row[0]}) | {row[1]} | {row[2]} | {row[3]} |\n')




# Extract table data
table = soup.find("table", {"class": "infobox"})

# Get the release date from the infobox table
rows = table.find_all("tr")
info = {}
release_date = ""
for row in rows:
    cols = row.find_all(["th", "td"])
    if len(cols) == 2:
        if cols[0].text.strip() == "Released":
            release_date = (
                cols[1].text.strip().replace(" (Update)", "").replace("(Update)", "")
            )
        else:
            info[cols[0].text.strip()] = cols[1].text.strip()





# Generate markdown output
output = f"# {title}\n\n## Content\n\n{description}\n\n## Information\n\n"
if release_date:
    output += f"{title} was released on {release_date}, "
else:
    output += f"{title} does not have a release date, "
output += f"is {'members-only' if info.get('Members', 'Yes') == 'Yes' else 'not members-only (it is accessible by free-to-play players)'}, "
if info["Quest"] == "No":
    output += "does not belong to any quest, "
else:
    output += f"belongs to the quest {info['Quest']}, "
output += f"is located in {info.get('Location', 'N/A')}, has {'no' if info.get('Options', 'N/A') == 'None' else ''} options, "
output += f"and has the examine text '{info.get('Examine', 'N/A')}'.\n"

# Save the output to a file
filename = title.lower().replace(" ", "-") + ".md"
with open(filename, "w", encoding="utf-8") as f:
    f.write(output)

print(f"Output saved to {filename}")
