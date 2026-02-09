import requests
import regex
import bs4
from .utils import get_cookies

def get_projects(cookies = None):
    if not cookies:
        cookies = get_cookies()
    r = requests.get('https://construct.hackclub.com/dashboard/projects', headers={"Cookie": cookies})
    soup = bs4.BeautifulSoup(r.text, features="html.parser")
    projects = []
    for link in soup.find_all('a'):
        aria_label = link.attrs.get('aria-label', None)
        if not aria_label == 'project':
            continue
        name = link.parent.find('h1').find('span')
        parent = link.parent
        time_div = parent.find_all('div')[-1].find_all('p')[0]
        match = regex.findall(r"(\d+)\s*h\s*(\d+)\s*min", time_div.text)
        if not match:
            continue
        match = match[0]
        minutes = (int(match[0]) * 60) + int(match[1])
        projects.append({
            'name': name.text,
            'minutes': minutes
        })
    return projects

if __name__ == "__main__":
    print(get_projects())