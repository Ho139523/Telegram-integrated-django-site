#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
واکشی سلسله‌مراتب کشور/استان/شهر از GeoNames با نام‌های چندزبانه،
ذخیرهٔ پیش‌رونده، پارت‌بندیِ اجرا و مدیریت محدودیت ۱۰۰۰ درخواست در ساعت.
"""

import json
import os
import time
from pathlib import Path
from typing import Dict, List

import requests

# ---------- تنظیمات عمومی ----------
LANGUAGES: List[str] = ["en", "ru", "ch", "fa", "ar"]
USERNAME = "hussein2079"        # نام کاربری GeoNames
BASE_URL = "https://secure.geonames.org"
DATA_FILE = Path("countries_full_multilang.json")

# ---------- تنظیمات نرخ درخواست ----------
MAX_REQ_PER_HOUR = 950          # حاشیهٔ امن نسبت به سقف 1000
HOUR_SECONDS = 3600

req_count = 0
window_start = time.time()


# ---------- توابع کمکی ----------
def throttled_get(url: str, timeout: int = 10) -> requests.Response:
    """
    لایه‌ای روی requests.get که شمارندهٔ درخواست‌ها را نگه می‌دارد
    و در صورت نزدیک‌شدن به سقف، صبر می‌کند.
    """
    global req_count, window_start

    # ریست شمارنده اگر ساعت جدید شروع شده باشد
    elapsed = time.time() - window_start
    if elapsed >= HOUR_SECONDS:
        req_count = 0
        window_start = time.time()

    # اگر نزدیک سقفیم، صبر کن
    if req_count >= MAX_REQ_PER_HOUR:
        wait = HOUR_SECONDS - elapsed + 5
        print(f"⏸️  {MAX_REQ_PER_HOUR} درخواست زده شد. "
              f"{int(wait)} ثانیه صبر می‌کنیم تا محدودیت ریست شود …")
        time.sleep(wait)
        req_count = 0
        window_start = time.time()

    response = requests.get(url, timeout=timeout)
    req_count += 1
    return response


def fetch_json(endpoint: str, **params) -> Dict:
    """دریافت JSON از GeoNames با مدیریت نرخ درخواست."""
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
def build_data():
    master = load_data()
    countries = fetch_countries()
    total = len(countries)

    # فقط اولین کشور ناتمام را در هر اجرا پردازش کن
    for idx, country in enumerate(countries, start=1):
        ccode = country["countryCode"]
        c_geoname = country["geonameId"]

        c_rec = master.get(ccode)

        # مطمئن شو کلید done برای کشور وجود دارد
        if c_rec and "done" not in c_rec:
            c_rec["done"] = False

        # اگر کشور کامل است، برو بعدی
        if c_rec and c_rec.get("done"):
            continue

        print(f"📍 کشور {idx}/{total}: {ccode}")

        # ایجاد رکورد کشور در صورت نیاز
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
                localized = fetch_json("countryInfoJSON", lang=lang).get(
                    "geonames", []
                )
                for lc in localized:
                    if lc["countryCode"] == ccode:
                        c_rec["names"][lang] = lc["countryName"]
                time.sleep(0.3)

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

            # اطمینان از وجود کلید 'done' برای استان
            p_rec.setdefault("done", False)

            # اگر استان کامل شده، رد شو
            if p_rec["done"]:
                continue

            # نام استان در سایر زبان‌ها
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

                # نام شهرها در سایر زبان‌ها
                for lang in LANGUAGES:
                    if lang == "en":
                        continue
                    for lc in fetch_children(p_id, lang=lang):
                        if lc["geonameId"] == city_id:
                            city_rec["names"][lang] = lc["name"]

            # استان تمام شد
            p_rec["done"] = True
            save_data(master)  # ذخیره بعد از هر استان
            print(f"   ✅ استان «{p_code}» تکمیل شد. (ذخیره شد)")

        # اگر همهٔ استان‌ها done باشند، کشور done می‌شود
        if all(p.get("done") for p in c_rec["provinces"].values()):
            c_rec["done"] = True
            print(f"🎉 کشور {ccode} کامل شد.")

        save_data(master)  # ذخیرهٔ نهایی کشور
        print("💾 داده ذخیره شد.")
        break  # در هر اجرا فقط همین یک کشور پردازش می‌شود

    else:
        print("🔚 هیچ کشور ناتمامی باقی نمانده.")


if __name__ == "__main__":
    print("🔄 در حال واکشی داده‌ها از GeoNames …")
    build_data()
    print("✅ پایان کار. فایل به‌روز شد:", DATA_FILE)
