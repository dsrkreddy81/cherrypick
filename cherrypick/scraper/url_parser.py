import re
from urllib.parse import unquote


def parse_google_maps_url(url: str) -> dict:
    if not re.match(
        r"https?://(www\.)?google\.com/maps|https?://maps\.(app\.)?goo\.gl", url
    ):
        raise ValueError(f"not a valid Google Maps URL: {url}")

    result = {"url": url, "place_name": None}

    match = re.search(r"/place/([^/@]+)", url)
    if match:
        result["place_name"] = unquote(match.group(1)).replace("+", " ")

    return result
