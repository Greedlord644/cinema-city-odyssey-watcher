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

  response = requests.post(
    url,
    json={
        "chat_id": chat_id,
        "text": message,
        "disable_web_page_preview": True
    },
    timeout=15
)

print(
    f"Telegram response: {response.text}",
    flush=True
)

response.raise_for_status()


def load_state():
    if not os.path.exists(STATE_FILE):
        return []

    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(data):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_events():

    start = datetime.now()

    # Cinema City běžně zveřejňuje program pouze několik týdnů dopředu.
    # 45 dní je bezpečná rezerva.
    days_to_check = 45

    print(
        f"IMAX watcher started. Checking {days_to_check} days",
        flush=True
    )

    results = []

    for i in range(days_to_check):

        date = (
            start + timedelta(days=i)
        ).strftime("%Y-%m-%d")

        url = (
            API_BASE
            + date
            + "?attr=&lang=cs_CZ"
        )

        try:
            response = requests.get(
                url,
                timeout=15
            )

            response.raise_for_status()

            data = response.json()

        except Exception as e:
            print(
                f"API error {date}: {e}",
                flush=True
            )
            continue


        events = (
            data
            .get("body", {})
            .get("events", [])
        )

        for event in events:

            if event.get("cinemaId") != CINEMA_ID:
                continue

            attributes = event.get(
                "attributeIds",
                []
            )

            if (
                "70-mm" in attributes
                and "subbed" in attributes
                and "original-lang-en" in attributes
            ):
                results.append(
                    {
                        "id": event["id"],
                        "date": event["eventDateTime"],
                        "hall": event.get("auditorium"),
                        "availability": event.get(
                            "availabilityRatio"
                        ),
                        "booking": event.get(
                            "bookingLink"
                        )
                    }
                )


    print(
        f"Found {len(results)} IMAX 70mm events",
        flush=True
    )

    return results


def main():

    events = get_events()

    current_ids = [
        event["id"]
        for event in events
    ]

    old_ids = load_state()


    new_events = [
        event
        for event in events
        if event["id"] not in old_ids
    ]


    if new_events:

        message = (
            "🎬 NOVÁ IMAX 70mm projekce!\n\n"
            "Cinema City Flora\n"
            "IMAX VOLVO\n\n"
        )

        for event in new_events:

            message += (
                f"📅 {event['date']}\n"
                f"🏛 {event['hall']}\n"
                f"🔗 {event['booking']}\n\n"
            )


        send_telegram(message)

        print(
            "Telegram notification sent",
            flush=True
        )

    else:

        print(
            "No new events",
            flush=True
        )


    save_state(current_ids)


if __name__ == "__main__":
    main()
