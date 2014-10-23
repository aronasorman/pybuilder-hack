import StringIO
import pathlib
import requests
import zipfile

def download_and_extract_zip(branch):
    url = "https://github.com/learningequality/ka-lite/archive/{}.zip".format(branch)

    response = requests.get(url)
    response.raise_for_status()

    f = StringIO.StringIO(response.content)
    zip = zipfile.ZipFile(f)
