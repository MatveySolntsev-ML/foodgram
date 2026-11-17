# Foodgram Backend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Django REST backend for Foodgram (recipe-sharing service) matching `docs/openapi-schema.yml` exactly, so it works with the provided React frontend, passes the provided Postman collection, and runs fully containerized (nginx + PostgreSQL + Django/Gunicorn).

**Architecture:** Three Django apps — `users` (custom User + Subscription), `recipes` (Ingredient/Recipe/RecipeIngredient/Favorite/ShoppingCart), `api` (all serializers/viewsets/routers). Djoser handles standard auth/user endpoints; custom code only where Djoser defaults diverge from the spec (avatar, is_subscribed, recipe nesting).

**Tech Stack:** Python 3.11, Django 4.2, djangorestframework, djoser, django-filter not needed (manual filtering), Pillow (ImageField), PostgreSQL 13, Gunicorn, nginx, Docker Compose.

**Spec:** `docs/superpowers/specs/2026-11-17-foodgram-backend-design.md`

## Global Constraints

- API shape is fixed by `docs/openapi-schema.yml` — every field name, required-ness, and status code in this plan is copied from it; do not improvise field names.
- Login is by **email** (`USERNAME_FIELD = "email"`), not username, but `username` stays required+unique per `CustomUserCreate`.
- No automated test runner is graded by the course, but we still write Django `APITestCase` tests per task — they're our only fast feedback loop before the Thursday defense, and `pytest`/autotest absence doesn't change that.
- PEP 8 via the repo's existing `setup.cfg` (flake8) — run flake8 before each commit touching `backend/`.
- DB config must support both sqlite (fast local dev) and Postgres (final container), switched by `POSTGRES_DB` env var presence — copy the exact pattern already working in the sibling project `~/kursovaya_pdd/backend/pdd_service/settings.py:74-91`.
- Pagination: DRF `PageNumberPagination`, `page_size_query_param="limit"` (spec uses `?page=&limit=`).
- All models registered in Django admin (explicit course grading criterion).

---

## Task 1: Scaffold Django project

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/manage.py`
- Create: `backend/foodgram_backend/__init__.py`, `settings.py`, `urls.py`, `wsgi.py`, `asgi.py`
- Create: `backend/users/__init__.py`, `apps.py` (app created via `startapp`)
- Create: `backend/recipes/__init__.py`, `apps.py`
- Create: `backend/api/__init__.py`, `apps.py`
- Delete: `backend/.gitkeep`

**Interfaces:**
- Produces: Django project `foodgram_backend` importable; `AUTH_USER_MODEL = "users.User"` set (model itself created in Task 2, but setting goes in now since it can't change later); installed apps `users`, `recipes`, `api`, `rest_framework`, `rest_framework.authtoken`, `djoser`.

- [ ] **Step 1: Create requirements.txt**

```
Django==4.2.16
djangorestframework==3.15.2
djoser==2.2.3
Pillow==10.4.0
psycopg2-binary==2.9.9
gunicorn==22.0.0
python-dotenv==1.0.1
```

- [ ] **Step 2: Install deps and scaffold project**

Run:
```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
django-admin startproject foodgram_backend .
python manage.py startapp users
python manage.py startapp recipes
python manage.py startapp api
rm -f .gitkeep
```

- [ ] **Step 3: Write settings.py**

Base it on `~/kursovaya_pdd/backend/pdd_service/settings.py` for the DB-switch pattern. Key contents of `backend/foodgram_backend/settings.py`:

```python
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-insecure-key-change-me")
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "*").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework.authtoken",
    "djoser",
    "users",
    "recipes",
    "api",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "foodgram_backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "foodgram_backend.wsgi.application"

if os.environ.get("POSTGRES_DB"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("POSTGRES_DB", "foodgram"),
            "USER": os.environ.get("POSTGRES_USER", "foodgram"),
            "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "foodgram"),
            "HOST": os.environ.get("DB_HOST", "db"),
            "PORT": os.environ.get("DB_PORT", "5432"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_USER_MODEL = "users.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "ru-ru"
TIME_ZONE = "Europe/Moscow"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "static"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.TokenAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ),
    "DEFAULT_PAGINATION_CLASS": "api.pagination.LimitPageNumberPagination",
    "PAGE_SIZE": 6,
}
```

(`api.pagination` module is created in Task 8 — settings reference it now, harmless since Django doesn't import it until a request needs pagination, which is after Task 8.)

- [ ] **Step 4: Write urls.py**

`backend/foodgram_backend/urls.py`:
```python
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("api.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

(`api.urls` is created in Task 5 — create a placeholder now so `manage.py check` passes: `backend/api/urls.py` with `urlpatterns = []`.)

- [ ] **Step 5: Verify scaffold**

Run: `cd backend && python manage.py check`
Expected: `System check identified no issues (0 silenced).`

- [ ] **Step 6: Commit**

```bash
cd ~/интеграция/foodgram
git add backend/
git commit -m "Scaffold Django project: apps, settings, base urls"
```

---

## Task 2: users app — User and Subscription models

**Files:**
- Modify: `backend/users/models.py`
- Create: `backend/users/tests/__init__.py`, `backend/users/tests/test_models.py`
- Modify: `backend/users/admin.py`

**Interfaces:**
- Produces: `users.models.User` (fields: `email` unique, `username` unique, `first_name`, `last_name`, `avatar` nullable ImageField upload_to `"users/avatars/"`); `users.models.Subscription` (fields: `user` FK→User related_name `"subscriptions"`, `author` FK→User related_name `"subscribers"`, unique_together `(user, author)`).

- [ ] **Step 1: Write failing tests**

`backend/users/tests/test_models.py`:
```python
from django.db import IntegrityError
from django.test import TestCase

from users.models import Subscription, User


class UserModelTests(TestCase):
    def test_create_user_by_email(self):
        user = User.objects.create_user(
            username="vasya",
            email="vasya@example.com",
            password="Qwerty123",
            first_name="Вася",
            last_name="Иванов",
        )
        self.assertEqual(user.email, "vasya@example.com")
        self.assertEqual(User.USERNAME_FIELD, "email")

    def test_email_must_be_unique(self):
        User.objects.create_user(
            username="vasya", email="dup@example.com", password="x",
            first_name="V", last_name="I",
        )
        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                username="petya", email="dup@example.com", password="x",
                first_name="P", last_name="P",
            )


class SubscriptionModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="follower", email="f@example.com", password="x",
            first_name="F", last_name="F",
        )
        self.author = User.objects.create_user(
            username="author", email="a@example.com", password="x",
            first_name="A", last_name="A",
        )

    def test_subscribe(self):
        sub = Subscription.objects.create(user=self.user, author=self.author)
        self.assertEqual(sub.user, self.user)
        self.assertEqual(sub.author, self.author)

    def test_duplicate_subscription_rejected(self):
        Subscription.objects.create(user=self.user, author=self.author)
        with self.assertRaises(IntegrityError):
            Subscription.objects.create(user=self.user, author=self.author)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && python manage.py test users -v 2`
Expected: `ModuleNotFoundError` / `ImportError` for `Subscription` (model doesn't exist yet).

- [ ] **Step 3: Implement models**

`backend/users/models.py`:
```python
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField("Адрес электронной почты", unique=True, max_length=254)
    first_name = models.CharField("Имя", max_length=150)
    last_name = models.CharField("Фамилия", max_length=150)
    avatar = models.ImageField(
        "Аватар", upload_to="users/avatars/", null=True, blank=True,
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    class Meta:
        ordering = ["username"]

    def __str__(self):
        return self.username


class Subscription(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="subscriptions",
        verbose_name="Подписчик",
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="subscribers",
        verbose_name="Автор",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "author"], name="unique_subscription",
            ),
        ]
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"

    def __str__(self):
        return f"{self.user} → {self.author}"
```

- [ ] **Step 4: Make and run migrations, run tests**

Run:
```bash
cd backend
python manage.py makemigrations users
python manage.py migrate
python manage.py test users -v 2
```
Expected: 4 tests pass.

- [ ] **Step 5: Register in admin**

`backend/users/admin.py`:
```python
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from users.models import Subscription, User


@admin.register(User)
class FoodgramUserAdmin(UserAdmin):
    list_display = ("id", "username", "email", "first_name", "last_name")
    search_fields = ("username", "email")
    fieldsets = UserAdmin.fieldsets + (
        ("Аватар", {"fields": ("avatar",)}),
    )


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "author")
    search_fields = ("user__username", "author__username")
```

- [ ] **Step 6: Commit**

```bash
git add backend/users/
git commit -m "Add User and Subscription models"
```

---

## Task 3: recipes app — models

**Files:**
- Modify: `backend/recipes/models.py`
- Create: `backend/recipes/tests/__init__.py`, `backend/recipes/tests/test_models.py`
- Modify: `backend/recipes/admin.py`

**Interfaces:**
- Consumes: `users.models.User`.
- Produces: `recipes.models.Ingredient` (`name`, `measurement_unit`); `Recipe` (`author` FK→User, `name`, `image`, `text`, `cooking_time` PositiveSmallInteger with `MinValueValidator(1)`, `ingredients` M2M through `RecipeIngredient`, `pub_date` auto_now_add); `RecipeIngredient` (`recipe` FK, `ingredient` FK, `amount` PositiveSmallInteger `MinValueValidator(1)`); `Favorite` (`user`, `recipe`, unique_together); `ShoppingCart` (`user`, `recipe`, unique_together).

- [ ] **Step 1: Write failing tests**

`backend/recipes/tests/test_models.py`:
```python
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from recipes.models import Favorite, Ingredient, Recipe, RecipeIngredient, ShoppingCart
from users.models import User


class RecipeModelTests(TestCase):
    def setUp(self):
        self.author = User.objects.create_user(
            username="chef", email="chef@example.com", password="x",
            first_name="C", last_name="C",
        )
        self.ingredient = Ingredient.objects.create(
            name="соль", measurement_unit="г",
        )

    def test_create_recipe_with_ingredient(self):
        recipe = Recipe.objects.create(
            author=self.author, name="Суп", text="Варить", cooking_time=30,
        )
        RecipeIngredient.objects.create(
            recipe=recipe, ingredient=self.ingredient, amount=5,
        )
        self.assertEqual(recipe.recipe_ingredients.count(), 1)

    def test_cooking_time_must_be_positive(self):
        recipe = Recipe(
            author=self.author, name="Суп", text="Варить", cooking_time=0,
        )
        with self.assertRaises(ValidationError):
            recipe.full_clean()

    def test_favorite_unique_together(self):
        recipe = Recipe.objects.create(
            author=self.author, name="Суп", text="Варить", cooking_time=10,
        )
        Favorite.objects.create(user=self.author, recipe=recipe)
        with self.assertRaises(IntegrityError):
            Favorite.objects.create(user=self.author, recipe=recipe)

    def test_shopping_cart_unique_together(self):
        recipe = Recipe.objects.create(
            author=self.author, name="Суп", text="Варить", cooking_time=10,
        )
        ShoppingCart.objects.create(user=self.author, recipe=recipe)
        with self.assertRaises(IntegrityError):
            ShoppingCart.objects.create(user=self.author, recipe=recipe)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && python manage.py test recipes -v 2`
Expected: `ImportError` — models don't exist.

- [ ] **Step 3: Implement models**

`backend/recipes/models.py`:
```python
from django.core.validators import MinValueValidator
from django.db import models

from users.models import User


class Ingredient(models.Model):
    name = models.CharField("Название", max_length=128)
    measurement_unit = models.CharField("Единица измерения", max_length=64)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["name", "measurement_unit"], name="unique_ingredient",
            ),
        ]
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"

    def __str__(self):
        return f"{self.name}, {self.measurement_unit}"


class Recipe(models.Model):
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="recipes",
        verbose_name="Автор",
    )
    name = models.CharField("Название", max_length=256)
    image = models.ImageField("Картинка", upload_to="recipes/images/")
    text = models.TextField("Описание")
    cooking_time = models.PositiveSmallIntegerField(
        "Время приготовления (мин)", validators=[MinValueValidator(1)],
    )
    ingredients = models.ManyToManyField(
        Ingredient, through="RecipeIngredient", related_name="recipes",
    )
    pub_date = models.DateTimeField("Дата публикации", auto_now_add=True)

    class Meta:
        ordering = ["-pub_date"]
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name="recipe_ingredients",
    )
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.PositiveSmallIntegerField(
        "Количество", validators=[MinValueValidator(1)],
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["recipe", "ingredient"], name="unique_recipe_ingredient",
            ),
        ]
        verbose_name = "Ингредиент в рецепте"
        verbose_name_plural = "Ингредиенты в рецептах"

    def __str__(self):
        return f"{self.ingredient} в {self.recipe}"


class Favorite(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="favorites",
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name="favorited_by",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"], name="unique_favorite",
            ),
        ]
        verbose_name = "Избранное"
        verbose_name_plural = "Избранное"

    def __str__(self):
        return f"{self.user} ♥ {self.recipe}"


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="shopping_cart",
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name="in_carts",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"], name="unique_shopping_cart_item",
            ),
        ]
        verbose_name = "Список покупок"
        verbose_name_plural = "Списки покупок"

    def __str__(self):
        return f"{self.recipe} в корзине {self.user}"
```

- [ ] **Step 4: Make and run migrations, run tests**

Run:
```bash
cd backend
python manage.py makemigrations recipes
python manage.py migrate
python manage.py test recipes -v 2
```
Expected: 4 tests pass.

- [ ] **Step 5: Register in admin**

`backend/recipes/admin.py`:
```python
from django.contrib import admin

from recipes.models import Favorite, Ingredient, Recipe, RecipeIngredient, ShoppingCart


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    min_num = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "author", "favorites_count")
    search_fields = ("name", "author__username")
    list_filter = ("author",)
    inlines = (RecipeIngredientInline,)

    @admin.display(description="В избранном раз")
    def favorites_count(self, obj):
        return obj.favorited_by.count()


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "measurement_unit")
    search_fields = ("name",)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "recipe")


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "recipe")
```

- [ ] **Step 6: Commit**

```bash
git add backend/recipes/
git commit -m "Add recipes app models: Ingredient, Recipe, RecipeIngredient, Favorite, ShoppingCart"
```

---

## Task 4: Ingredient data loader

**Files:**
- Create: `backend/recipes/management/__init__.py`, `backend/recipes/management/commands/__init__.py`, `backend/recipes/management/commands/load_ingredients.py`
- Create: `backend/recipes/tests/test_commands.py`
- Create: `backend/recipes/tests/fixtures/ingredients_sample.json`

**Interfaces:**
- Consumes: `recipes.models.Ingredient`.
- Produces: management command `load_ingredients --path <file>` (default path `../data/ingredients.json` relative to `BASE_DIR`), idempotent (safe to re-run via `get_or_create`).

- [ ] **Step 1: Write failing test**

`backend/recipes/tests/fixtures/ingredients_sample.json`:
```json
[
    {"name": "соль", "measurement_unit": "г"},
    {"name": "сахар", "measurement_unit": "г"}
]
```

`backend/recipes/tests/test_commands.py`:
```python
from pathlib import Path

from django.core.management import call_command
from django.test import TestCase

from recipes.models import Ingredient

FIXTURE = Path(__file__).parent / "fixtures" / "ingredients_sample.json"


class LoadIngredientsTests(TestCase):
    def test_loads_ingredients_from_json(self):
        call_command("load_ingredients", path=str(FIXTURE))
        self.assertEqual(Ingredient.objects.count(), 2)
        self.assertTrue(Ingredient.objects.filter(name="соль").exists())

    def test_is_idempotent(self):
        call_command("load_ingredients", path=str(FIXTURE))
        call_command("load_ingredients", path=str(FIXTURE))
        self.assertEqual(Ingredient.objects.count(), 2)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python manage.py test recipes.tests.test_commands -v 2`
Expected: `CommandError: Unknown command: 'load_ingredients'`

- [ ] **Step 3: Implement command**

`backend/recipes/management/commands/load_ingredients.py`:
```python
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
                name=item["name"], measurement_unit=item["measurement_unit"],
            )
            created += was_created
        self.stdout.write(
            self.style.SUCCESS(
                f"Processed {len(items)} rows, created {created} new ingredients",
            )
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && python manage.py test recipes.tests.test_commands -v 2`
Expected: 2 tests pass.

- [ ] **Step 5: Smoke-load the real dataset**

Run: `cd backend && python manage.py load_ingredients`
Expected: `Processed 2186 rows, created 2186 new ingredients`

- [ ] **Step 6: Commit**

```bash
git add backend/recipes/management/ backend/recipes/tests/test_commands.py backend/recipes/tests/fixtures/
git commit -m "Add load_ingredients management command"
```

---

## Task 5: api app scaffolding — pagination, permissions, router wiring

**Files:**
- Create: `backend/api/pagination.py`
- Create: `backend/api/permissions.py`
- Modify: `backend/api/urls.py`

**Interfaces:**
- Produces: `api.pagination.LimitPageNumberPagination` (referenced in Task 1's `REST_FRAMEWORK` setting); `api.permissions.IsAuthorOrReadOnly`.
- Consumes: nothing yet — later tasks register their viewsets into the router created here.

- [ ] **Step 1: Write pagination class**

`backend/api/pagination.py`:
```python
from rest_framework.pagination import PageNumberPagination


class LimitPageNumberPagination(PageNumberPagination):
    page_size_query_param = "limit"
```

- [ ] **Step 2: Write permission class**

`backend/api/permissions.py`:
```python
from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return (
            request.method in permissions.SAFE_METHODS
            or obj.author == request.user
        )
```

- [ ] **Step 3: Write router scaffold**

`backend/api/urls.py`:
```python
from django.urls import include, path
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

urlpatterns = [
    path("auth/", include("djoser.urls.authtoken")),
    path("", include(router.urls)),
]
```

(Viewsets register into `router` in Tasks 6, 7, 8 by importing and extending this file.)

- [ ] **Step 4: Verify**

Run: `cd backend && python manage.py check`
Expected: no issues.

- [ ] **Step 5: Commit**

```bash
git add backend/api/
git commit -m "Add api pagination, permissions, and router scaffold"
```

---

## Task 6: Users API — Djoser config, custom serializers, avatar endpoint

**Files:**
- Create: `backend/api/serializers/__init__.py`, `backend/api/serializers/users.py`
- Create: `backend/api/views/__init__.py`, `backend/api/views/users.py`
- Modify: `backend/api/urls.py`
- Modify: `backend/foodgram_backend/settings.py` (add `DJOSER` config)
- Create: `backend/api/tests/__init__.py`, `backend/api/tests/test_users.py`

**Interfaces:**
- Consumes: `users.models.User`, `api.pagination.LimitPageNumberPagination`.
- Produces: `api.serializers.users.UserSerializer` (fields: `email, id, username, first_name, last_name, is_subscribed, avatar`), `CustomUserCreateSerializer`; `api.views.users.AvatarView` (APIView, PUT/DELETE at `/api/users/me/avatar/`).

- [ ] **Step 1: Write failing tests**

`backend/api/tests/test_users.py`:
```python
import base64

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import User

PIXEL = (
    "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABAgMAAABieywaAAAACVBMVEUAAAD/"
    "//9fX1/S0ecCAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAACklEQVQImWNoAAAAggCByxOyYQAAAABJRU5ErkJggg=="
)


class UserRegistrationTests(APITestCase):
    def test_register_and_login(self):
        response = self.client.post(
            "/api/users/",
            {
                "email": "vasya@example.com",
                "username": "vasya",
                "first_name": "Вася",
                "last_name": "Иванов",
                "password": "Qwerty123",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotIn("password", response.data)

        login = self.client.post(
            "/api/auth/token/login/",
            {"email": "vasya@example.com", "password": "Qwerty123"},
            format="json",
        )
        self.assertEqual(login.status_code, status.HTTP_200_OK)
        self.assertIn("auth_token", login.data)


class AvatarEndpointTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="vasya", email="vasya@example.com", password="Qwerty123",
            first_name="V", last_name="I",
        )
        self.client.force_authenticate(user=self.user)

    def test_set_avatar(self):
        response = self.client.put(
            "/api/users/me/avatar/", {"avatar": PIXEL}, format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("avatar", response.data)
        self.user.refresh_from_db()
        self.assertTrue(bool(self.user.avatar))

    def test_delete_avatar(self):
        self.client.put("/api/users/me/avatar/", {"avatar": PIXEL}, format="json")
        response = self.client.delete("/api/users/me/avatar/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.user.refresh_from_db()
        self.assertFalse(bool(self.user.avatar))
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && python manage.py test api.tests.test_users -v 2`
Expected: 404s — `/api/users/` and `/api/users/me/avatar/` don't exist yet.

- [ ] **Step 3: Write Base64ImageField (shared, used again in Task 8)**

`backend/api/fields.py`:
```python
import base64
import uuid

from django.core.files.base import ContentFile
from rest_framework import serializers


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith("data:image"):
            header, imgstr = data.split(";base64,")
            ext = header.split("/")[-1]
            data = ContentFile(
                base64.b64decode(imgstr), name=f"{uuid.uuid4()}.{ext}",
            )
        return super().to_internal_value(data)
```

- [ ] **Step 4: Write user serializers**

`backend/api/serializers/users.py`:
```python
from djoser.serializers import UserCreateSerializer, UserSerializer as DjoserUserSerializer
from rest_framework import serializers

from api.fields import Base64ImageField
from users.models import User


class CustomUserCreateSerializer(UserCreateSerializer):
    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = (
            "email", "id", "username", "first_name", "last_name", "password",
        )


class UserSerializer(DjoserUserSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta(DjoserUserSerializer.Meta):
        model = User
        fields = (
            "email", "id", "username", "first_name", "last_name",
            "is_subscribed", "avatar",
        )

    def get_is_subscribed(self, obj):
        request = self.context.get("request")
        if request is None or not request.user.is_authenticated:
            return False
        return request.user.subscriptions.filter(author=obj).exists()


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ("avatar",)
```

- [ ] **Step 5: Write avatar view**

`backend/api/views/users.py`:
```python
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.serializers.users import AvatarSerializer


class AvatarView(APIView):
    permission_classes = (IsAuthenticated,)

    def put(self, request):
        serializer = AvatarSerializer(
            request.user, data=request.data, partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request):
        request.user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)
```

- [ ] **Step 6: Wire Djoser settings and URLs**

Add to `backend/foodgram_backend/settings.py`:
```python
DJOSER = {
    "LOGIN_FIELD": "email",
    "USER_CREATE_PASSWORD_RETYPE": False,
    "SERIALIZERS": {
        "user_create": "api.serializers.users.CustomUserCreateSerializer",
        "user": "api.serializers.users.UserSerializer",
        "current_user": "api.serializers.users.UserSerializer",
    },
    "PERMISSIONS": {
        "user": ("rest_framework.permissions.AllowAny",),
        "user_list": ("rest_framework.permissions.AllowAny",),
    },
}
```

Update `backend/api/urls.py` — add before the router include:
```python
from api.views.users import AvatarView
# ...
urlpatterns = [
    path("users/me/avatar/", AvatarView.as_view(), name="user-avatar"),
    path("", include("djoser.urls")),
    path("auth/", include("djoser.urls.authtoken")),
    path("", include(router.urls)),
]
```

(`users/me/avatar/` must be listed before `djoser.urls` include so it isn't shadowed by Djoser's own `users/me/` route handling — Django matches top-to-bottom.)

- [ ] **Step 7: Run tests to verify they pass**

Run: `cd backend && python manage.py test api.tests.test_users -v 2`
Expected: 3 tests pass.

- [ ] **Step 8: Commit**

```bash
git add backend/api/ backend/foodgram_backend/settings.py
git commit -m "Add users API: Djoser config, custom serializers, avatar endpoint"
```

---

## Task 7: Subscriptions API

**Files:**
- Create: `backend/api/serializers/subscriptions.py`
- Create: `backend/api/views/subscriptions.py`
- Modify: `backend/api/urls.py`
- Create: `backend/api/tests/test_subscriptions.py`

**Interfaces:**
- Consumes: `users.models.Subscription`, `api.serializers.users.UserSerializer`, `api.pagination.LimitPageNumberPagination`.
- Produces: `GET /api/users/subscriptions/`, `POST/DELETE /api/users/{id}/subscribe/`.

- [ ] **Step 1: Write failing tests**

`backend/api/tests/test_subscriptions.py`:
```python
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import User


class SubscriptionTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="follower", email="f@example.com", password="x",
            first_name="F", last_name="F",
        )
        self.author = User.objects.create_user(
            username="author", email="a@example.com", password="x",
            first_name="A", last_name="A",
        )
        self.client.force_authenticate(user=self.user)

    def test_subscribe(self):
        response = self.client.post(f"/api/users/{self.author.id}/subscribe/")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["id"], self.author.id)
        self.assertTrue(response.data["is_subscribed"])

    def test_cannot_subscribe_twice(self):
        self.client.post(f"/api/users/{self.author.id}/subscribe/")
        response = self.client.post(f"/api/users/{self.author.id}/subscribe/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_subscribe_to_self(self):
        response = self.client.post(f"/api/users/{self.user.id}/subscribe/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unsubscribe(self):
        self.client.post(f"/api/users/{self.author.id}/subscribe/")
        response = self.client.delete(f"/api/users/{self.author.id}/subscribe/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_unsubscribe_when_not_subscribed_404(self):
        response = self.client.delete(f"/api/users/{self.author.id}/subscribe/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_subscriptions(self):
        self.client.post(f"/api/users/{self.author.id}/subscribe/")
        response = self.client.get("/api/users/subscriptions/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], self.author.id)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && python manage.py test api.tests.test_subscriptions -v 2`
Expected: 404s, routes don't exist.

- [ ] **Step 3: Write subscription serializer**

`backend/api/serializers/subscriptions.py`:
```python
from rest_framework import serializers

from api.serializers.users import UserSerializer
from recipes.models import Recipe


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")


class UserWithRecipesSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ("recipes", "recipes_count")

    def get_recipes(self, obj):
        request = self.context.get("request")
        recipes = obj.recipes.all()
        limit = request.query_params.get("recipes_limit") if request else None
        if limit is not None and limit.isdigit():
            recipes = recipes[: int(limit)]
        return RecipeMinifiedSerializer(
            recipes, many=True, context=self.context,
        ).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()
```

- [ ] **Step 4: Write subscription views**

`backend/api/views/subscriptions.py`:
```python
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.pagination import LimitPageNumberPagination
from api.serializers.subscriptions import UserWithRecipesSerializer
from users.models import Subscription, User


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_subscriptions(request):
    authors = User.objects.filter(subscribers__user=request.user)
    paginator = LimitPageNumberPagination()
    page = paginator.paginate_queryset(authors, request)
    serializer = UserWithRecipesSerializer(
        page, many=True, context={"request": request},
    )
    return paginator.get_paginated_response(serializer.data)


@api_view(["POST", "DELETE"])
@permission_classes([IsAuthenticated])
def manage_subscription(request, id):
    author = get_object_or_404(User, id=id)

    if request.method == "POST":
        if author == request.user:
            return Response(
                {"errors": "Нельзя подписаться на самого себя"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        _, created = Subscription.objects.get_or_create(
            user=request.user, author=author,
        )
        if not created:
            return Response(
                {"errors": "Вы уже подписаны на этого пользователя"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = UserWithRecipesSerializer(
            author, context={"request": request},
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    deleted, _ = Subscription.objects.filter(
        user=request.user, author=author,
    ).delete()
    if not deleted:
        return Response(
            {"errors": "Вы не были подписаны на этого пользователя"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    return Response(status=status.HTTP_204_NO_CONTENT)
```

- [ ] **Step 5: Wire URLs**

Update `backend/api/urls.py` — add before the djoser include:
```python
from api.views.subscriptions import list_subscriptions, manage_subscription
# ...
urlpatterns = [
    path("users/me/avatar/", AvatarView.as_view(), name="user-avatar"),
    path("users/subscriptions/", list_subscriptions, name="subscriptions"),
    path("users/<int:id>/subscribe/", manage_subscription, name="subscribe"),
    path("", include("djoser.urls")),
    path("auth/", include("djoser.urls.authtoken")),
    path("", include(router.urls)),
]
```

(Must precede `djoser.urls` so `users/<int:id>/subscribe/` and `users/subscriptions/` aren't shadowed by Djoser's own `users/<id>/` detail route.)

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd backend && python manage.py test api.tests.test_subscriptions -v 2`
Expected: 6 tests pass.

- [ ] **Step 7: Commit**

```bash
git add backend/api/
git commit -m "Add subscriptions API"
```

---

## Task 8: Ingredients API

**Files:**
- Create: `backend/api/serializers/ingredients.py`
- Create: `backend/api/views/ingredients.py`
- Modify: `backend/api/urls.py`
- Create: `backend/api/tests/test_ingredients.py`

**Interfaces:**
- Consumes: `recipes.models.Ingredient`.
- Produces: `GET /api/ingredients/`, `GET /api/ingredients/{id}/`, `?name=` filter.

- [ ] **Step 1: Write failing tests**

`backend/api/tests/test_ingredients.py`:
```python
from rest_framework import status
from rest_framework.test import APITestCase

from recipes.models import Ingredient


class IngredientTests(APITestCase):
    def setUp(self):
        Ingredient.objects.create(name="соль", measurement_unit="г")
        Ingredient.objects.create(name="сахар", measurement_unit="г")
        Ingredient.objects.create(name="солянка", measurement_unit="шт")

    def test_list_ingredients(self):
        response = self.client.get("/api/ingredients/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_filter_by_name_prefix_case_insensitive(self):
        response = self.client.get("/api/ingredients/", {"name": "СОЛ"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = {item["name"] for item in response.data}
        self.assertEqual(names, {"соль", "солянка"})
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && python manage.py test api.tests.test_ingredients -v 2`
Expected: 404, route doesn't exist.

- [ ] **Step 3: Write serializer**

`backend/api/serializers/ingredients.py`:
```python
from rest_framework import serializers

from recipes.models import Ingredient


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")
```

- [ ] **Step 4: Write viewset (no pagination for this one — spec returns a plain list)**

`backend/api/views/ingredients.py`:
```python
from rest_framework import viewsets

from api.serializers.ingredients import IngredientSerializer
from recipes.models import Ingredient


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.query_params.get("name")
        if name:
            queryset = queryset.filter(name__istartswith=name)
        return queryset
```

- [ ] **Step 5: Register on router**

Update `backend/api/urls.py` — after router creation:
```python
from api.views.ingredients import IngredientViewSet

router.register("ingredients", IngredientViewSet, basename="ingredients")
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd backend && python manage.py test api.tests.test_ingredients -v 2`
Expected: 2 tests pass.

- [ ] **Step 7: Commit**

```bash
git add backend/api/
git commit -m "Add ingredients API with name search"
```

---

## Task 9: Recipes API — serializers and core CRUD

**Files:**
- Create: `backend/api/serializers/recipes.py`
- Create: `backend/api/views/recipes.py`
- Modify: `backend/api/urls.py`
- Create: `backend/api/tests/test_recipes.py`

**Interfaces:**
- Consumes: `recipes.models.{Recipe,RecipeIngredient,Ingredient}`, `api.fields.Base64ImageField`, `api.permissions.IsAuthorOrReadOnly`, `api.serializers.users.UserSerializer`.
- Produces: `api.serializers.recipes.RecipeReadSerializer`, `RecipeWriteSerializer`; `api.views.recipes.RecipeViewSet` registered as `/api/recipes/`.

- [ ] **Step 1: Write failing tests**

`backend/api/tests/test_recipes.py`:
```python
from rest_framework import status
from rest_framework.test import APITestCase

from recipes.models import Ingredient, Recipe
from users.models import User

PIXEL = (
    "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABAgMAAABieywaAAAACVBMVEUAAAD/"
    "//9fX1/S0ecCAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAACklEQVQImWNoAAAAggCByxOyYQAAAABJRU5ErkJggg=="
)


class RecipeCRUDTests(APITestCase):
    def setUp(self):
        self.author = User.objects.create_user(
            username="chef", email="chef@example.com", password="x",
            first_name="C", last_name="C",
        )
        self.other = User.objects.create_user(
            username="guest", email="guest@example.com", password="x",
            first_name="G", last_name="G",
        )
        self.ingredient = Ingredient.objects.create(name="соль", measurement_unit="г")

    def test_create_recipe(self):
        self.client.force_authenticate(user=self.author)
        response = self.client.post(
            "/api/recipes/",
            {
                "ingredients": [{"id": self.ingredient.id, "amount": 5}],
                "image": PIXEL,
                "name": "Суп",
                "text": "Варить 30 минут",
                "cooking_time": 30,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Recipe.objects.count(), 1)
        self.assertEqual(response.data["ingredients"][0]["amount"], 5)

    def test_create_requires_auth(self):
        response = self.client.post(
            "/api/recipes/",
            {
                "ingredients": [{"id": self.ingredient.id, "amount": 5}],
                "image": PIXEL, "name": "Суп", "text": "x", "cooking_time": 1,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_rejects_empty_ingredients(self):
        self.client.force_authenticate(user=self.author)
        response = self.client.post(
            "/api/recipes/",
            {"ingredients": [], "image": PIXEL, "name": "Суп", "text": "x", "cooking_time": 1},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_rejects_duplicate_ingredients(self):
        self.client.force_authenticate(user=self.author)
        response = self.client.post(
            "/api/recipes/",
            {
                "ingredients": [
                    {"id": self.ingredient.id, "amount": 5},
                    {"id": self.ingredient.id, "amount": 3},
                ],
                "image": PIXEL, "name": "Суп", "text": "x", "cooking_time": 1,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_recipes_paginated(self):
        Recipe.objects.create(
            author=self.author, name="Суп", text="x", cooking_time=10, image="r.jpg",
        )
        response = self.client.get("/api/recipes/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)

    def test_update_only_by_author(self):
        recipe = Recipe.objects.create(
            author=self.author, name="Суп", text="x", cooking_time=10, image="r.jpg",
        )
        self.client.force_authenticate(user=self.other)
        response = self.client.patch(
            f"/api/recipes/{recipe.id}/",
            {
                "ingredients": [{"id": self.ingredient.id, "amount": 1}],
                "image": PIXEL, "name": "Новый суп", "text": "x", "cooking_time": 5,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_only_by_author(self):
        recipe = Recipe.objects.create(
            author=self.author, name="Суп", text="x", cooking_time=10, image="r.jpg",
        )
        self.client.force_authenticate(user=self.other)
        response = self.client.delete(f"/api/recipes/{recipe.id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && python manage.py test api.tests.test_recipes -v 2`
Expected: 404s.

- [ ] **Step 3: Write serializers**

`backend/api/serializers/recipes.py`:
```python
from django.db import transaction
from rest_framework import serializers

from api.fields import Base64ImageField
from api.serializers.users import UserSerializer
from recipes.models import Ingredient, Recipe, RecipeIngredient


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="ingredient.id")
    name = serializers.CharField(source="ingredient.name")
    measurement_unit = serializers.CharField(source="ingredient.measurement_unit")

    class Meta:
        model = RecipeIngredient
        fields = ("id", "name", "measurement_unit", "amount")


class RecipeIngredientWriteSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(min_value=1)


class RecipeReadSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientReadSerializer(
        source="recipe_ingredients", many=True, read_only=True,
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            "id", "author", "ingredients", "is_favorited",
            "is_in_shopping_cart", "name", "image", "text", "cooking_time",
        )

    def _user(self):
        request = self.context.get("request")
        return request.user if request and request.user.is_authenticated else None

    def get_is_favorited(self, obj):
        user = self._user()
        return bool(user) and obj.favorited_by.filter(user=user).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self._user()
        return bool(user) and obj.in_carts.filter(user=user).exists()


class RecipeWriteSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientWriteSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ("id", "ingredients", "image", "name", "text", "cooking_time")

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError("Нужен хотя бы один ингредиент")
        ids = [item["id"].id for item in value]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError("Ингредиенты не должны повторяться")
        return value

    @transaction.atomic
    def create(self, validated_data):
        ingredients = validated_data.pop("ingredients")
        recipe = Recipe.objects.create(
            author=self.context["request"].user, **validated_data,
        )
        self._set_ingredients(recipe, ingredients)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients = validated_data.pop("ingredients", None)
        instance = super().update(instance, validated_data)
        if ingredients is not None:
            instance.recipe_ingredients.all().delete()
            self._set_ingredients(instance, ingredients)
        return instance

    def _set_ingredients(self, recipe, ingredients):
        RecipeIngredient.objects.bulk_create(
            RecipeIngredient(
                recipe=recipe, ingredient=item["id"], amount=item["amount"],
            )
            for item in ingredients
        )

    def to_representation(self, instance):
        return RecipeReadSerializer(instance, context=self.context).data
```

- [ ] **Step 4: Write viewset**

`backend/api/views/recipes.py`:
```python
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from api.pagination import LimitPageNumberPagination
from api.permissions import IsAuthorOrReadOnly
from api.serializers.recipes import RecipeReadSerializer, RecipeWriteSerializer
from recipes.models import Recipe


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.select_related("author").prefetch_related(
        "recipe_ingredients__ingredient",
    )
    permission_classes = (IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly)
    pagination_class = LimitPageNumberPagination

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params
        user = self.request.user

        if params.get("author"):
            queryset = queryset.filter(author_id=params["author"])
        if user.is_authenticated and params.get("is_favorited") == "1":
            queryset = queryset.filter(favorited_by__user=user)
        if user.is_authenticated and params.get("is_in_shopping_cart") == "1":
            queryset = queryset.filter(in_carts__user=user)
        return queryset
```

- [ ] **Step 5: Register on router**

Update `backend/api/urls.py`:
```python
from api.views.recipes import RecipeViewSet

router.register("recipes", RecipeViewSet, basename="recipes")
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd backend && python manage.py test api.tests.test_recipes -v 2`
Expected: 7 tests pass.

- [ ] **Step 7: Commit**

```bash
git add backend/api/
git commit -m "Add recipes API: CRUD with ingredient nesting and author permission"
```

---

## Task 10: Recipe actions — favorite, shopping_cart, get-link, download_shopping_cart

**Files:**
- Modify: `backend/api/views/recipes.py`
- Create: `backend/api/views/short_links.py`
- Modify: `backend/foodgram_backend/urls.py`
- Modify: `backend/api/urls.py`
- Create: `backend/api/tests/test_recipe_actions.py`

**Interfaces:**
- Consumes: `recipes.models.{Favorite,ShoppingCart,RecipeIngredient}`, `api.serializers.subscriptions.RecipeMinifiedSerializer`.
- Produces: `POST/DELETE /api/recipes/{id}/favorite/`, `POST/DELETE /api/recipes/{id}/shopping_cart/`, `GET /api/recipes/{id}/get-link/`, `GET /api/recipes/download_shopping_cart/`, redirect route `GET /s/<code>/`.

- [ ] **Step 1: Write failing tests**

`backend/api/tests/test_recipe_actions.py`:
```python
from rest_framework import status
from rest_framework.test import APITestCase

from recipes.models import Ingredient, Recipe, RecipeIngredient
from users.models import User


class RecipeActionTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="eater", email="e@example.com", password="x",
            first_name="E", last_name="E",
        )
        self.author = User.objects.create_user(
            username="chef", email="chef@example.com", password="x",
            first_name="C", last_name="C",
        )
        self.recipe = Recipe.objects.create(
            author=self.author, name="Суп", text="x", cooking_time=10, image="r.jpg",
        )
        self.client.force_authenticate(user=self.user)

    def test_favorite_add_and_remove(self):
        response = self.client.post(f"/api/recipes/{self.recipe.id}/favorite/")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = self.client.post(f"/api/recipes/{self.recipe.id}/favorite/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = self.client.delete(f"/api/recipes/{self.recipe.id}/favorite/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_shopping_cart_add_and_remove(self):
        response = self.client.post(f"/api/recipes/{self.recipe.id}/shopping_cart/")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = self.client.delete(f"/api/recipes/{self.recipe.id}/shopping_cart/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_get_link(self):
        response = self.client.get(f"/api/recipes/{self.recipe.id}/get-link/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("short-link", response.data)

    def test_download_shopping_cart_aggregates_amounts(self):
        salt = Ingredient.objects.create(name="соль", measurement_unit="г")
        other_recipe = Recipe.objects.create(
            author=self.author, name="Борщ", text="x", cooking_time=20, image="r2.jpg",
        )
        RecipeIngredient.objects.create(recipe=self.recipe, ingredient=salt, amount=5)
        RecipeIngredient.objects.create(recipe=other_recipe, ingredient=salt, amount=3)
        self.client.post(f"/api/recipes/{self.recipe.id}/shopping_cart/")
        self.client.post(f"/api/recipes/{other_recipe.id}/shopping_cart/")

        response = self.client.get("/api/recipes/download_shopping_cart/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = response.content.decode("utf-8")
        self.assertIn("соль", content)
        self.assertIn("8", content)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && python manage.py test api.tests.test_recipe_actions -v 2`
Expected: 404s, actions don't exist.

- [ ] **Step 3: Add actions to RecipeViewSet**

Extend `backend/api/views/recipes.py` (add imports and methods to the existing `RecipeViewSet` class):
```python
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.serializers.subscriptions import RecipeMinifiedSerializer
from recipes.models import Favorite, RecipeIngredient, ShoppingCart


class RecipeViewSet(viewsets.ModelViewSet):
    # ... existing queryset/permission_classes/pagination_class/get_serializer_class/get_queryset ...

    def _toggle_relation(self, model, request, pk, add_error, remove_error):
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == "POST":
            _, created = model.objects.get_or_create(user=request.user, recipe=recipe)
            if not created:
                return Response({"errors": add_error}, status=status.HTTP_400_BAD_REQUEST)
            serializer = RecipeMinifiedSerializer(recipe, context={"request": request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        deleted, _ = model.objects.filter(user=request.user, recipe=recipe).delete()
        if not deleted:
            return Response({"errors": remove_error}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post", "delete"], permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        return self._toggle_relation(
            Favorite, request, pk,
            "Рецепт уже в избранном", "Рецепта не было в избранном",
        )

    @action(detail=True, methods=["post", "delete"], permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        return self._toggle_relation(
            ShoppingCart, request, pk,
            "Рецепт уже в корзине", "Рецепта не было в корзине",
        )

    @action(detail=True, methods=["get"], url_path="get-link")
    def get_link(self, request, pk=None):
        from api.views.short_links import short_code_for
        request = self.request
        code = short_code_for(int(pk))
        link = request.build_absolute_uri(f"/s/{code}/")
        return Response({"short-link": link})

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        rows = (
            RecipeIngredient.objects
            .filter(recipe__in_carts__user=request.user)
            .values("ingredient__name", "ingredient__measurement_unit")
            .annotate(total=Sum("amount"))
            .order_by("ingredient__name")
        )
        lines = [
            f"{row['ingredient__name']} ({row['ingredient__measurement_unit']}) — {row['total']}"
            for row in rows
        ]
        content = "\n".join(lines) or "Список покупок пуст"
        response = HttpResponse(content, content_type="text/plain; charset=utf-8")
        response["Content-Disposition"] = "attachment; filename=shopping_cart.txt"
        return response
```

- [ ] **Step 4: Write short-link helper and redirect view**

`backend/api/views/short_links.py`:
```python
import string

from django.http import Http404
from django.shortcuts import redirect

ALPHABET = string.digits + string.ascii_letters


def short_code_for(recipe_id: int) -> str:
    if recipe_id == 0:
        return ALPHABET[0]
    digits = []
    base = len(ALPHABET)
    while recipe_id:
        recipe_id, rem = divmod(recipe_id, base)
        digits.append(ALPHABET[rem])
    return "".join(reversed(digits))


def recipe_id_from_code(code: str) -> int:
    base = len(ALPHABET)
    recipe_id = 0
    for char in code:
        recipe_id = recipe_id * base + ALPHABET.index(char)
    return recipe_id


def resolve_short_link(request, code):
    try:
        recipe_id = recipe_id_from_code(code)
    except ValueError:
        raise Http404
    return redirect(f"/recipes/{recipe_id}")
```

- [ ] **Step 5: Wire the `/s/<code>/` redirect at project level**

Modify `backend/foodgram_backend/urls.py` — add:
```python
from api.views.short_links import resolve_short_link
# ...
urlpatterns = [
    path("admin/", admin.site.urls),
    path("s/<str:code>/", resolve_short_link, name="short-link-redirect"),
    path("api/", include("api.urls")),
]
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd backend && python manage.py test api.tests.test_recipe_actions -v 2`
Expected: 4 tests pass.

- [ ] **Step 7: Run the full backend test suite**

Run: `cd backend && python manage.py test`
Expected: all tests across `users`, `recipes`, `api` pass.

- [ ] **Step 8: flake8 check**

Run: `cd backend && flake8 .`
Expected: no output (clean).

- [ ] **Step 9: Commit**

```bash
git add backend/
git commit -m "Add favorite, shopping_cart, get-link, and download_shopping_cart actions"
```

---

## Task 11: Local smoke test against SQLite

**Files:** none (verification task, no new files)

**Interfaces:** none — this task only exercises what Tasks 1–10 built.

- [ ] **Step 1: Run the server locally**

Run:
```bash
cd backend
python manage.py migrate
python manage.py load_ingredients
python manage.py createsuperuser --noinput --username admin --email admin@example.com || true
python manage.py changepassword admin   # set a known password interactively, or use shell:
python manage.py runserver 0.0.0.0:8000
```

- [ ] **Step 2: Exercise the admin panel**

Open `http://localhost:8000/admin/`, log in, confirm `Users`, `Subscriptions`, `Recipes` (with inline ingredients), `Ingredients`, `Favorite`, `ShoppingCart` are all visible and the Recipe list shows the `favorites_count` column.

- [ ] **Step 3: Run the course's Postman collection**

Import `postman_collection/foodgram.postman_collection.json` into Postman (or run with `newman run postman_collection/foodgram.postman_collection.json` if newman is installed), point its base URL at `http://localhost:8000`, run the full collection.
Expected: all requests pass. Fix any mismatch against `docs/openapi-schema.yml` found here before moving to containerization — this is the same check the course reviewer will run.

- [ ] **Step 4: Commit any fixes found during this pass**

If Step 3 surfaces bugs, fix them in the relevant file from Tasks 6–10, re-run the affected test file, then:
```bash
git add backend/
git commit -m "Fix issues found running the Postman collection"
```

---

## Task 12: Containerize — Dockerfile, docker-compose, nginx

**Files:**
- Create: `backend/Dockerfile`
- Create: `backend/entrypoint.sh`
- Modify: `infra/docker-compose.yml`
- Modify: `infra/nginx.conf`
- Create: `.env.example` (repo root)

**Interfaces:** none new — wraps the existing Django project in containers; no application code changes.

- [ ] **Step 1: Write backend Dockerfile**

`backend/Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
```

- [ ] **Step 2: Write entrypoint.sh**

`backend/entrypoint.sh`:
```bash
#!/bin/sh
set -e

python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py load_ingredients

exec gunicorn foodgram_backend.wsgi:application --bind 0.0.0.0:8000
```

- [ ] **Step 3: Write .env.example**

`.env.example` (repo root):
```
POSTGRES_DB=foodgram
POSTGRES_USER=foodgram
POSTGRES_PASSWORD=change-me
DB_HOST=db
DB_PORT=5432
DJANGO_SECRET_KEY=change-me
DJANGO_DEBUG=0
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
```

- [ ] **Step 4: Extend docker-compose.yml to three containers**

Replace `infra/docker-compose.yml` contents:
```yaml
version: '3.3'
services:

  db:
    container_name: foodgram-db
    image: postgres:13
    env_file: ../.env
    volumes:
      - pg_data:/var/lib/postgresql/data

  backend:
    container_name: foodgram-backend
    build: ../backend
    env_file: ../.env
    depends_on:
      - db
    volumes:
      - static_data:/app/static
      - media_data:/app/media

  frontend:
    container_name: foodgram-front
    build: ../frontend
    volumes:
      - ../frontend/:/app/result_build/

  nginx:
    container_name: foodgram-proxy
    image: nginx:1.25.4-alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
      - ../frontend/build:/usr/share/nginx/html/
      - ../docs/:/usr/share/nginx/html/api/docs/
      - static_data:/var/html/static
      - media_data:/var/html/media
    depends_on:
      - backend
      - frontend

volumes:
  pg_data:
  static_data:
  media_data:
```

- [ ] **Step 5: Extend nginx.conf to proxy API/admin/static/media**

Replace `infra/nginx.conf` contents:
```nginx
server {
    listen 80;
    client_max_body_size 20M;

    location /api/docs/ {
        root /usr/share/nginx/html;
        try_files $uri $uri/redoc.html;
    }

    location /api/ {
        proxy_set_header Host $http_host;
        proxy_pass http://backend:8000/api/;
    }

    location /admin/ {
        proxy_set_header Host $http_host;
        proxy_pass http://backend:8000/admin/;
    }

    location /static/admin/ {
        root /var/html;
        alias /var/html/static/admin/;
    }

    location /media/ {
        root /var/html;
    }

    location / {
        root /usr/share/nginx/html;
        index index.html index.htm;
        try_files $uri $uri/ /index.html;
    }
}
```

- [ ] **Step 6: Build and run the full stack**

Run:
```bash
cp .env.example .env   # fill in real values
cd infra
docker compose up -d --build
```

- [ ] **Step 7: Verify the containerized stack**

Run:
```bash
curl -s -o /dev/null -w "%{http_code}\n" http://localhost/
curl -s -o /dev/null -w "%{http_code}\n" http://localhost/api/ingredients/
curl -s -o /dev/null -w "%{http_code}\n" http://localhost/admin/
docker compose exec backend python manage.py createsuperuser
```
Expected: `200` for `/` and `/api/ingredients/`, `200` or `302` for `/admin/`. Re-run the Postman collection (Task 11 Step 3) against `http://localhost` this time.

- [ ] **Step 8: Commit**

```bash
cd ~/интеграция/foodgram
git add backend/Dockerfile backend/entrypoint.sh infra/ .env.example
git commit -m "Containerize: Postgres + Django/Gunicorn + nginx + frontend"
```

(`.env` itself stays untracked — confirm it's covered by the existing root `.gitignore`, which already lists `.env`.)

---

## Task 13: Push to GitHub and Docker Hub

**Files:** none (deployment task)

**Interfaces:** none.

- [ ] **Step 1: Point the repo at Матвей's own GitHub remote**

Run (once his repo + token are confirmed working — this is the same blocker tracked for the sibling `pdd_club` repo):
```bash
cd ~/интеграция/foodgram
git remote set-url origin https://<TOKEN>@github.com/MatveySolntsev-ML/<repo-name>.git
git push -u origin main
```

- [ ] **Step 2: Build and push the backend image to Docker Hub**

Needs Матвей's Docker Hub username/password or access token.
```bash
docker build -t <dockerhub-username>/foodgram-backend:latest backend/
docker login
docker push <dockerhub-username>/foodgram-backend:latest
```

- [ ] **Step 3: Point docker-compose at the pushed image for the final demo**

In `infra/docker-compose.yml`, change the `backend` service's `build: ../backend` to `image: <dockerhub-username>/foodgram-backend:latest` (keep a `docker-compose.dev.yml` or comment noting the `build:` variant for local iteration, since switching to `image:` stops picking up local code changes).

- [ ] **Step 4: Final end-to-end check before the defense**

Run `docker compose up -d --pull always`, re-run the Postman collection, re-check the admin panel, confirm `git log` on GitHub shows the full history. This is the exact checklist from the teacher's photo: Postman, admin demo, code in GitHub, containerized.
