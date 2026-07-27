import requests
from datetime import datetime, timedelta


FILM_ID = "7268s2r"

API_BASE = (
    "https://www.cinemacity.cz/cz/data-api-service/v1/"
    "quickbook/10101/cinema-events/in-group/prague/"
    f"with-film/{FILM_ID}/at-date/"
)


def main():

    start = datetime.now()

    for i in range(45):

        date = (
            start + timedelta(days=i)
        ).strftime("%Y-%m-%d")


        url = (
            API_BASE
            + date
            + "?attr=&lang=cs_CZ"
        )


        response = requests.get(
            url,
            timeout=15
        )

        data = response.json()


        events = (
            data
            .get("body", {})
            .get("events", [])
        )


        for event in events:

            if str(event.get("cinemaId")) != "1052":
                continue


            print("\n====================")
            print("DATE:", date)

            print(
                "EVENT:"
            )

            print(
                event
            )


if __name__ == "__main__":
    main()
