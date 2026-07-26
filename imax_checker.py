import os
import json
import requests
from datetime import datetime, timedelta


FILM_ID = "7268s2r"
CINEMA_ID = "1052"

FILM_URL = "https://www.cinemacity.cz/films/odyssea/7268s2r"

STATE_FILE = "state.json"

API_BASE = (
    "https://www.cinemacity.cz/cz/data-api-service/v1/"
    "quickbook/10101/cinema-events/in-group/prague/"
    f"with-film/{FILM_ID}/at-date/"
)


def send_telegram(message):

    token = os.environ["TELEGRAM_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]

    url = (
        f"https://api.telegram.org/"
        f"bot{token}/sendMessage"
    )

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
        return None

    with open(
        STATE_FILE,
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)


def save_state(data):

    with open(
        STATE_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False
        )


def format_datetime(value):

    dt = datetime.fromisoformat(value)

    return (
        dt.strftime("%d.%m.%Y"),
        dt.strftime("%H:%M")
    )


def get_events():

    start = datetime.now()

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


        except Exception as error:

            print(
                f"API error {date}: {error}",
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
                        "datetime": event["eventDateTime"],
                        "hall": event.get(
                            "auditorium"
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


    current = {
        event["id"]: event
        for event in events
    }


    old = load_state()


    # první běh pouze uloží aktuální stav
    if old is None:

        save_state(current)

        print(
            "First run. State saved. No notification sent.",
            flush=True
        )

        return


    new_events = [
        event
        for event_id, event in current.items()
        if event_id not in old
    ]


    if new_events:

        message = (
            "🎬 NOVÁ IMAX 70mm projekce!\n\n"
            "🏛 Cinema City Flora\n"
            "🎞 IMAX 70mm\n\n"
        )


        for event in new_events:

            date, time = format_datetime(
                event["datetime"]
            )

            message += (
                f"📅 {date}\n"
                f"🕒 {time}\n"
                f"🏟 {event['hall']}\n\n"
            )


        message += (
            "🔗 Film:\n"
            f"{FILM_URL}"
        )


        if len(message) > 4000:

            message = (
                "🎬 Nové IMAX 70mm projekce!\n\n"
                f"Počet nových termínů: {len(new_events)}\n\n"
                "🔗 Film:\n"
                f"{FILM_URL}"
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


    save_state(current)



if __name__ == "__main__":
    main()
