from .utils import get_page_data
import requests
from bs4 import BeautifulSoup
from chompjs import parse_js_object
import json
import time
import threading
import traceback

avg_time = 0
number_of_times = 0

all_users_data = []
users_idx_in_progress = []
not_found_errors = []


def get_user_data(user_id: int, cookies=None):
    data, request = get_page_data(
        f"https://construct.hackclub.com/dashboard/users/{user_id}", cookies=cookies
    )
    if not request.ok:
        raise FileNotFoundError("request not okay!")
    data = data[2]["data"]
    return data


def get_and_store_data(i):
    global avg_time, number_of_times, users_idx_in_progress
    if i in users_idx_in_progress:
        return
    users_idx_in_progress.append(i)
    try:
        try:
            start_time = time.time()
            data = get_user_data(i)
            end_time = time.time()
            avg_time = end_time - start_time
            number_of_times += 1
            print(f"[{i}] data retrieved! time: {avg_time}s")
            dataToStore = data
            dataToStore["id"] = dataToStore["requestedUser"]["id"]
            dataToStore["slackId"] = dataToStore["requestedUser"]["slackId"]
            dataToStore = data["requestedUser"]
            all_users_data.append(dataToStore)
        except FileNotFoundError:
            print(f"[{i}] request was not okay! (user id: {i})")
            not_found_errors.append(i)
            with open("not_found_errors.json", "w") as f:
                json.dump(not_found_errors, f)
    except Exception:
        print(f"uh oh! User id: {i}")
        traceback.print_tb()


def get_user_data_from_slack_id(slack_id):
    with open("all_users_data.json") as f:
        data = json.load(f)

    for row in data:
        if not row:
            continue
        print(row)
        if row["slackId"] == slack_id:
            return get_user_data(row["id"])
    return None


def main(starting_index=1, max_threads=5):
    global avg_time, number_of_times
    i = starting_index
    current_threads: list[threading.Thread] = []
    start_time = time.time()
    while True:
        if max_threads != -1:
            while len(current_threads) > max_threads:
                # print(f"Max thread count reached! waiting for threads to become free... (avg: {(time.time() - start_time)/i})")
                threads_completed = []
                for thread in current_threads:
                    if not thread.is_alive():
                        threads_completed.append(thread)
                if len(threads_completed) > 0:
                    print(
                        f"--> {len(threads_completed)} threads freed. (avg: {(time.time() - start_time)/i})"
                    )
                for thread in threads_completed:
                    current_threads.remove(thread)
        t = threading.Thread(target=get_and_store_data, args=(i,))
        t.start()
        current_threads.append(t)
        get_and_store_data(i)
        i += 1

        if len(not_found_errors) > 300:
            break
    end_time = time.time()
    for thread in current_threads:
        thread.join()

    all_users_data.sort(key=(lambda x: x["id"]))
    with open("all_users_data.json", "w") as f:
        json.dump(all_users_data, f)

    not_found_errors.sort()
    with open("not_found_errors.json", "w") as f:
        json.dump(not_found_errors, f)

    print(f"completed in {end_time - start_time}s.")


if __name__ == "__main__":
    all_users_data = []
    not_found_errors = []

    if all_users_data:
        main(all_users_data[-1]["id"] + 1, max_threads=-1)
    else:
        main(max_threads=-1)
