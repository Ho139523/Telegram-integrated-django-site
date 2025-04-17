import pycountry

countries = [
    (country.alpha_2, country.name)
    for country in pycountry.countries
    if country.alpha_2 != "IL"  # حذف اسرائیل
]

