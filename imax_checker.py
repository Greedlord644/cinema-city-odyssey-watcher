import os
import json
import requests
from datetime import datetime, timedelta


FILM_ID = "7268s2r"
CINEMA_ID = "1052"

STATE_FILE = "state.json"

API_BASE = (
    "https://www.cinemacity.cz/cz/data-api-service/v1/"
    "quickbook/10101/cinema-events/in-group/prague/"
    f"with-film/{FILM_ID}/at-date/"
)


def send_telegram(message):
    token = os.environ["TELEGRAM_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    requests.post(
        url,
        json={
            "chat_id": chat_id,
            "text": message,
            "disable_web_page_preview": True
        },
        timeout=20
    )


def load_state():
    if not os.path.exists(STATE_FILE):
        return []

    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(data):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_relevant_events():
    results = []

    today = datetime.now()

    # kontrolujeme cca rok dopředu
    for i in range(0, 365):

        date = (today + timedelta(days=i)).strftime("%Y-%m-%d")

        url = (
            API_BASE
            + date
            + "?attr=&lang=cs_CZ"
        )

        try:
            response = requests.get(url, timeout=20)
            response.raise_for_status()
            data = response.json()

        except Exception:
            continue


        body = data.get("body", {})

        events = body.get("events", [])

        for event in events:

            if event.get("cinemaId") != CINEMA_ID:
                continue

            attrs = event.get("attributeIds", [])

            if "70-mm" not in attrs:
                continue

            if "subbed" not in attrs:
                continue

            if "original-lang-en" not in attrs:
                continue


            results.append(
                {
                    "id": event["id"],
                    "date": event["eventDateTime"],
                    "hall": event.get("auditorium"),
                    "availability": event.get("availabilityRatio"),
                    "booking": event.get("bookingLink")
                }
            )

    return results


def main():

    current = get_relevant_events()

    current_ids = [
        x["id"]
        for x in current
    ]

    old_ids = load_state()

    new_events = [
        x for x in current
        if x["id"] not in old_ids
    ]


    if new_events:

        message = (
            "🎬 NOVÁ IMAX 70mm projekce\n\n"
            "Cinema City Flora\n\n"
        )

        for event in new_events:

            free = event["availability"]

            if free is not None:
                free = round(free * 100, 1)
                free_text = f"{free}% volných míst"
            else:
                free_text = ""

            message += (
                f"📅 {event['date']}\n"
                f"🏛 {event['hall']}\n"
                f"🎟 {free_text}\n"
                f"{event['booking']}\n\n"
            )

        send_telegram(message)


    save_state(current_ids)


if __name__ == "__main__":
    main()
