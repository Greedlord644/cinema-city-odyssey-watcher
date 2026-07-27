import requests
import os
import json
from datetime import datetime


PRESENTATION_ID = "220780"

SEATS_URL = (
    "https://tickets.cinemacity.cz/api/seats/seats-statusV2"
)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


# podmínky:
# - ignorovat řady 1-5
# - ignorovat řadu 12
# - ignorovat krajních 10 míst zleva/zprava
# - hledat pouze 2 sousední volná místa


def get_seats():

    params = {
        "presentationId": PRESENTATION_ID,
        "venueTypeId": "1",
        "isReserved": "1"
    }

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/126.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://tickets.cinemacity.cz/",
        "Origin": "https://tickets.cinemacity.cz"
    }

    response = requests.get(
        SEATS_URL,
        params=params,
        headers=headers,
        timeout=15
    )

    response.raise_for_status()

    return response.json()


def parse_seats(data):

    seats = data.get("seats", {})

    available = []

    for key, status in seats.items():

        if status != 0:
            continue

        try:
            cinema, seat, row = key.split("_")

            available.append(
                {
                    "seat": int(seat),
                    "row": int(row)
                }
            )

        except Exception:
            continue

    return available


def find_good_pairs(seats):

    good_pairs = []

    rows = {}

    for seat in seats:
        rows.setdefault(
            seat["row"],
            []
        ).append(
            seat["seat"]
        )


    for row, numbers in rows.items():

        # ignorované řady
        if row <= 5:
            continue

        if row == 12:
            continue


        numbers.sort()


        for i in range(len(numbers)-1):

            first = numbers[i]
            second = numbers[i+1]


            # musí být vedle sebe
            if second != first + 1:
                continue


            # ignorace krajů
            if first <= 10:
                continue

            # předpoklad šířky sálu - pravý kraj
            if second >= 35:
                continue


            good_pairs.append(
                {
                    "row": row,
                    "seats": [
                        first,
                        second
                    ]
                }
            )


    return good_pairs


def send_telegram(message):

    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram není nastaven")
        return


    url = (
        f"https://api.telegram.org/"
        f"bot{TELEGRAM_TOKEN}/sendMessage"
    )

    requests.post(
        url,
        json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message
        },
        timeout=10
    )


def main():

    print("Cinema City seat checker")
    print(
        "Presentation:",
        PRESENTATION_ID
    )

    data = get_seats()

    seats = parse_seats(data)

    print(
        "Available seats:",
        len(seats)
    )

    pairs = find_good_pairs(seats)


    if pairs:

        message = (
            "🎬 IMAX Flora - nalezena vhodná místa!\n\n"
        )

        for pair in pairs:
            message += (
                f"Řada {pair['row']}, "
                f"místa {pair['seats'][0]} + "
                f"{pair['seats'][1]}\n"
            )

        print(message)

        send_telegram(message)

    else:

        print(
            "Nenalezena žádná vhodná dvojice."
        )


if __name__ == "__main__":
    main()
