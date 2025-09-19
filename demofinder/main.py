import requests
import re
import json
import progressbar
from urllib.parse import urlparse
from urllib.request import urlretrieve


pbar = None
limit = 10 # Page Delimiter


def extract_steamid(url: str) -> int:
    return int(url.split("/")[-1])


def verify_url(url: str, mode: str) -> bool:
    '''Mode is either logs or demos'''
    if mode == "logs":
        return verify_logstf_url(url)
    elif mode == "demos":
        return verify_demostf_url(url)
    else:
        return False
    

def verify_logstf_url(url):
    url_dict = urlparse(url)
    netloc = "logs.tf"
    pattern = "/profile/7656[0-9]{13}/?$"
    if url_dict.netloc != netloc: return False
    if not re.match(pattern, url_dict.path): return False
    return True


def verify_demostf_url(url):
    url_dict = urlparse(url)
    netloc = "demos.tf"
    pattern = "/profiles/7656[0-9]{13}/?$"
    if url_dict.netloc != netloc: return False
    if not re.match(pattern, url_dict.path): return False
    return True


def verify_search(string, limit):
    # Format: 1 2 3 
    # No repeating
    lst = string.split(" ")
    if len(set(lst)) != len(lst): return False # Repeating
    if [s for s in lst if s.isdigit() and int(s) <= limit and int(s) > 0] != lst: return False
    return True


def show_progress(block_num, block_size, total_size):
    global pbar
    if pbar is None:
        pbar = progressbar.ProgressBar(maxval=total_size)
        pbar.start()

    downloaded = block_num * block_size
    if downloaded < total_size:
        pbar.update(downloaded)
    else:
        pbar.finish()
        pbar = None


def get_user_log_profile():
    logs_tf_url = input("Enter your Logs.tf profile: ")
    while not verify_url(logs_tf_url, "logs"):
        logs_tf_url = input("Enter your Logs.tf profile: ")
    return logs_tf_url


def menu():
    print("DEMOFINDER")
    print("1) Get Demo from logs.tf URL")
    print("2) Get Demos from logs.tf profile")


def download_demo_files(demos: list) -> int:
    download_demos = []
    for i in demos:
        demo_url = i['url']
        filename = demo_url.split("/")[-1]
        print(f"URL: {demo_url}")
        download_demos += [[demo_url, filename]]

    answer = input("Download these demos? (Y/N) : ")

    while answer.lower() not in ("y", "n"):
        answer = input("Download these demos? (Y/N) : ")
    if answer.lower() != "y":
        print("Exiting...")
        return 0
    for i in download_demos:
        print(f"Downloading {i[1]}...")
        urlretrieve(i[0], i[1], show_progress)
    return 1


def find_demos_from_logs(logs: dict, search: str, steamid64: int) -> list:
    selected_logs = [logs['logs'][int(j)-1] for j in search.split(" ")]
    demos = []
    for log in selected_logs:
        demos_api = rf"https://api.demos.tf/profiles/{steamid64}?after={log['date']-10000}&before={log['date']+10000}&map={log['map']}"
        demos_response = requests.get(demos_api)
        demos += demos_response.json()
    return demos


def find_demo_from_log(log: dict) -> list:
    demos = []
    players = [key for key in log["players"]]
    steamid64 = steamid_to_64bit(players[0])
    demos_api = rf"https://api.demos.tf/profiles/{steamid64}?after={log['info']['date']-5000}&before={log['info']['date']+5000}&map={log['info']['map']}"
    demos_response = requests.get(demos_api)
    demos += demos_response.json()
    return demos


def display_search_results(logs: dict, steamid64: int) -> None:
    print(f"Last {limit} logs for {steamid64}:")
    for i in range(limit):
        item = logs['logs'][i]
        print(rf"{i+1}: logs.tf/{item['id']}, {item['title']}, {item['map']}")


def dump_logs(logs: dict) -> None:
    file = open("search.json", "w")
    json.dump(logs, file)


def steamid_to_64bit(steamid: str) -> int:
    steamid = steamid.strip('[').strip(']')

    id_split = steamid.split(":")
    steamid64 = (1 << 56) + (1 << 52) + (1 << 32) + int(id_split[2])
    return steamid64


def main() -> None:
    menu()
    user_choice = input()
    while user_choice not in ["1", "2"]:
        print("Invalid Option Chosen.")
        user_choice = input()

    if user_choice == "1":
        logs_tf_url = input("Enter your logs.tf URL: ")
        logs_api = rf"http://logs.tf/api/v1/log/{logs_tf_url}"

        logs_response = requests.get(logs_api)
        log = logs_response.json()
        
        dump_logs(log)

        demos = find_demo_from_log(log)
    
    elif user_choice == "2":
        logs_tf_profile_url = get_user_log_profile()

        steamid64 = extract_steamid(logs_tf_profile_url)
        logs_api = rf"https://logs.tf/api/v1/log?player={steamid64}&limit={limit}"

        logs_response = requests.get(logs_api)
        logs = logs_response.json()
        dump_logs(logs)

        display_search_results(logs, steamid64)

        search = input("Select logs to search for demos, separated by spaces: ")
        while not verify_search(search, limit):
            search = input("Select logs to search for demos, separated by spaces: ")
        
        demos = find_demos_from_logs(logs, search, steamid64)
        
    if not demos:
        print("There is no demos.tf record for these logs.")
    else:
        download_demo_files(demos)
        
    
    
if __name__ == "__main__":
    main()