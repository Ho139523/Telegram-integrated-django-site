#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
واکشی سلسله‌مراتب کشور/استان/شهر از GeoNames با نام‌های چندزبانه
برای یک کشور خاص (با کد کوتاه مانند US, IR و ...)،
و تکمیل فایل countries_full_multilang.json.
"""

import json
import time
from pathlib import Path
from typing import Dict, List
import sys
import requests

# ---------- تنظیمات عمومی ----------
LANGUAGES: List[str] = ["en", "ru", "ch", "fa", "ar"]
USERNAME = "hussein2079"  # نام کاربری GeoNames
BASE_URL = "https://secure.geonames.org"
DATA_FILE = Path("countries_full_multilang.json")

# ---------- تنظیمات نرخ درخواست ----------
MAX_REQ_PER_HOUR = 950  # حاشیه امن نسبت به سقف 1000
HOUR_SECONDS = 3600

req_count = 0
window_start = time.time()


# ---------- توابع کمکی ----------
def throttled_get(url: str, timeout: int = 10) -> requests.Response:
    """ارسال درخواست HTTP با محدودیت نرخ."""
    global req_count, window_start

    elapsed = time.time() - window_start
    if elapsed >= HOUR_SECONDS:
        req_count = 0
        window_start = time.time()

    if req_count >= MAX_REQ_PER_HOUR:
        wait = HOUR_SECONDS - elapsed + 5
        print(f"⏸️  {MAX_REQ_PER_HOUR} درخواست زده شد. {int(wait)} ثانیه صبر می‌کنیم …")
        time.sleep(wait)
        req_count = 0
        window_start = time.time()

    response = requests.get(url, timeout=timeout)
    req_count += 1
    return response


def fetch_json(endpoint: str, **params) -> Dict:
    qs = "&".join(f"{k}={v}" for k, v in params.items())
    url = f"{BASE_URL}/{endpoint}?{qs}&username={USERNAME}"
    return throttled_get(url).json()


def fetch_countries() -> List[Dict]:
    return fetch_json("countryInfoJSON", lang="en").get("geonames", [])


def fetch_children(geoname_id: int, lang: str = "en") -> List[Dict]:
    try:
        return fetch_json("childrenJSON", geonameId=geoname_id, lang=lang).get(
            "geonames", []
        )
    except Exception as e:
        print(f"⚠️  خطا در دریافت بچه‌های {geoname_id} ({lang}): {e}")
        return []


def load_data() -> Dict:
    if DATA_FILE.exists():
        with DATA_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_data(data: Dict) -> None:
    with DATA_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ---------- منطق اصلی ----------
def build_data_for_country(target_code: str):
    target_code = target_code.upper()
    master = load_data()
    countries = fetch_countries()
    country = next((c for c in countries if c["countryCode"] == target_code), None)

    if not country:
        print(f"❌ کشور با کد '{target_code}' پیدا نشد.")
        return

    ccode = country["countryCode"]
    c_geoname = country["geonameId"]

    c_rec = master.get(ccode)
    if not c_rec:
        master[ccode] = {
            "geonameId": c_geoname,
            "names": {},
            "provinces": {},
            "done": False,
        }
        c_rec = master[ccode]

        # نام کشور در زبان‌های مختلف
        for lang in LANGUAGES:
            localized = fetch_json("countryInfoJSON", lang=lang).get("geonames", [])
            for lc in localized:
                if lc["countryCode"] == ccode:
                    c_rec["names"][lang] = lc["countryName"]
            time.sleep(0.3)

    print(f"📍 شروع پردازش کشور: {ccode}")

    # ---------- استان‌ها ----------
    provinces_en = fetch_children(c_geoname, lang="en")
    for prov in provinces_en:
        p_id = prov["geonameId"]
        p_code = prov["name"]

        p_rec = c_rec["provinces"].setdefault(
            p_code,
            {
                "geonameId": p_id,
                "names": {"en": prov["name"]},
                "cities": {},
            },
        )

        p_rec.setdefault("done", False)
        if p_rec["done"]:
            continue

        for lang in LANGUAGES:
            if lang == "en":
                continue
            for lp in fetch_children(c_geoname, lang=lang):
                if lp["geonameId"] == p_id:
                    p_rec["names"][lang] = lp["name"]

        # ---------- شهرها ----------
        cities_en = fetch_children(p_id, lang="en")
        for city in cities_en:
            city_id = city["geonameId"]
            city_code = city["name"]
            city_rec = p_rec["cities"].setdefault(
                city_code, {"geonameId": city_id, "names": {"en": city["name"]}}
            )

            for lang in LANGUAGES:
                if lang == "en":
                    continue
                for lc in fetch_children(p_id, lang=lang):
                    if lc["geonameId"] == city_id:
                        city_rec["names"][lang] = lc["name"]

        p_rec["done"] = True
        save_data(master)
        print(f"   ✅ استان «{p_code}» تکمیل شد. (ذخیره شد)")

    if all(p.get("done") for p in c_rec["provinces"].values()):
        c_rec["done"] = True
        print(f"🎉 کشور {ccode} کامل شد.")

    save_data(master)
    print("💾 داده ذخیره شد.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❗ لطفاً کد کشور (مثلاً US یا IR) را وارد کنید.")
        sys.exit(1)

    country_code = sys.argv[1]
    print(f"🔄 در حال واکشی داده‌های کشور {country_code} از GeoNames …")
    build_data_for_country(country_code)
    print("✅ پایان کار. فایل به‌روز شد:", DATA_FILE)

