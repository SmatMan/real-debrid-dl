import requests
import hashlib
import time
from tqdm import tqdm
from urllib.parse import urlparse, unquote
import os

import config as cfg

def get_filename_from_url(url):
    parsed_url = urlparse(url)
    return unquote(parsed_url.path.split('/')[-1])

def encode_sha1(input_string):
    sha1 = hashlib.sha1()
    sha1.update(input_string.encode())
    return sha1.hexdigest()

def download_file(url, path):
    path = get_filename_from_url(url)
    path = os.path.join(os.path.expanduser(cfg.download_path), path)
    print(path)

    response = requests.get(url, stream=True)

    # Get the total file size
    file_size = int(response.headers.get("Content-Length", 0))

    # Create a progress bar
    progress = tqdm(response.iter_content(1024), f"Downloading...", total=file_size, unit="B", unit_scale=True, unit_divisor=1024)

    with open(path, "wb") as f:
        for data in progress.iterable:
            # Write data read to the file
            f.write(data)
            # Update the progress bar manually
            progress.update(len(data))

class RD():
    def __init__(self):
        self.base = "https://api.real-debrid.com/rest/1.0/"
        self.headers = {'Authorization': "Bearer " + str(cfg.token)}

    def add_magnet(self, magnet):
        url = self.base + "torrents/addMagnet"
        data = {'magnet': magnet}
        r = requests.post(url, headers=self.headers, data=data)
        if r.status_code == 201:
            print(r.json()["uri"])
            return r.json()["id"]
        else:
            print(r.status_code)
            print(r.json())
            return False
            
    def get_info(self, id):
        url = self.base + "torrents/info/" + str(id)
        # print(url)
        r = requests.get(url, headers=self.headers)
        r = r.json()
        # print(r)
        info = {
            "id": r["id"],
            "hash": r["hash"],
            "filename": r["filename"],
            "status": True if r["status"] == "downloaded" else False,
            "progress": r["progress"] if "progress" in r else 0,
            "seeders": r["seeders"] if "seeders" in r else 0,
            # "speed": r["speed"] if "speed" in r else "0",
            "links": r["links"] if "links" in r else []
        }

        # if info["speed"] == "0":
        #     info["speed"] = "0 B/s"
        # else:
        #     info["speed"] = f"{round(int(info['speed'])/1024/1024, 2)} MB/s" if int(info['speed']) > 1024*1024 else f"{round(int(info['speed'])/1024, 2)} KB/s"
        return info

    def select_all_files(self, id):
        url = self.base + "torrents/selectFiles/" + str(id)
        params = {"files": "all"}

        r = requests.post(url, headers=self.headers, data=params)
        if r.status_code == 204:
            return True
        else:
            print(r.status_code)
            print(r.json())
            return False

    def get_file_progress(self, id):
        info = self.get_info(id)
        return info["progress"]

    def unrestrict_link(self, link):
        url = self.base + "unrestrict/link"
        data = {"link": link}
        r = requests.post(url, headers=self.headers, data=data)
        if r.status_code == 200:
            return r.json()["download"]
        else:
            print(r.status_code)
            print(r.json())
            return False

    def download_magnet(self, magnet):
        id = self.add_magnet(magnet)
        time.sleep(5)
        if id:
            if self.select_all_files(id):
                print("Downloading")
                progress = self.get_file_progress(id)
                while progress < 100:
                    info = self.get_info(id)
                    print(f"Progress: {info['progress']}% - Seeders: {info['seeders']} - Filename: {info['filename']}")
                    progress = info["progress"]
                    time.sleep(2)

                link = ""
                for i in range(5):
                    print(f"Getting file link - #{i+1}")
                    info = self.get_info(id)
                    if info["links"] != []:
                        link = info["links"][0]
                        print(link)
                        link = self.unrestrict_link(link)
                        print(link)
                        break
                    time.sleep(5)


                if link == "":
                    print("Error getting link")
                    return False
                else:
                    print("Downloading file")
                    filename = info["filename"]
                    download_file(link, filename)
                    return True
                
                    
        else:
            print("Error adding magnet")


if __name__ == "__main__":
    rd = RD()

    magnet = input("Enter magnet link: ")
    rd.download_magnet(magnet)