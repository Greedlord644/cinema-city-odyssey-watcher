import requests
import os
from datetime import datetime, timedelta


FILM_ID = "7268s2r"
CINEMA_ID = "1052"

DAYS_TO_CHECK = 45


FILM_URL = (
    "https://www.cinemacity.cz/films/odyssea/7268s2r"
)


EVENTS_API = (
    "https://www.cinemacity.cz/cz/data-api-service/v1/"
    "quickbook/10101/cinema-events/in-group/prague/"
    f"with-film/{FILM_ID}/at-date/"
)


SEATS_API = (
    "https://tickets.cinemacity.cz/api/seats/"
    "seats-statusV2"
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



def get_headers():

    uuid = os.environ["CINEMA_UUID"]

    return {
        "accept": "application/json, text/plain, */*",
        "accept-language": "cs-CZ,cs;q=0.9",
        "user-agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/150.0.0.0 Safari/537.36"
        ),
        "uuid": uuid
    }



def get_cookies():

    return parse_cookies(
        os.environ["CINEMA_COOKIES"]
    )



def format_datetime(value):

    dt = datetime.fromisoformat(
        value.replace("Z", "+00:00")
    )

    return dt.strftime(
        "%d.%m.%Y %H:%M"
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

    response.raise_for_status()



def get_imax_events():

    events = []

    start = datetime.now()


    for i in range(DAYS_TO_CHECK):

        date = (
            start + timedelta(days=i)
        ).strftime("%Y-%m-%d")


        url = (
            EVENTS_API
            + date
            + "?attr=&lang=cs_CZ"
        )


        response = requests.get(
            url,
            timeout=15
        )

        response.raise_for_status()


        data = response.json()


        for event in (
            data
            .get("body", {})
            .get("events", [])
        ):

            if str(event.get("cinemaId")) != CINEMA_ID:
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

                events.append(
                    {
                        "id": event["id"],
                        "date": event["eventDateTime"]
                    }
                )


    return events



def get_seats(presentation_id):

    params = {
        "presentationId": presentation_id,
        "venueTypeId": "1",
        "isReserved": "1"
    }


    response = requests.get(
        SEATS_API,
        params=params,
        headers=get_headers(),
        cookies=get_cookies(),
        timeout=15
    )


    response.raise_for_status()


    return response.json()



def parse_free_seats(data):

    result = []


    for key, status in data.get("seats", {}).items():

        if status != 0:
            continue


        try:

            _, seat, row = key.split("_")

            result.append(
                {
                    "row": int(row),
                    "seat": int(seat)
                }
            )

        except Exception:
            continue


    return result



def is_allowed(row, seat):

    if row <= 5:
        return False


    if row == 12:
        return False


    if seat <= 10:
        return False


    if seat >= 31:
        return False


    return True



def find_pairs(seats):

    pairs = []

    rows = {}


    for seat in seats:

        if not is_allowed(
            seat["row"],
            seat["seat"]
        ):
            continue


        rows.setdefault(
            seat["row"],
            []
        ).append(
            seat["seat"]
        )


    for row, numbers in rows.items():

        numbers.sort()


        for i in range(len(numbers)-1):

            first = numbers[i]
            second = numbers[i + 1]


            if second == first + 1:

                pairs.append(
                    {
                        "row": row,
                        "seats": [
                            first,
                            second
                        ]
                    }
                )


    return pairs



def main():

    # DOČASNÝ TEST TELEGRAMU
    send_telegram(
        "🧪 Test Telegramu - Seat Checker funguje."
    )


    print(
        "Kontrola míst Cinema City IMAX"
    )


    events = get_imax_events()


    print(
        "Nalezeno IMAX 70mm projekcí:",
        len(events)
    )


    notifications = []


    for event in events:

        print(
            "Kontrola:",
            event["id"],
            format_datetime(event["date"])
        )


        try:

            data = get_seats(
                event["id"]
            )


            free = parse_free_seats(
                data
            )


            pairs = find_pairs(
                free
            )


            for pair in pairs:

                notifications.append(
                    {
                        "date": format_datetime(
                            event["date"]
                        ),
                        "row": pair["row"],
                        "seats": pair["seats"]
                    }
                )


        except Exception as error:

            print(
                "CHYBA:",
                error
            )


    if notifications:

        message = (
            "🎬 Uvolněná místa IMAX Odyssea\n\n"
            "🏛 Cinema City Flora\n\n"
        )


        for item in notifications:

            message += (
                f"📅 {item['date']}\n"
                f"💺 Řada {item['row']}, "
                f"místa "
                f"{item['seats'][0]} + "
                f"{item['seats'][1]}\n\n"
            )


        message += (
            "🔗 "
            + FILM_URL
        )


        send_telegram(
            message
        )

        print(
            "Telegram notifikace odeslána"
        )


    else:

        print(
            "Nejsou žádná vhodná místa"
        )



if __name__ == "__main__":
    main()
