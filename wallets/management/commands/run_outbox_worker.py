# wallets/management/commands/run_outbox_worker.py

from time import sleep

from django.core.management.base import BaseCommand

from wallets.events.outbox_worker import OutboxWorker


class Command(BaseCommand):

    help = "Run Outbox Worker"

    def add_arguments(self, parser):

        parser.add_argument(
            "--interval",
            type=float,
            default=1,
            help="Polling interval in seconds",
        )

        parser.add_argument(
            "--batch-size",
            type=int,
            default=100,
        )

    def handle(self, *args, **options):

        interval = options["interval"]
        batch_size = options["batch_size"]

        self.stdout.write(
            self.style.SUCCESS(
                "Outbox Worker started..."
            )
        )

        while True:

            OutboxWorker.process(
                batch_size=batch_size,
            )

            sleep(interval)
