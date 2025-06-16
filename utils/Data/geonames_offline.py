import requests
import json
import time
import os

LANGUAGES = ["en", "ru", "ch", "fa", "ar"]
USERNAME = "hussein2079"
BASE_URL = "https://secure.geonames.org"
DATA_FILE = "countries_full_multilang.json"

def fetch_countries():
    url = f"{BASE_URL}/countryInfoJSON?lang=en&username={USERNAME}"
    res = requests.get(url)
    countries = res.json().get("geonames", [])
    return countries

def fetch_children(geoname_id, lang="en"):
    url = f"{BASE_URL}/childrenJSON?geonameId={geoname_id}&lang={lang}&username={USERNAME}"
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        return res.json().get("geonames", [])
    except Exception as e:
        print(f"⚠️ Error fetching children for {geoname_id} ({lang}): {e}")
        return []

def load_existing_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def build_data():
    master_data = load_existing_data()
    countries = fetch_countries()
    total = len(countries)

    for idx, country in enumerate(countries, start=1):
        country_code = country["countryCode"]
        country_geoname_id = country["geonameId"]

        existing = master_data.get(country_code)
        has_valid_provinces = (
            existing and
            "provinces" in existing and
            isinstance(existing["provinces"], dict) and
            len(existing["provinces"]) > 0 and
            any("cities" in prov and len(prov["cities"]) > 0 for prov in existing["provinces"].values())
        )

        if has_valid_provinces:
            print(f"⏭️ Skipping {idx}/{total}: {country_code} (already processed)")
            continue

        print(f"📍 Processing {idx}/{total}: {country_code}")

        master_data[country_code] = {
            "geonameId": country_geoname_id,
            "names": {},
            "provinces": {}
        }

        # Country names in multiple languages
        for lang in LANGUAGES:
            time.sleep(1)
            url = f"{BASE_URL}/countryInfoJSON?lang={lang}&username={USERNAME}"
            try:
                res = requests.get(url)
                localized = res.json().get("geonames", [])
                for lc in localized:
                    if lc["countryCode"] == country_code:
                        master_data[country_code]["names"][lang] = lc["countryName"]
            except:
                continue

        # Provinces
        provinces_en = fetch_children(country_geoname_id, lang="en")
        for province in provinces_en:
            prov_id = province["geonameId"]
            prov_code = province["name"]
            master_data[country_code]["provinces"][prov_code] = {
                "geonameId": prov_id,
                "names": {"en": province["name"]},
                "cities": {}
            }

        # Provinces in other languages
        for lang in LANGUAGES:
            if lang == "en":
                continue
            localized_provs = fetch_children(country_geoname_id, lang=lang)
            for lp in localized_provs:
                for prov_code, prov_data in master_data[country_code]["provinces"].items():
                    if prov_data["geonameId"] == lp["geonameId"]:
                        prov_data["names"][lang] = lp["name"]

        # Cities
        for prov_code, prov_data in master_data[country_code]["provinces"].items():
            prov_id = prov_data["geonameId"]
            cities_en = fetch_children(prov_id, lang="en")
            for city in cities_en:
                city_id = city["geonameId"]
                city_code = city["name"]
                prov_data["cities"][city_code] = {
                    "geonameId": city_id,
                    "names": {"en": city["name"]}
                }

            for lang in LANGUAGES:
                if lang == "en":
                    continue
                localized_cities = fetch_children(prov_id, lang=lang)
                for lc in localized_cities:
                    for city_code, city_data in prov_data["cities"].items():
                        if city_data["geonameId"] == lc["geonameId"]:
                            city_data["names"][lang] = lc["name"]

        # Save after each country
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(master_data, f, ensure_ascii=False, indent=2)

    return master_data

if __name__ == "__main__":
    print("🔄 Fetching data from GeoNames...")
    data = build_data()
    print("✅ Done. Data saved to countries_full_multilang.json")
