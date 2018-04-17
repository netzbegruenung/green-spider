from google.cloud import storage
import hashlib
import json
import subprocess
import os
import sys

json_file = 'webapp/dist/data/spider_result.json'

bucket_name = "green-spider-screenshots.sendung.de"

if len(sys.argv) == 1:
    print("Error: please provide path to Google Storage API system account JSON file as argument")
    sys.exit(1)

key_path = sys.argv[1]

client = None
bucket = None

# result dict. key: url, value: file name
urls_done = {}

def main():
    global client
    global bucket

    client = storage.Client.from_service_account_json(key_path)
    bucket = client.get_bucket(bucket_name)

    with open(json_file, 'r', encoding="utf8") as jsonfile:
        data = json.load(jsonfile)
    for entry in data:
        urls = entry.get('canonical_urls')
        if urls is None or len(urls) == 0:
            continue
        url = urls[0]

        if url in urls_done:
            continue

        filename = make_screenshots(url)

        urls_done[url] = filename

    output_filename = "./webapp/dist/data/screenshots.json"
    with open(output_filename, 'w', encoding="utf8") as jsonfile:
        json.dump(urls_done, jsonfile, indent=2, sort_keys=True, ensure_ascii=False)

def make_screenshots(url):
    """
    Creates screenshots in various sizes, uploads them to
    Google Cloud Storage and returns the output filename
    """
    sizes = ([320, 640], [1500, 1500])
    for size in sizes:
        print("Screenshotting size %s for %s" % (size, url))
        sizeargument = "%spx*%spx" % (size[0], size[1])
        subfolder = "%sx%s" % (size[0], size[1])
        filename = hashlib.md5(bytearray(url, 'utf-8')).hexdigest() + ".png"
        command = [
            "docker", "run", "--rm", "-v",
            os.getenv("PWD") + "/temp/%s:/srv" % subfolder,
            "netzbegruenung/green-spider-screenshotter:latest",
            url, filename, sizeargument
        ]
        subprocess.run(command)
        blob = bucket.blob('%s/%s' % (subfolder, filename))
        with open('./temp/%s/%s' % (subfolder, filename), 'rb') as my_file:
            blob.upload_from_file(my_file, content_type="image/png")
        blob.make_public()
    return filename

if __name__ == "__main__":
    main()
