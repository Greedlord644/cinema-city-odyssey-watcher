import requests
import json


EVENT_ID = "212817"

URLS = [
    f"https://tickets.cinemacity.cz/api/order/{EVENT_ID}?lang=cs",
    f"https://tickets.cinemacity.cz/api/order/{EVENT_ID}",
]


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/120 Safari/537.36"
    ),
    "Accept": "application/json,text/plain,*/*",
}


def test_url(url):

    print("\n==============================")
    print("TEST:")
    print(url)
    print("==============================")

    try:

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=20,
            allow_redirects=True
        )

        print("STATUS:", response.status_code)
        print("FINAL URL:", response.url)
        print("CONTENT TYPE:", response.headers.get("content-type"))

        print("\nFIRST 500 CHARACTERS:")
        print(response.text[:500])


        try:

            data = response.json()

            print("\nJSON FOUND")

            with open(
                "seat_response.json",
                "w",
                encoding="utf-8"
            ) as file:

                json.dump(
                    data,
                    file,
                    indent=2,
                    ensure_ascii=False
                )

            print(
                "Saved as seat_response.json"
            )


        except Exception:

            print(
                "Response is not JSON"
            )


    except Exception as error:

        print(
            "ERROR:",
            error
        )


def main():

    print(
        "Cinema City seat investigation"
    )

    for url in URLS:

        test_url(url)


if __name__ == "__main__":
    main()
