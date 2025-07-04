import requests
from datetime import datetime
import smtplib
from email.message import EmailMessage
import os
from dotenv import load_dotenv

load_dotenv()

EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_RECEIVERS = os.getenv("EMAIL_RECEIVERS")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")
SMTP_PASSWORD =os.getenv("SMTP_PASSWORD")
YOUR_CITY = os.getenv("YOUR_CITY")
MAX_PRICE = int(os.getenv("MAX_PRICE"))

def get_flights_from_city():
    url = "https://www.ryanair.com/api/farfnd/3/oneWayFares"
    params = {
        "departureAirportIataCode": YOUR_CITY,
        "language": "pl",
        "market": "pl-pl",
        "outboundDepartureDateFrom": datetime.today().strftime('%Y-%m-%d'),
        "outboundDepartureDateTo": "2025-12-31",
        "currency": "PLN"
    }
    response = requests.get(url, params=params)
    data = response.json()

    flights = []
    for fare in data.get("fares", []):
        price = fare["outbound"]["price"]["value"]
        if price <= MAX_PRICE:
            destination = fare["outbound"]["arrivalAirport"]
            flights.append({
                "from": YOUR_CITY,
                "to": destination["iataCode"],
                "to_name": destination["name"],
                "date": fare["outbound"]["departureDate"][:10],
                "price": price
            })
    return flights

def get_flights_to_city():
    def get_airports_flying_to_city():
        url = "https://www.ryanair.com/api/views/locate/3/routes"
        response = requests.get(url)
        data = response.json()
        return list({
            route["airportTo"]
            for route in data if route["airportFrom"] == YOUR_CITY
        })

    airports = get_airports_flying_to_city()
    url = "https://www.ryanair.com/api/farfnd/3/oneWayFares"
    flights = []

    for airport in airports:
        params = {
            "departureAirportIataCode": airport,
            "arrivalAirportIataCode": YOUR_CITY,
            "language": "pl",
            "market": "pl-pl",
            "outboundDepartureDateFrom": datetime.today().strftime('%Y-%m-%d'),
            "outboundDepartureDateTo": "2025-12-31",
            "currency": "PLN"
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()


            for fare in data.get("fares", []):
                arrival = fare["outbound"]["arrivalAirport"]["iataCode"]
                price = fare["outbound"]["price"]["value"]
                if arrival == YOUR_CITY and price <= MAX_PRICE:
                    departure = fare["outbound"]["departureAirport"]
                    flights.append({
                        "from": departure["iataCode"],
                        "from_name": departure["name"],
                        "to": YOUR_CITY,
                        "date": fare["outbound"]["departureDate"][:10],
                        "price": price
                    })
        except Exception as e:
            print(f"Błąd przy lotnisku {airport}: {e}")
            continue

    return flights

def pair_round_trips(flights_from, flights_to):
    results = []

    for out in flights_from:
        for ret in flights_to:
            if out["to"] == ret["from"]:
                date_out = datetime.strptime(out["date"], "%Y-%m-%d")
                date_ret = datetime.strptime(ret["date"], "%Y-%m-%d")
                delta = (date_ret - date_out).days

                if 0 < delta <= 7:
                    results.append({
                        "city": out["to"],
                        "city_name": out["to_name"],
                        "depart": out["date"],
                        "return": ret["date"],
                        "total_price": out["price"] + ret["price"],
                        "price_go": out["price"],
                        "price_return": ret["price"]
                    })
    return sorted(results, key=lambda x: x["total_price"])

def send_email(body):
    msg = EmailMessage()
    msg["Subject"] = "✈️ Tanie loty "
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER
    msg["Bcc"] = EMAIL_RECEIVERS
    msg.set_content(body)
    print(body)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
       smtp.login(EMAIL_SENDER, SMTP_PASSWORD)
       smtp.send_message(msg)
    print("📧 Wysłano e-mail!")

def main():
    flights_from = get_flights_from_city()
    print(flights_from)

    flights_to = get_flights_to_city()
    print(flights_to)
    round_trips = pair_round_trips(flights_from, flights_to)

    if round_trips:
        lines = [
            f"{YOUR_CITY} → {r['city']} ({r['city_name']}): {r['depart']} → {r['return']}, "
            f"{r['total_price']} zł (tam: {r['price_go']} zł, powrót: {r['price_return']} zł)"
            for r in round_trips
        ]
        lines_from = [
            f"{YOUR_CITY} → ({r['to_name']}): {r['date']}, "
            f"{r['price']} zł"
            for r in flights_from
        ]
        message = f"Loty poniżej {MAX_PRICE} zł:\n\n" + "\n".join(lines_from) + f"\n\n🌀 Loty w obie strony do {MAX_PRICE} zł z przerwą ≤ 7 dni:\n\n" + "\n".join(lines)
        #print(message)
        send_email(message)
    else:
        print("😞 Brak pasujących lotów.")

if __name__ == "__main__":
    main()
