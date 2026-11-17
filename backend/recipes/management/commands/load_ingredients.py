import json

from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    help = "Load ingredients from a JSON file into the database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            default=str(settings.BASE_DIR.parent / "data" / "ingredients.json"),
        )

    def handle(self, *args, **options):
        with open(options["path"], encoding="utf-8") as f:
            items = json.load(f)
        created = 0
        for item in items:
            _, was_created = Ingredient.objects.get_or_create(
                name=item["name"],
                measurement_unit=item["measurement_unit"],
            )
            created += was_created
        self.stdout.write(
            self.style.SUCCESS(
                f"Processed {len(items)} rows, created {created} new ingredients",
            )
        )
