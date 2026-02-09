from bs4 import BeautifulSoup
from chompjs import parse_js_object
import requests
from emoji import replace_emoji


def get_cookies():
    with open("construct_cookie") as f:
        cookie = f.read()

    if not cookie:
        raise Exception(
            "Cookie not found! Please enter it in ./construct_cookie and get it from the Cookie header when reaching construct.hackclub.com."
        )

    return cookie


def get_page_data(page_url, cookies=None):
    if not cookies:
        cookies = get_cookies()
    r = requests.get(page_url, headers={"Cookie": cookies})
    r.encoding = 'utf-8'
    if not r.ok:
        return None, r
    soup = BeautifulSoup(r.text, features="html.parser")
    script = soup.find("script")
    text = replace_emoji(script.text, "<emoji>")
    data = None
    for line in text.splitlines():
        if "data" not in line:
            continue
        data = line.strip().removeprefix("data:").removesuffix(",")
    data = parse_js_object(data)
    return data, r
