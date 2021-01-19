import os
import time
import pickle
import json
import requests
import telegram

url = "https://jobs.dsi.infn.it./data.php"
data_folder = os.getenv("DATA_PATH", "/data/")
users_json_file = os.getenv("USERS_JSON", data_folder + "users.json")
check_period = int(os.getenv("CHECK_PERIOD", 600))
token = os.getenv("TELEGRAM_TOKEN", None)

if token is None:
    print("ERROR: TELEGRAM_TOKEN env variable is required.")
    exit(1)


def download_webpage(url):
    try:
        r = requests.get(url)
        r.raise_for_status()

        data = r.json()

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

# offer = {
#  unique_id: unique ID of job offers
#  tipo: type of job
#  numero: job offer number
#  titolo: title
#  scadenza: expiry date for application
#  numero_posti*: number of available places
#  durata*: job duration
#  url_bando: URL to job offer notice
# } *optional
def compose_msg(offer):
    msg = f"<b>{offer.get('tipo', 'OFFERTA DI LAVORO')}</b>\n"
    msg += f"{offer.get('titolo', 'Titolo non disponibile')}\n"
    
    if 'numero_posti' in offer:
        msg += f"Posti: {offer['numero_posti']}\n"
    if 'durata' in offer:
        msg += f"Durata: {offer['durata']}\n"
    
    msg += f"\nScadenza: {offer.get('scadenza', 'non disponibile')}\n"    
    msg += f"<a href=\"{offer.get('url_bando', '#')}\">Scarica il bando {offer.get('numero', '')}</a>"
    return msg


def find_new_offers(data, old_data):
    curr_ids = set([d["unique_id"] for d in data])
    old_ids = set([d["unique_id"] for d in old_data])

    new_ids = list(curr_ids - old_ids)
    new_offers = [d for d in data if d["unique_id"] in new_ids]

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
        data = download_webpage(url)
        if data is None:
            print("Could not download data")
            continue

        old_data = load_old_data(data_folder + "/data.pkl")
        save_data(data_folder + "/data.pkl", data)

        if old_data is None:
            print("Could not load old data")
            continue

        new_offers = find_new_offers(data, old_data)
        for offer in new_offers:
            msg = compose_msg(offer)
            print(f"Sending offer to {len(users.values())} users:\n{msg}")
            send_messages(users, msg)

        time.sleep(check_period)
