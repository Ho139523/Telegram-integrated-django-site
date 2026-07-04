import pycountry

from django.core.management.base import BaseCommand

from wallets.models import Currency


class Command(BaseCommand):

    help = "Seed all world currencies into database."

    def handle(self, *args, **options):

        created = 0
        updated = 0

        for currency in pycountry.currencies:

            code = currency.alpha_3
            name = currency.name

            # Iranian Toman support
            if code == "IRR":
                code = "IRT"
                name = "Iranian Toman"

            obj, is_created = Currency.objects.update_or_create(
                code=code,
                defaults={
                    "name": name,
                    "symbol": code,
                    "decimals": 2,
                    "is_active": True,
                    "is_crypto": False,
                },
            )

            if is_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Created: {created}, Updated: {updated}"
            )
        )
