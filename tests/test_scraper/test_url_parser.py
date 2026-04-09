from cherrypick.scraper.url_parser import parse_google_maps_url


def test_parse_standard_url():
    url = "https://www.google.com/maps/place/Some+Restaurant/@40.7128,-74.0060,17z/data=!3m1!4b1"
    result = parse_google_maps_url(url)
    assert result["place_name"] == "Some Restaurant"
    assert result["url"] == url


def test_parse_short_url_keeps_original():
    url = "https://maps.app.goo.gl/abc123"
    result = parse_google_maps_url(url)
    assert result["url"] == url


def test_rejects_non_google_url():
    import pytest

    with pytest.raises(ValueError, match="not a valid Google Maps URL"):
        parse_google_maps_url("https://yelp.com/biz/something")
