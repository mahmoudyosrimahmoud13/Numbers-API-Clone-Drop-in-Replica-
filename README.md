# Numbers API Clone (Drop-in Replica) 🔢

A modern, high-performance, and asynchronous implementation of the [Numbers API](http://numbersapi.com). This project serves interesting trivia, mathematical properties, and historical data about numbers and dates.

## 💡 Why this exists?

Let's be honest: the original Numbers API is a classic, but it is **frequently down or unreachable**. I built this replica for **fun** and to ensure that developers have a **reliable, always-on alternative** that doesn't break their applications when the original service hiccups. 

This version carries its own "brain"—a massive local database built from `wiki.py`—so it provides millisecond response times and works perfectly even when external APIs are slow or offline.

## ✨ Key Features

* **FastAPI Powered**: Built with modern Python for high-concurrency and asynchronous speed.
* **Independent Data Harvester**: Includes `wiki.py`, a powerful engine that scrapes Wikipedia and Wikidata to build a local knowledge base.
* **Zero-Latency Responses**: Once the database is built, facts are served from RAM/JSON, eliminating external API lag.
* **Full Drop-in Compatibility**: Supports the exact same URL structures as the original API.
* **Smart Fallback**: If a specific fact is missing from the local database, the system dynamically fetches a unique fact from an external API to keep the data flowing.

## 🛠 Tech Stack

* **FastAPI**: The high-performance web framework.
* **Httpx**: For asynchronous networking.
* **Requests**: Used in the builder script for robust data harvesting.
* **Wikidata & Wikipedia REST API**: The primary sources for the historical and trivia database.

## 📂 Category Breakdown

1.  **Trivia**: Detailed facts about numbers harvested from Wikidata entries.
2.  **Math**: Algorithmic generation of properties like Primes, Perfect Squares, Harshad numbers, and Binary/Hex conversions.
3.  **Date**: Historical events for every day of the year (e.g., "10/24 is the day that...").
4.  **Year**: Significant events tied to specific years throughout history.

## 🚀 Getting Started

### 1. Installation
Clone the repository and install the required dependencies:

    git clone https://github.com/mahmoudyosrimahmoud13/Numbers-API-Clone-Drop-in-Replica-.git
    cd Numbers-API-Clone-Drop-in-Replica-
    pip install fastapi httpx requests uvicorn

### 2. Populate the "Brain"
The server needs the `numbers_db.json` file to function at peak performance. Build it by running the harvester:

    python wiki.py

> **Note**: This script queries thousands of events. It takes a few minutes to complete to remain polite to Wikipedia's API limits.

### 3. Run the API
Start the local server:

    python main.py

The API will be live at `http://localhost:8000`.

## 📖 API Reference

### Single Facts
* **GET /42**: Get a trivia fact about 42.
* **GET /42/math**: Get a mathematical property of 42.
* **GET /10/24/date**: Get a historical event for October 24th.

### Random & Range Requests
* **GET /random/trivia?min=10&max=100**: A random fact within a specific range.
* **GET /1..3,10?json**: Returns facts for 1, 2, 3, and 10 in a single JSON object (Batch mode).

### Response Modifiers
* **?json**: Returns the response in structured JSON.
* **?fragment**: Returns only the fact string without the leading number.

## 📜 License
This project is licensed under the MIT License - created for the love of numbers and the necessity of 100% uptime.
