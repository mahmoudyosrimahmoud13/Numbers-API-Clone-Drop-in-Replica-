import requests
import json
import time
import math
import os


def build_wikidata_trivia():
    print("1/3 Querying Wikidata for thousands of trivia facts... (Takes ~5 seconds)")
    query = """
    SELECT ?number ?description WHERE {
      ?item wdt:P31/wdt:P279* wd:Q21199 .
      ?item wdt:P1181 ?number .
      ?item schema:description ?description .
      FILTER(LANG(?description) = "en")
      FILTER(LCASE(?description) NOT IN ("natural number", "number", "integer", "even number", "odd number", "prime number", "composite number", "positive integer"))
    }
    ORDER BY ?number
    LIMIT 10000
    """
    url = "https://query.wikidata.org/sparql"
    headers = {"User-Agent": "NumbersAPI-Mass-Builder/1.0",
               "Accept": "application/json"}

    trivia_db = {}
    try:
        # Added a 10-second timeout here to prevent freezing
        response = requests.get(
            url, params={'query': query}, headers=headers, timeout=10)
        response.raise_for_status()
        results = response.json().get("results", {}).get("bindings", [])

        for item in results:
            try:
                clean_num = int(float(item["number"]["value"]))
                desc = item["description"]["value"]
                if not desc.startswith(("a ", "an ", "the ", "in ", "of ")):
                    desc = "a " + desc if not desc.endswith("s") else desc
                trivia_db[clean_num] = f"is {desc}"
            except ValueError:
                continue
        print(f"  -> Harvested {len(trivia_db)} high-quality trivia facts.")
    except Exception as e:
        print(f"  -> Failed to fetch Wikidata: {e}")
    return trivia_db


def build_math_facts(limit=10000):
    print(f"2/3 Generating math facts algorithmically up to {limit}...")
    math_db = {}
    for i in range(1, limit + 1):
        if i > 1 and all(i % j != 0 for j in range(2, int(math.sqrt(i)) + 1)):
            math_db[i] = "is a prime number"
        elif math.isqrt(i)**2 == i:
            math_db[i] = f"is a perfect square ({math.isqrt(i)}\u00b2)"
        elif str(i) == str(i)[::-1] and i > 9:
            math_db[i] = "is a palindromic number"
        elif i % sum(int(digit) for digit in str(i)) == 0:
            math_db[i] = "is a Harshad number, meaning it is divisible by the sum of its digits"
        else:
            if i % 2 == 0:
                math_db[i] = f"is {bin(i)[2:]} in base 2 (binary)"
            elif i % 3 == 0:
                math_db[i] = f"is {oct(i)[2:]} in base 8 (octal)"
            else:
                math_db[i] = f"is {hex(i)[2:]} in base 16 (hexadecimal)"
    print(f"  -> Generated {len(math_db)} math facts.")
    return math_db


def build_date_and_year_facts():
    print("3/3 Scraping Wikipedia for 365 days of history... (Takes ~3 minutes)")
    date_db, year_db = {}, {}
    days_in_month = {1: 31, 2: 29, 3: 31, 4: 30, 5: 31,
                     6: 30, 7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31}
    headers = {"User-Agent": "NumbersAPI-Mass-Builder/1.0"}

    for month, max_days in days_in_month.items():
        for day in range(1, max_days + 1):
            url = f"https://en.wikipedia.org/api/rest_v1/feed/onthisday/events/{month}/{day}"
            try:
                # Added a 5-second timeout so it never hangs!
                res = requests.get(url, headers=headers, timeout=5)

                events = []
                if res.status_code == 200:
                    events = res.json().get("events", [])
                    if events:
                        date_db[f"{month}/{day}"] = f"is the day that {events[0]['text']}"
                        for event in events:
                            year = event.get("year")
                            if year and year not in year_db:
                                year_db[year] = f"is the year that {event['text']}"

                # Print statement so you can see exactly where it is
                print(
                    f"  -> Scraped {month}/{day}... (Found {len(events)} events)")

                time.sleep(0.5)  # Be polite to Wikipedia

            except requests.exceptions.Timeout:
                print(
                    f"  -> TIMEOUT on {month}/{day}! Skipping to keep moving...")
            except Exception as e:
                print(f"  -> Error on {month}/{day}: {e}")

    print(
        f"  -> Harvested {len(date_db)} date facts and {len(year_db)} year facts.")
    return date_db, year_db


if __name__ == "__main__":
    trivia = build_wikidata_trivia()
    math_facts = build_math_facts()
    dates, years = build_date_and_year_facts()

    master_db = {
        "trivia": trivia,
        "math": math_facts,
        "date": dates,
        "year": years
    }

    with open("numbers_db.json", "w", encoding="utf-8") as f:
        json.dump(master_db, f, indent=4)
    print("\nSUCCESS! Saved entirely to numbers_db.json.")
