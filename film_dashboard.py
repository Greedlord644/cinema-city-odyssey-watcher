import os
import requests
from datetime import datetime, timedelta


FILM_ID = "7268s2r"
CINEMA_ID = "1052"

DAYS_TO_CHECK = 45

OUTPUT_FILE = "docs/index.html"


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

    return {
        "accept": "application/json, text/plain, */*",
        "accept-language": "cs-CZ,cs;q=0.9",
        "user-agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "Chrome/150.0.0.0 Safari/537.36"
        ),
        "uuid": os.environ["CINEMA_UUID"]
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


def get_events():

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


def get_free_seats(data):

    seats = {}


    for key, status in data.get("seats", {}).items():

        if status != 0:
            continue


        try:

            _, seat, row = key.split("_")

            row = int(row)
            seat = int(seat)


            # ignorovat vozickarskou radu
            if row == 12:
                continue


            seats.setdefault(
                row,
                []
            ).append(seat)


        except Exception:
            continue


    return seats


def generate_html(events):

    now = datetime.now().strftime(
        "%d.%m.%Y %H:%M"
    )


    html = f"""
<!DOCTYPE html>
<html lang="cs">

<head>

<meta charset="UTF-8">

<title>Odyssea IMAX 70mm Flora</title>

<style>

body {{
    font-family: Arial, sans-serif;
    max-width: 1000px;
    margin: 40px auto;
    padding: 0 20px;
}}

h1 {{
    margin-bottom: 5px;
}}

.updated {{
    color: #666;
}}

.card {{
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 15px;
    margin-top: 20px;
}}

.row {{
    margin-top: 8px;
}}

</style>

</head>


<body>


<h1>🎬 Odyssea – IMAX 70mm Flora</h1>

<p class="updated">
Aktualizováno: {now}
</p>

"""


    shown_events = 0


    for event in events:

        try:

            data = get_seats(
                event["id"]
            )


            seats = get_free_seats(
                data
            )


            # pokud nejsou žádná volná místa,
            # tento termín vůbec nezobrazovat
            if not seats:
                continue


            shown_events += 1


            html += f"""
<div class="card">

<h2>
{format_datetime(event["date"])}
</h2>

<h3>Volná místa:</h3>
"""


            for row in sorted(seats):

                numbers = ", ".join(
                    map(
                        str,
                        sorted(seats[row])
                    )
                )


                html += f"""
<div class="row">
<b>Řada {row}:</b> {numbers}
</div>
"""


            html += """
</div>
"""


        except Exception as error:

            print(
                f"Seat error {event['id']}: {error}"
            )


    if shown_events == 0:

        html += """
<div class="card">
Žádné dostupné volné místo.
</div>
"""


    html += """

</body>

</html>

"""


    return html


def main():

    print(
        "Generating IMAX dashboard"
    )


    events = get_events()


    print(
        "Events found:",
        len(events)
    )


    html = generate_html(
        events
    )


    os.makedirs(
        "docs",
        exist_ok=True
    )


    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(
            html
        )


    print(
        "Dashboard generated"
    )


if __name__ == "__main__":
    main()
