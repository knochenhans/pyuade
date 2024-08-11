import hashlib
from pathlib import Path
import re

from bs4 import BeautifulSoup
from platformdirs import user_config_dir
import requests

from uade import Song
from utils.log import LOG_TYPE, log


def scrape_modarchive(username: str, song: Song) -> Song | None:
    license_file = Path(user_config_dir(username)) / "modarchive-api.key"

    if not license_file.exists():
        log(LOG_TYPE.ERROR, "No modarchive-api.key found in config folder!")
        return None

    with open(license_file, "r") as f:
        api_key = f.read()

    with requests.Session() as session:
        md5 = hashlib.md5()

        log(
            LOG_TYPE.INFO,
            f"Looking up {song.song_file.filename} in ModArchive.",
        )

        with open(song.song_file.filename, "rb") as f:
            data = f.read()

            if data:
                md5.update(data)

                md5_request = f"request=search&type=hash&query={md5.hexdigest()}"

                query = f"https://modarchive.org/data/xml-tools.php?key={api_key}&{md5_request}"

                response = session.get(query)

                xml_tree = ElementTree.fromstring(response.content)

                xml_module = xml_tree.find("module")

                if xml_module:
                    if int(xml_tree.find("results").text) > 0:
                        log(
                            LOG_TYPE.SUCCESS,
                            f"ModArchive Metadata found for {song.song_file.filename}.",
                        )
                        xml_artist_info = xml_module.find("artist_info")

                        for artist_idx in range(
                            int(xml_artist_info.find("artists").text)
                        ):
                            xml_artist = xml_artist_info.find("artist")

                            song.song_file.author = xml_artist.find("alias").text

                            log(
                                LOG_TYPE.INFO,
                                f"Artist {song.song_file.author} found for {song.song_file.filename}.",
                            )

                    else:
                        log(
                            LOG_TYPE.WARNING,
                            f"More than 1 results for md5 of {song.song_file.filename} found!",
                        )

                else:
                    log(
                        LOG_TYPE.WARNING,
                        f"No ModArchive results found for {song.song_file.filename}!",
                    )

    return song


def scrape_modland(song: Song, column: str) -> str:
    md5 = hashlib.md5()

    with open(song.song_file.filename, "rb") as f:
        data = f.read()

        if data:
            md5.update(data)

            url = (
                "https://www.exotica.org.uk/mediawiki/index.php?title=Special%3AModland&md=qsearch&qs="
                + md5.hexdigest()
            )

            response = requests.get(url)
            if response.status_code == 200:
                website = requests.get(url)
                results = BeautifulSoup(website.content, "html5lib")

                table = results.find("table", id="ml_resultstable")
                if table:
                    search_results = table.find("caption")

                    pattern = re.compile("^Search - ([0-9]+) result.*?$")
                    match = pattern.match(search_results.text)
                    if match:
                        if int(match.group(1)) > 0:
                            # webbrowser.open(url, new=2)
                            table_body = table.find("tbody")

                            author_col_nr = -1

                            # Find out which row contains author (just to make a little more flexible)

                            table_rows = table_body.find_all("tr")
                            for table_row in table_rows:
                                cols = table_row.find_all("th")

                                for c, col in enumerate(cols):
                                    header_name = col.find("a")

                                    if header_name.text.strip() == column:
                                        author_col_nr = c
                                        break

                                if author_col_nr >= 0:
                                    tds = table_row.find_all("td")

                                    if tds:
                                        td = tds[author_col_nr]
                                        return td.find("a").text.strip()
    return ""


def scrape_msm(song: Song) -> dict:
    # Lookup in .Mod Sample Master database via sha1 and return data
    return_data = {}

    sha1 = hashlib.sha1()

    with open(song.song_file.filename, "rb") as f:
        data = f.read()

        if data:
            sha1.update(data)

            url = (
                "https://modsamplemaster.thegang.nu/module.php?sha1=" + sha1.hexdigest()
            )

            response = requests.get(url)
            if response.status_code == 200:
                website = requests.get(url)
                results = BeautifulSoup(website.content, "html5lib")

                page = results.find("div", class_="page")
                if page:
                    # Check if we have a result
                    name = page.find("h1")

                    if name.text:
                        return_data["name"] = name.text

                        # Find h1 "Links"
                        links = page.find("h1", string="Links")
                        details = links.find_next_sibling("div")

                        if details:
                            # Read all list items
                            list_items = details.find_all("li")

                            urls = []

                            # Loop through all list items and add them to the return_data
                            for item in list_items:
                                urls.append(item.text)

                            return_data["urls"] = urls

    return return_data


def lookup_msm(song: Song) -> str:
    # Experimental lookup in .Mod Sample Master database

    sha1 = hashlib.sha1()

    with open(song.song_file.filename, "rb") as f:
        data = f.read()

        if data:
            sha1.update(data)

            url = (
                "https://modsamplemaster.thegang.nu/module.php?sha1=" + sha1.hexdigest()
            )

            response = requests.get(url)
            if response.status_code == 200:
                website = requests.get(url)
                results = BeautifulSoup(website.content, "html5lib")

                page = results.find("div", class_="page")
                if page:
                    name = page.find("h1")

                    if name.text:
                        return name.text
    return ""
