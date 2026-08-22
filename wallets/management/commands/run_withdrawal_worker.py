# wallets/management/commands/run_withdrawal_worker.py

from time import sleep

from django.core.management.base import BaseCommand

from wallets.models import Withdrawal

from wallets.tasks.process_withdrawal import (
    process_withdrawal,
)


class Command(BaseCommand):

    help = "Run Withdrawal Worker"

    def add_arguments(
        self,
        parser,
    ):

        parser.add_argument(
            "--interval",
            type=float,
            default=2,
            help="Polling interval in seconds",
        )

        parser.add_argument(
            "--batch-size",
            type=int,
            default=50,
        )

    def handle(
        self,
        *args,
        **options,
    ):

        interval = options["interval"]
        batch_size = options["batch_size"]

        self.stdout.write(
            self.style.SUCCESS(
                "Withdrawal Worker started..."
            )
        )

        while True:

            withdrawals = list(
                Withdrawal.objects
                .filter(
                    status=Withdrawal.Status.PENDING,
                )
                .order_by("created_at")
                .values_list(
                    "id",
                    flat=True,
                )[:batch_size]
            )

            for withdrawal_id in withdrawals:

                try:

                    process_withdrawal(
                        withdrawal_id
                    )

                except Exception:

                    self.stderr.write(
                        self.style.ERROR(
                            "Unexpected error while "
                            f"processing withdrawal "
                            f"{withdrawal_id}"
                        )
                    )

            sleep(interval)
