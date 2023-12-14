from bs4 import BeautifulSoup
import requests
import datetime

import pandas as pd


def outAfterOneDay(checkIn):
    months31 = [1, 3, 5, 7, 8, 10]
    months30 = [4, 6, 9, 11]
    if (
        (checkIn.month in months30 and checkIn.day == 30)
        or (checkIn.month == 2 and checkIn.day == 28 and checkIn.year == 2025)
        or (checkIn.month == 2 and checkIn.day == 29 and checkIn.year == 2024)
        or (checkIn.month in months31 and checkIn.day == 31)
    ):
        checkOut = datetime.datetime(checkIn.year, checkIn.month + 1, 1)
    elif checkIn.month == 12 and checkIn.day == 31:
        checkOut = datetime.datetime(checkIn.year + 1, 1, 1)
    else:
        checkOut = datetime.datetime(checkIn.year, checkIn.month, checkIn.day + 1)
    return checkOut


def scraper(checkIn):
    hotelData = []
    checkIn = checkIn
    checkOut = outAfterOneDay(checkIn)
    url = f'https://www.booking.com/searchresults.html?ss=Madrid%2C+Spain&aid=304142&lang=en-us&sb=1&src_elem=sb&src=index&dest_id=-390625&dest_type=city&checkin={checkIn.strftime("%Y-%m-%d")}&checkout={checkOut.strftime("%Y-%m-%d")}&group_adults=1&no_rooms=1&group_children=0&sb_travel_purpose=leisure&selected_currency=EUR'
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; CrOS x86_64 8172.45.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.64 Safari/537.36",
        "Accept-Language": "en-US, en;q=0.5",
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    # Number of hotels found - to get the whole data
    # pages = soup.find('div', {'data-testid': 'pagination'}).parent.text.split(':')[1].split('properties found')[0].strip()

    while len(hotelData) < 100:
        hotels = soup.find_all(
            "div", {"data-testid": "property-card"}
        )  # property-card, hotelLink
        for hotel in hotels:
            name = hotel.find("div", {"data-testid": "title"}).text.strip()
            price = hotel.find(
                "span", {"data-testid": "price-and-discounted-price"}
            ).text.strip()
            link = hotel.find("a", {"data-testid": "title-link"}).attrs["href"]
            hotel_url = requests.get(link)
            hotel_soup = BeautifulSoup(hotel_url.text, "html.parser")
            hotel_address = hotel_soup.find(id="hotel_address")
            if hotel_address is not None:
                hotel_latlng = hotel_address.attrs["data-atlas-latlng"]
            hotel_lat, hotel_lng = hotel_latlng.split(",")
            room_type = (
                hotel.find("div", {"data-testid": "recommended-units"}).find("h4").text
            )
            hotelData.append(
                {
                    "check-in date": checkIn.strftime("%Y-%m-%d"),
                    "check-out date": checkOut.strftime("%Y-%m-%d"),
                    "year": checkIn.year,
                    "month": checkIn.month,
                    "name": name,
                    "price": price,
                    "lat": hotel_lat,
                    "lng": hotel_lng,
                    "room type": room_type,
                    "url": link,
                }
            )

        print(checkIn.strftime("%Y-%m-%d"), checkOut.strftime("%Y-%m-%d"))
        # Go the the next page
        new_url = url + f"&offset={len(hotelData)}"
        print(new_url.split("EUR")[1])
        response = requests.get(new_url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")

    return hotelData, checkOut


checkIn = datetime.datetime(2024, 10, 1)
finalData = []

try:
    while checkIn != datetime.datetime(2024, 12, 31):
        data, checkOut = scraper(checkIn)
        if data:  # Check if data is not empty
            finalData.extend(data)
            print(
                f"Data collected for {checkIn.strftime('%Y-%m-%d')}: {len(data)} items"
            )
        else:
            print(f"No data collected for {checkIn.strftime('%Y-%m-%d')}")
        checkIn = checkOut

except KeyboardInterrupt:
    print("Interrupted manually. Saving data collected so far...")

finally:
    if finalData:  # Check if finalData is not empty
        bookingData = pd.DataFrame(finalData)
        bookingData.to_csv("bookingDataServer.csv")
        print(f"Data saved to bookingDataServer.csv. Total items: {len(finalData)}")
    else:
        print("No data collected. No file saved.")
