from .utils import get_page_data
import requests
from bs4 import BeautifulSoup
from chompjs import parse_js_object
import json
import time

avg_time = 0
number_of_times = 0

all_users_data = []
not_found_errors = []
def get_user_data(user_id:int, cookies=None):
    data, request = get_page_data(f"https://construct.hackclub.com/dashboard/users/{user_id}", cookies=cookies)
    if not request.ok:
        raise FileNotFoundError("request not okay!")
    data = data[2]['data']
    return data

def get_user_data_from_slack_id(slack_id):
    ...

def main(starting_index = 1):
    global avg_time, number_of_times
    i = starting_index
    while True:
        print('retrieving data...')
        try:
            start_time = time.time()
            data = get_user_data(i)
            end_time = time.time()
            avg_time = (avg_time * number_of_times + end_time - start_time) / (number_of_times + 1)
            number_of_times += 1
            print(f'data retrieved! current index: {i} // avg time: {avg_time} ({number_of_times} records)')
            onlyUser = data['requestedUser']
            all_users_data.append(onlyUser)
            with open('all_users_data.json', 'w') as f:
                json.dump(all_users_data, f)
        except FileNotFoundError:
            print(f"request was not okay! (user id: {i})")
            not_found_errors.append(i)
            with open('not_found_errors.json', 'w') as f:
                json.dump(not_found_errors, f)
        i += 1


if __name__ == "__main__":
    try:
        with open('all_users_data.json') as f:
            all_users_data = json.load(f)
    except Exception:
        all_users_data = []
    try:
        with open('not_found_errors.json') as f:
            not_found_errors = json.load(f)
    except Exception:
        not_found_errors = []
    
    if all_users_data:
        main(all_users_data[-1]['id']+1)
    else:
        main()