import requests


PRESENTATION_ID = "220780"

VENUE_TYPE_ID = "1"


SEATS_URL = (
    "https://tickets.cinemacity.cz/api/seats/"
    "seats-statusV2"
)


def get_seats():

    params = {
        "presentationId": PRESENTATION_ID,
        "venueTypeId": VENUE_TYPE_ID,
        "isReserved": "1"
    }

    response = requests.get(
        SEATS_URL,
        params=params,
        timeout=15
    )

    response.raise_for_status()

    return response.json()["seats"]



def parse_seats(data):

    free = []

    for seat_id, status in data.items():

        if status == 0:

            parts = seat_id.split("_")

            seat_number = int(parts[1])
            row = int(parts[2])

            free.append(
                {
                    "row": row,
                    "seat": seat_number
                }
            )

    return free



def is_allowed(row, seat):

    # ignorujeme první řady
    if row <= 5:
        return False

    # ignorujeme poslední řadu
    if row == 12:
        return False

    # zatím jednoduchý filtr krajů
    if seat <= 10:
        return False

    if seat >= 31:
        return False

    return True



def find_pairs(seats):

    result = []

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

        for i in range(
            len(numbers) - 1
        ):

            if numbers[i + 1] == numbers[i] + 1:

                result.append(
                    {
                        "row": row,
                        "seats": [
                            numbers[i],
                            numbers[i + 1]
                        ]
                    }
                )


    return result



def main():

    print(
        "Cinema City seat checker test"
    )

    print(
        f"Presentation: {PRESENTATION_ID}"
    )


    data = get_seats()


    free = parse_seats(
        data
    )


    print(
        f"Free seats: {len(free)}"
    )


    pairs = find_pairs(
        free
    )


    if pairs:

        print(
            "\nFOUND SUITABLE PAIRS:"
        )

        for pair in pairs:

            print(
                f"Row {pair['row']} "
                f"Seats {pair['seats'][0]} "
                f"+ {pair['seats'][1]}"
            )

    else:

        print(
            "No suitable pairs found"
        )



if __name__ == "__main__":
    main()
