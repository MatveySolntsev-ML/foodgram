import base64
import json
import uuid

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from recipes.models import Ingredient, Recipe, RecipeIngredient
from users.models import User

PLACEHOLDER_IMAGE = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABAgMAAABieywaAAAACVBMVEUAAAD///9fX1/S0ecC"
    "AAAACXBIWXMAAA7EAAAOxAGVKw4bAAAACklEQVQImWNoAAAAggCByxOyYQAAAABJRU5Erk"
    "Jggg=="
)


class Command(BaseCommand):
    help = "Create a handful of demo recipes for a running instance"

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            default=str(
                settings.BASE_DIR.parent / "data" / "demo_recipes.json"
            ),
        )
        parser.add_argument("--author-email", default="demo_chef@example.com")

    def handle(self, *args, **options):
        author, _ = User.objects.get_or_create(
            email=options["author_email"],
            defaults={
                "username": "demo_chef",
                "first_name": "Демо",
                "last_name": "Шеф",
            },
        )
        if author.has_usable_password():
            author.set_unusable_password()
            author.save()

        with open(options["path"], encoding="utf-8") as f:
            items = json.load(f)

        created = 0
        for item in items:
            exists = Recipe.objects.filter(
                author=author, name=item["name"],
            ).exists()
            if exists:
                continue
            image = ContentFile(
                base64.b64decode(PLACEHOLDER_IMAGE),
                name=f"{uuid.uuid4()}.png",
            )
            recipe = Recipe.objects.create(
                author=author,
                name=item["name"],
                text=item["text"],
                cooking_time=item["cooking_time"],
                image=image,
            )
            RecipeIngredient.objects.bulk_create(
                RecipeIngredient(
                    recipe=recipe,
                    ingredient=Ingredient.objects.get(name=ing["name"]),
                    amount=ing["amount"],
                )
                for ing in item["ingredients"]
            )
            created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Processed {len(items)} recipes, created {created} new "
                f"(author: {author.email})",
            )
        )
