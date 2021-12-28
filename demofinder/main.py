import requests
import re
import json
import progressbar
from urllib.parse import urlparse
from urllib.request import urlretrieve


pbar = None


def extract_steamid(url):
    return int(url.split("/")[-1])


def verify_url(url, mode):
    url_dict = urlparse(url)
    if mode == 0:
        netloc = "logs.tf"
        pattern = "/profile/7656[0-9]{13}\/?$"
    elif mode == 1:
        netloc = "demos.tf"
        pattern = "/profiles/7656[0-9]{13}\/?$"
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


def main():
    limit = 10

    logs_tf_url = input("Enter your Logs.tf profile: ")
    while not verify_url(logs_tf_url, 0):
        logs_tf_url = input("Enter your Logs.tf profile: ")

    steamid64 = extract_steamid(logs_tf_url)
    logs_api = rf"https://logs.tf/api/v1/log?player={steamid64}&limit={limit}"

    logs_response = requests.get(logs_api)
    logs = logs_response.json()

    file = open("search.json", "w")
    json.dump(logs, file)

    print(f"Last {limit} logs for {steamid64}:")
    for i in range(limit):
        item = logs['logs'][i]
        print(rf"{i+1}: logs.tf/{item['id']}, {item['title']}, {item['map']}")

    search = input("Select logs to search for demos, separated by spaces: ")
    while not verify_search(search, limit):
        search = input("Select logs to search for demos, separated by spaces: ")
    
    selected_logs = [logs['logs'][int(j)-1] for j in search.split(" ")]
    demos = []
    for log in selected_logs:
        demos_api = rf"https://api.demos.tf/profiles/{steamid64}?after={log['date']-10000}&before={log['date']+10000}&map={log['map']}"
        demos_response = requests.get(demos_api)
        demos += demos_response.json()
    
    if not demos:
        print("There is no demos.tf record for these logs.")
    else:
        download_demos = []
        for i in demos:
            demo_url = i['url']
            filename = demo_url.split("/")[-1]
            print(f"URL: {demo_url}")
            download_demos += [[demo_url, filename]]

        answer = input("Download these demos? (Y/N) : ")
        while answer.lower() not in ("y", "n"):
            answer = input("Download these demos? (Y/N) : ")
        for i in download_demos:
            print(f"Downloading {i[1]}...")
            urlretrieve(i[0], i[1], show_progress)
        
    
    
if __name__ == "__main__":
    main()