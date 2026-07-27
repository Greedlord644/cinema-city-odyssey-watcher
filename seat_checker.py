import requests
import os


PRESENTATION_ID = "220780"

SEATS_URL = (
    "https://tickets.cinemacity.cz/api/seats/seats-statusV2"
)


def parse_cookies(cookie_string):

    cookies = {}

    for item in cookie_string.split(";"):

        item = item.strip()

        if "=" not in item:
            continue

        key, value = item.split("=", 1)

        cookies[key] = value

    return cookies



def get_seats():

    cookies_raw = os.environ["CINEMA_COOKIES"]
    uuid = os.environ["CINEMA_UUID"]

    cookies = parse_cookies(
        cookies_raw
    )

    print(
        "Cookies loaded:",
        len(cookies)
    )

    params = {
        "presentationId": PRESENTATION_ID,
        "venueTypeId": "1",
        "isReserved": "1"
    }

    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "cs-CZ,cs;q=0.9",
        "referer": (
            f"https://tickets.cinemacity.cz/"
            f"order/{PRESENTATION_ID}?lang=cs"
        ),
        "user-agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/150.0.0.0 Safari/537.36"
        ),
        "uuid": uuid
    }

    response = requests.get(
        SEATS_URL,
        params=params,
        headers=headers,
        cookies=cookies,
        timeout=15
    )

    print(
        "STATUS:",
        response.status_code
    )

    response.raise_for_status()

    return response.json()



def parse_seats(data):

    available = []

    for key, status in data["seats"].items():

        if status == 0:

            _, seat, row = key.split("_")

            available.append(
                {
                    "row": int(row),
                    "seat": int(seat)
                }
            )

    return available



def find_pairs(seats):

    pairs = []

    rows = {}

    for seat in seats:

        rows.setdefault(
            seat["row"],
            []
        ).append(
            seat["seat"]
        )


    for row, numbers in rows.items():

        if row <= 5:
            continue

        if row == 12:
            continue

        numbers.sort()

        for i in range(len(numbers)-1):

            first = numbers[i]
            second = numbers[i + 1]

            if second != first + 1:
                continue

            if first <= 10:
                continue

            if second >= 35:
                continue

            pairs.append(
                {
                    "row": row,
                    "seats": (
                        first,
                        second
                    )
                }
            )

    return pairs



def main():

    print(
        "Cinema City seat checker"
    )

    print(
        "Presentation:",
        PRESENTATION_ID
    )

    data = get_seats()

    seats = parse_seats(
        data
    )

    print(
        "Free seats:",
        len(seats)
    )

    pairs = find_pairs(
        seats
    )

    if pairs:

        print(
            "FOUND SUITABLE PAIRS:"
        )

        for pair in pairs:

            print(
                f"Row {pair['row']} "
                f"Seats {pair['seats'][0]} + "
                f"{pair['seats'][1]}"
            )

    else:

        print(
            "No suitable pairs found"
        )


if __name__ == "__main__":
    main()
