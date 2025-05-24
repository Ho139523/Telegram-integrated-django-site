import requests

def get_country_choices(lang="en"):
    try:
        url = f"https://secure.geonames.org/countryInfoJSON?lang={lang}&username=Hussein2079"
        response = requests.get(url)
        data = response.json()
        countries = data.get("geonames", [])
        return [(c["countryCode"], c["countryName"]) for c in countries if c["countryCode"] != "IL"]
    except Exception as e:
        print("Error fetching country list:", e)
        return []
