"""Populate the board with a realistic set of cards for demos and screenshots."""

from __future__ import annotations

from django.core.management.base import BaseCommand

from boards.services import CardService

SEED_CARDS = [
    (
        "Design the board layout",
        "Three fixed lanes, drag to move between them.",
        "todo",
    ),
    (
        "Add pagination to the card list",
        "Cursor-based; the scan used to truncate at 1 MB.",
        "todo",
    ),
    (
        "Write the Playwright screenshot script",
        "1440x900, seeded data, no empty states.",
        "todo",
    ),
    (
        "Audit the GraphQL error paths",
        "Unknown ids should return errors, not 500s.",
        "todo",
    ),
    (
        "Extract the service layer",
        "Validation out of the resolvers and into CardService.",
        "in-progress",
    ),
    (
        "Make the DynamoDB client lazy",
        "No network calls at import time, so tests can mock it.",
        "in-progress",
    ),
    (
        "Replace the entrypoint script",
        "Idempotent management command instead of a module-level create_table.",
        "in-progress",
    ),
    (
        "Remove the committed virtualenv",
        "162 MB of site-packages tracked in git.",
        "done",
    ),
    (
        "Move the Django secret key to the environment",
        "Was hardcoded in settings.py.",
        "done",
    ),
    (
        "Drop the unused Tailwind import",
        "Shipped raw @tailwind directives in the CSS bundle.",
        "done",
    ),
]


class Command(BaseCommand):
    help = "Insert a set of demo cards. Existing cards are left alone."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete every existing card before seeding.",
        )

    def handle(self, *args, **options):
        service = CardService()

        if options["reset"]:
            removed = 0
            for card in list(service.repository.iter_all()):
                service.delete_card(card["id"])
                removed += 1
            self.stdout.write(f"Removed {removed} existing card(s).")

        for title, description, status in SEED_CARDS:
            service.create_card(title=title, description=description, status=status)

        self.stdout.write(self.style.SUCCESS(f"Seeded {len(SEED_CARDS)} cards onto the board."))
