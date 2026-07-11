import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from archive_database import (
    is_archived,
    save_archive
)


HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def get_blog_links(url):

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=10
    )

    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "lxml"
    )

    links = []

    for a in soup.select("a[href]"):

        href = a.get("href")

        if "/detail/" not in href:
            continue

        full = urljoin(url, href)

        if full not in links:
            links.append(full)

    return links


def get_oldest_not_archived(url):

    links = get_blog_links(url)

    # 古い順
    links.reverse()

    for link in links:

        if not is_archived(link):
            return link

    return None
