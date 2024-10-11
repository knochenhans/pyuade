import requests
from bs4 import BeautifulSoup

url = "https://modsamplemaster.thegang.nu/module.php?sha1=3b3b18b46f2d09d0572e4aa19faafbc3e4522"

response = requests.get(url)
if response.status_code == 200:
    website = requests.get(url)
    results = BeautifulSoup(website.content, 'html5lib')

    page = results.find('div', class_='page')
    if page:
        name = page.find('h1')

        if name:
            print(name.text)
