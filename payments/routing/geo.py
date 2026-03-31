import requests


class GeoIPService:

    @staticmethod
    def detect_country(ip):

        try:
            response = requests.get(
                f"https://ipapi.co/{ip}/json/"
            )

            return response.json().get("country_code")

        except:
            return None

