import requests
import os
import time
from requests import Response
from urllib.parse import urlencode
from user_agent import generate_user_agent

sc_cookie = 'kAcSOqF21Fu85e7zjz7ZN2U4ZRhfV3WpwPAoE3Z7kBw&LswwdoUaIvS8ltyTt5jkRh4J50vUPVVHtR2YPi5kE'
user_agent = generate_user_agent()

# [0] = Daily, [1] = 4h, [2] = 1h, [3] = 1w
iValues = ['p07557323106', 'p07557323106', 'p23851798625', 'p07557323106']

def get_chart(symbol, tf, startDate, endDate):
    if tf == '1d':
        selector = 0
    if tf == '4h':
        selector = 1
    if tf == '1h':
        selector = 2
    if tf == '1w':
        selector = 3

    millisecondsEpoch = str(int(time.time()*1000))

    # [0] = Daily, [1] = 4h, [2] = 1h, [3] = 1w
    payloadObjects = [
        {"s": symbol, "p": "D", "st": startDate, "en": endDate, 'i': iValues[selector], 'r': millisecondsEpoch},
        {"s": symbol, "p": "195", "st": startDate, "en": endDate, "i": iValues[selector], 'r': millisecondsEpoch},
        {"s": symbol, "p": "60", "st": startDate, "en": endDate, "i": iValues[selector], 'r': millisecondsEpoch},
        {"s": symbol, "p": "W", "st": startDate, "en": endDate, "i": iValues[selector], 'r': millisecondsEpoch}
    ]

    encoded_payload = urlencode(
            payloadObjects[selector]
        )
    
    url = f"https://stockcharts.com/c-sc/sc?{encoded_payload}"
    response = stockCharts_request(url, user_agent)
    fileName = download_chart_image(response, url, tf)
    return fileName

def stockCharts_request(url: str, user_agent: str) -> Response:
    response = requests.get(url, headers={
        "cookie": sc_cookie, 
        "User-Agent": user_agent
    })
    return response

def download_chart_image(page_content: requests.Response, url, tf):
    """ Downloads a .png image of a chart into the "charts" folder. """
    file_name = f"{url.split('s=')[1].split('&')[0]}_{int(time.time())}-{tf}.png"

    with open(os.path.join("charts", file_name), "wb") as handle:
        handle.write(page_content.content)
    
    return file_name

#get_chart('AAPL', '1d', '2022-07-05', '2023-02-1')