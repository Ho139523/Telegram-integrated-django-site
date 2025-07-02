# geonames_offline.py
import argparse
import json
import os
from typing import Dict, Any

# Import the necessary functions from your original script
from utils.Data.geonames_offline import (
    LANGUAGES,
    USERNAME,
    BASE_URL,
    DATA_FILE,
    fetch_countries,
    fetch_children,
    load_existing_data,
)

def process_single_country(country_code: str) -> Dict[str, Any]:
    """Process a single country and update the data file incrementally."""
    master_data = load_existing_data()
    countries = fetch_countries()
    
    # Find the requested country
    target_country = None
    for country in countries:
        if country["countryCode"].upper() == country_code.upper():
            target_country = country
            break
    
    if not target_country:
        print(f"❌ Country with code {country_code} not found in GeoNames data")
        return master_data
    
    country_code = target_country["countryCode"]
    country_geoname_id = target_country["geonameId"]
    
    # Check if the country already has complete data
    existing = master_data.get(country_code)
    has_valid_provinces = (
        existing and
        "provinces" in existing and
        isinstance(existing["provinces"], dict) and
        len(existing["provinces"]) > 0 and
        any("cities" in prov and len(prov["cities"]) > 0 for prov in existing["provinces"].values())
    )
    
    if has_valid_provinces:
        print(f"⏭️ Country {country_code} already has complete data in the file")
        return master_data
    
    print(f"📍 Processing country: {country_code}")
    
    # Initialize country data if not exists
    if country_code not in master_data:
        master_data[country_code] = {
            "geonameId": country_geoname_id,
            "names": {},
            "provinces": {}
        }
    
    # Country names in multiple languages
    for lang in LANGUAGES:
        time.sleep(1)  # Respect GeoNames rate limits
        url = f"{BASE_URL}/countryInfoJSON?lang={lang}&username={USERNAME}"
        try:
            res = requests.get(url)
            localized = res.json().get("geonames", [])
            for lc in localized:
                if lc["countryCode"] == country_code:
                    master_data[country_code]["names"][lang] = lc["countryName"]
        except Exception as e:
            print(f"⚠️ Error fetching country name for {country_code} in {lang}: {e}")
            continue
    
    # Provinces
    provinces_en = fetch_children(country_geoname_id, lang="en")
    for province in provinces_en:
        prov_id = province["geonameId"]
        prov_code = province["name"]
        
        # Only add if province doesn't exist or is empty
        if (prov_code not in master_data[country_code]["provinces"] or 
            not master_data[country_code]["provinces"][prov_code].get("cities")):
            
            master_data[country_code]["provinces"][prov_code] = {
                "geonameId": prov_id,
                "names": {"en": province["name"]},
                "cities": {}
            }
    
    # Provinces in other languages
    for lang in LANGUAGES:
        if lang == "en":
            continue
        
        time.sleep(1)  # Respect GeoNames rate limits
        localized_provs = fetch_children(country_geoname_id, lang=lang)
        for lp in localized_provs:
            for prov_code, prov_data in master_data[country_code]["provinces"].items():
                if prov_data["geonameId"] == lp["geonameId"]:
                    prov_data["names"][lang] = lp["name"]
    
    # Cities
    for prov_code, prov_data in master_data[country_code]["provinces"].items():
        prov_id = prov_data["geonameId"]
        
        # Only fetch cities if we don't have any for this province
        if not prov_data.get("cities"):
            cities_en = fetch_children(prov_id, lang="en")
            for city in cities_en:
                city_id = city["geonameId"]
                city_code = city["name"]
                prov_data["cities"][city_code] = {
                    "geonameId": city_id,
                    "names": {"en": city["name"]}
                }
        
        # City names in other languages
        for lang in LANGUAGES:
            if lang == "en":
                continue
            
            time.sleep(1)  # Respect GeoNames rate limits
            localized_cities = fetch_children(prov_id, lang=lang)
            for lc in localized_cities:
                for city_code, city_data in prov_data["cities"].items():
                    if city_data["geonameId"] == lc["geonameId"]:
                        city_data["names"][lang] = lc["name"]
    
    # Save the updated data
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(master_data, f, ensure_ascii=False, indent=2)
    
    return master_data

def main():
    parser = argparse.ArgumentParser(description="Incremental GeoNames data extractor")
    parser.add_argument("--country", help="Process a specific country by its country code (e.g., IR for Iran)")
    args = parser.parse_args()
    
    if not args.country:
        print("Please specify a country code using --country (e.g., --country IR for Iran)")
        return
    
    print(f"🔄 Fetching data for country: {args.country}")
    data = process_single_country(args.country)
    print(f"✅ Done. Data saved to {DATA_FILE}")

if __name__ == "__main__":
    main()