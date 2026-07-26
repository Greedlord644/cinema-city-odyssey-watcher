import os
import json
import requests
from datetime import datetime, timedelta


FILM_ID = "7268s2r"
CINEMA_ID = "1052"

STATE_FILE = "state.json"

BASE_URL = (
    "https://www.cinemacity.cz/cz/data-api-service/v1/"
    "quickbook/10101/cinema-events/in-group/prague/"
    f"with-film/{FILM_ID}/at-date/"
)


def send_telegram(message):
    token = os.environ["TELEGRAM_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]

    requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": message,
            "disable_web_page_preview": True
        },
        timeout=15
    )


def load_state():
    if not os.path.exists(STATE_FILE):
        return []

    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(events):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(events, f, indent=2)


def get_program_end_date():

    url = (
        "https://www.cinemacity.cz/cz/data-api-service/v1/"
        "quickbook/10101/groups/with-film/"
        f"{FILM_ID}/until/2027-12-31"
        "?attr=&lang=cs_CZ"
    )

    r = requests.get(url, timeout=15)
    r.raise_for_status()

    # zatím používáme bezpečný rozsah
    return datetime.now() + timedelta(days=45)


def get_events():

    start = datetime.now()
    end = get_program_end_date()

    days = (end - start).days

    print(f"Checking {days} days")

    results = []

    for i in range(days + 1):

        date = (
            start + timedelta(days=i)
        ).strftime("%Y-%m-%d")

        url = BASE_URL + date + "?attr=&lang=cs_CZ"

        try:
            r = requests.get(url, timeout=15)
            r.raise_for_status()
            data = r.json()

        except Exception:
            continue


        for event in data.get("body", {}).get("events", []):

            if event.get("cinemaId") != CINEMA_ID:
                continue

            attrs = event.get("attributeIds", [])

            if (
                "70-mm" in attrs
                and "subbed" in attrs
                and "original-lang-en" in attrs
            ):
                results.append(event)


    print(f"Found {len(results)} IMAX 70mm events")

    return results


def main():

    events = get_events()

    current = [
        e["id"]
        for e in events
    ]

    old = load_state()

    new = [
        e for e in events
        if e["id"] not in old
    ]


    if new:

        msg = "🎬 Nová IMAX 70mm projekce Flora\n\n"

        for e in new:
            msg += (
                f"📅 {e['eventDateTime']}\n"
                f"🏛 {e['auditorium']}\n"
                f"🎟 {e['bookingLink']}\n\n"
            )

        send_telegram(msg)

    else:
        print("No new events")


    save_state(current)


if __name__ == "__main__":
    main()
