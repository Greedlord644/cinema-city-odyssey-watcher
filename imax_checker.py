import requests
import os
import json
from datetime import datetime

FILM_ID = "7268s2r"
CINEMA_ID = "1052"

API_URL = (
    "https://www.cinemacity.cz/cz/data-api-service/v1/"
    "quickbook/10101/groups/with-film/"
    f"{FILM_ID}/until/2027-07-26"
    "?attr=&lang=cs_CZ"
)


def send_telegram(message):
    token = os.environ["TELEGRAM_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    requests.post(
        url,
        json={
            "chat_id": chat_id,
            "text": message
        }
    )


def check():
    r = requests.get(API_URL, timeout=20)
    r.raise_for_status()

    data = r.json()

    events = data["body"]["events"]

    matches = []

    for event in events:

        if event["cinemaId"] != CINEMA_ID:
            continue

        attrs = event.get("attributeIds", [])

        if "70-mm" not in attrs:
            continue

        if "subbed" not in attrs:
            continue

        if "original-lang-en" not in attrs:
            continue

        matches.append(event)

    if matches:

        msg = "🎬 Nalezen 70mm IMAX Flora!\n\n"

        for e in matches:
            msg += (
                f"{e['eventDateTime']}\n"
                f"Sál: {e['auditorium']}\n"
                f"Volno: {round(e['availabilityRatio']*100,1)} %\n"
                f"{e['bookingLink']}\n\n"
            )

        send_telegram(msg)


if __name__ == "__main__":
    check()
