import os
import time
import re
import pickle
import json
import requests
from bs4 import BeautifulSoup
import telegram

url = "https://jobs.dsi.infn.it/"
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36"
}
date_pattern = re.compile(r"(\d+-\d+-\d+)")
users_json_file = "/data/users.json"
check_period = int(os.getenv("CHECK_PERIOD", 600))
token = os.getenv("TELEGRAM_TOKEN", None)

if token is None:
    print("ERROR: TELEGRAM_TOKEN env variable is required.")
    exit(1)


def download_webpage(url, headers):
    try:
        r = requests.get(url, headers=headers)
        r.raise_for_status()

        webpage = r.text

    except requests.exceptions.ConnectionError:
        print("Connection error")
        return None
    except requests.exceptions.HTTPError:
        print("HTTP error: [%d]" % (r.status_code))
        return None
    except requests.exceptions.Timeout:
        print("Connection timeout")
        return None
    except requests.exceptions.TooManyRedirects:
        print("Too many redirects")
        return None
    except requests.exceptions.RequestException as e:
        print("Unknown request error")
        return None

    return BeautifulSoup(webpage, "html.parser")


def mine_data(soup):
    data = {}

    tables = soup.find_all("table")
    for table in tables:
        # Get table name
        table_name = table.find_previous("h5").text.split(":")[0]

        # List of column titles
        table_heads = table.find("thead").find("tr").find_all("th")
        heads = [th.text.strip() for th in table_heads]

        items = []
        table_body = table.find("tbody")
        rows = table_body.find_all("tr")
        for row in rows:
            item = {}
            cols = row.find_all("td")
            for i, col in enumerate(cols):
                links = []
                for link in col.find_all("a"):
                    links.append(link.extract())
                text = col.text.strip()
                item[heads[i]] = {"links": links, "text": text}

            items.append(item)
        data[table_name] = items
    return data


def load_old_data(filename):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        print("Picke file not found")
        return None


def save_data(filename, data):
    with open(filename, "wb") as f:
        pickle.dump(data, f)


def compose_msg(offer, section_name):
    msg = f"<b>{section_name}</b>\n"

    title_text = offer["TITOLO"]["text"]
    title_text = re.sub("\n{2,}", "\n", title_text)
    title_text = re.sub(" {2,}", " ", title_text)
    title_text = title_text.replace("\n ", "\n")
    msg += title_text + "\n"

    for link in offer["BANDO"]["links"]:
        link_string = link.string
        link_string = re.sub("\n", " ", link_string)
        link_string = re.sub(" {2,}", " ", link_string)
        link.string = link_string
        msg += "\n" + str(link).strip()

    msg += "\n"
    if re.search(date_pattern, offer["BANDO"]["text"]):
        msg += offer["BANDO"]["text"]
    else:
        msg += f"Scadenza: {offer['SCADENZA']['text']}"

    return msg


def find_new_offers(data, old_data):
    new_offers = {}
    for section_name, section in data.items():
        new_offers[section_name] = []
        for offer in section:
            if offer not in old_data.get(section_name, []):
                print("New offer")
                new_offers[section_name].append(offer)
    return new_offers


def send_messages(users, msg):
    for user_id in users.values():
        try:
            bot.sendMessage(
                chat_id=user_id, text=msg, parse_mode=telegram.ParseMode.HTML
            )
            time.sleep(0.05)
        except Exception:
            print(f"Could not send message to user {user_id}.")


if __name__ == "__main__":
    print("Bot waking up...")
    users = {}
    with open(users_json_file, "r") as f:
        users = json.load(f)

    bot = telegram.Bot(token=token)

    while True:
        soup = download_webpage(url, headers)
        if soup is None:
            print("Could not download webpage")
            continue

        data = mine_data(soup)
        old_data = load_old_data("/data/data.pkl")
        save_data("/data/data.pkl", data)

        if old_data is None:
            print("Could not load old data")
            continue

        new_offers = find_new_offers(data, old_data)
        #new_offers["ASSEGNI DI RICERCA"].append(data["ASSEGNI DI RICERCA"][0])
        for section_name, section in new_offers.items():
            for offer in section:
                msg = compose_msg(offer, section_name)
                print(f"Sending offer to {len(users.values())} users:\n{msg}")
                send_messages(users, msg)

        time.sleep(check_period)
