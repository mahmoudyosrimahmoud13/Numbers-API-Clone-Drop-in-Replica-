from fastapi import FastAPI, HTTPException, Request, Path, Query
from fastapi.responses import PlainTextResponse, JSONResponse
from contextlib import asynccontextmanager
from typing import Optional
import random
import httpx
import asyncio
import json
import os


FACTS = {"trivia": {}, "math": {}, "year": {}, "date": {}}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Loads the massive facts database into memory when the server boots up."""
    db_path = "numbers_db.json"
    print("Loading massive numbers database...")
    if os.path.exists(db_path):
        try:
            with open(db_path, "r", encoding="utf-8") as file:
                loaded_data = json.load(file)
                for category in FACTS.keys():
                    if category in loaded_data:
                        for k, v in loaded_data[category].items():
                            if str(k).lstrip('-').isdigit():
                                FACTS[category][int(k)] = v
                            else:
                                FACTS[category][str(k)] = v
            print("Successfully loaded thousands of facts into RAM!")
        except Exception as e:
            print(f"Error loading database: {e}")
    else:
        print("WARNING: numbers_db.json not found. Run build_db.py first! Falling back to external API.")
    yield
    print("Shutting down Numbers API clone...")

app = FastAPI(title="Numbers API Clone (Drop-in Replica)", lifespan=lifespan)


@app.middleware("http")
async def skip_phishing_page_middleware(request: Request, call_next):
    response = await call_next(request)

    response.headers["X-Tunnel-Skip-Anti-Phishing-Page"] = "true"
    return response


def wants_json(request: Request) -> bool:
    if "json" in request.query_params:
        return True
    return "application/json" in request.headers.get("accept", "")


def wants_fragment(request: Request) -> bool:
    return "fragment" in request.query_params


def format_fact_text(number_str: str, fact_fragment: str, is_fragment: bool) -> str:
    if is_fragment:
        return fact_fragment
    if fact_fragment.endswith("."):
        fact_fragment = fact_fragment[:-1]
    full_sentence = f"{number_str} {fact_fragment}."
    return full_sentence[0].upper() + full_sentence[1:]


async def fetch_external_fact(category: str) -> str:
    api_url = "https://uselessfacts.jsph.pl/api/v2/facts/random"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(api_url, timeout=3.0)
            if response.status_code == 200:
                fact_text = response.json().get("text", "is a mystery").strip()
                if fact_text[0].isupper():
                    fact_text = fact_text[0].lower() + fact_text[1:]
                return f"is associated with the fact that {fact_text}"
        except httpx.RequestError:
            pass
    return "is a boring number" if category != "date" else "is a day like any other"


@app.get("/random")
@app.get("/random/{category}")
async def get_random_fact(
    request: Request, category: str = "trivia",
    min: Optional[int] = Query(None), max: Optional[int] = Query(None)
):
    if category not in ["trivia", "math", "year", "date"]:
        category = "trivia"

    if category == "date":
        number = f"{random.randint(1, 12)}/{random.randint(1, 28)}"
    else:
        lower_bound, upper_bound = min if min is not None else 0, max if max is not None else 9999
        number = str(random.randint(lower_bound, upper_bound))

    fact_fragment = FACTS.get(category, {}).get(
        int(number) if number.isdigit() else number)
    if not fact_fragment:
        fact_fragment = await fetch_external_fact(category)

    text = format_fact_text(number, fact_fragment, wants_fragment(request))
    if wants_json(request):
        return JSONResponse(content={"text": text, "number": number, "found": True, "type": category})
    return PlainTextResponse(content=text)


@app.get("/{month}/{day}")
@app.get("/{month}/{day}/{category}")
async def get_date_fact(
    request: Request,
    month: int = Path(..., ge=1, le=12), day: int = Path(..., ge=1, le=31),
    category: str = "date", default: Optional[str] = None
):
    date_str = f"{month}/{day}"
    fact_fragment = FACTS.get("date", {}).get(date_str)
    if not fact_fragment:
        fact_fragment = default if default else await fetch_external_fact("date")

    text = format_fact_text(date_str, fact_fragment, wants_fragment(request))
    if wants_json(request):
        return JSONResponse(content={"text": text, "year": 2000, "found": True, "type": "date"})
    return PlainTextResponse(content=text)


@app.get("/{number_str}")
@app.get("/{number_str}/{category}")
async def get_number_fact(
    request: Request, number_str: str,
    category: str = "trivia", default: Optional[str] = None
):
    if category not in ["trivia", "math", "year"]:
        category = "trivia"
    is_fragment, is_json = wants_fragment(request), wants_json(request)

    if ".." in number_str or "," in number_str:
        numbers_to_fetch = set()
        for part in number_str.split(','):
            if ".." in part:
                try:
                    start, end = map(int, part.split(".."))
                    for i in range(start, min(end + 1, start + 100)):
                        numbers_to_fetch.add(i)
                except ValueError:
                    pass
            elif part.lstrip('-').isdigit():
                numbers_to_fetch.add(int(part))

        async def fetch_for_batch(num):
            frag = FACTS.get(category, {}).get(num)
            if not frag:
                frag = default if default else await fetch_external_fact(category)
            text = format_fact_text(str(num), frag, is_fragment)
            if is_json:
                return str(num), {"text": text, "number": num, "found": True, "type": category}
            return str(num), text

        results = dict(await asyncio.gather(*(fetch_for_batch(n) for n in numbers_to_fetch)))
        return JSONResponse(content=results)

    try:
        num_val = int(number_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid number")

    fact_fragment = FACTS.get(category, {}).get(num_val)
    if not fact_fragment:
        fact_fragment = default if default else await fetch_external_fact(category)

    text = format_fact_text(number_str, fact_fragment, is_fragment)
    if is_json:
        return JSONResponse(content={"text": text, "number": num_val, "found": True, "type": category})
    return PlainTextResponse(content=text)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
