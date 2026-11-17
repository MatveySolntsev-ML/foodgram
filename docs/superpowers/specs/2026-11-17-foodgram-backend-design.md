# Foodgram backend — design

Diploma/exam project for РЭУ course «Интеграция и управление приложениями на
удалённом сервере» (built on Яндекс.Практикум backend-разработчик
curriculum). Deadline: defense Thursday 2026-11-19, 14:00, ауд. 6.13(9).
Scope confirmed with Матвей 2026-11-17: full checklist, not MVP — three
containers (nginx, PostgreSQL, Django+Gunicorn), image on Docker Hub.

Contract is fixed by `docs/openapi-schema.yml` (already in repo) — this
design is about how to structure Django apps/models to satisfy it, not
about API behavior, which is not up for debate.

## Apps

- **users** — custom `User` (`AbstractUser` subclass, `USERNAME_FIELD =
  "email"`, `REQUIRED_FIELDS = ["username", "first_name", "last_name"]`,
  unique email, optional `avatar` ImageField), `Subscription`
  (follower → author, unique-together, can't self-subscribe).
- **recipes** — `Ingredient` (name, measurement_unit; loaded from
  `data/ingredients.json` via a management command), `Recipe` (author,
  name, image, text, cooking_time ≥ 1), `RecipeIngredient` (through model:
  recipe, ingredient, amount ≥ 1), `Favorite`, `ShoppingCart` (both
  user+recipe unique-together).
- **api** — serializers, viewsets, routers for every path in the OpenAPI
  spec. No separate "core" app needed at this size — shared permission
  (`IsAuthorOrReadOnly`) and pagination class live in `api/`.

## Auth

Djoser + DRF `TokenAuthentication`. Djoser endpoints cover
`/api/auth/token/login`, `/api/auth/token/logout`,
`/api/users/`, `/api/users/me/`, `/api/users/set_password/` out of the
box with custom serializers swapped in via `DJOSER` settings
(`CustomUserCreate`/`CustomUserResponseOnCreate` shapes). Login is by
email+password per `TokenCreate` schema.

## Custom behavior beyond Djoser defaults

- `avatar` PUT/DELETE on `/api/users/me/avatar/` — small custom view.
- `is_subscribed`/`is_in_shopping_cart`/`is_favorited` — computed
  `SerializerMethodField`s against `request.user`.
- Base64 image upload — custom `Base64ImageField(serializers.ImageField)`
  overriding `to_internal_value` to decode `data:image/...;base64,...`
  into a `ContentFile`. Used for both recipe `image` and user `avatar`.
- `RecipeCreate`/`RecipeUpdate` — override `create`/`update` on the
  serializer to write the `RecipeIngredient` rows (bulk_create),
  validating: ingredients list non-empty, no duplicate ingredient ids,
  each amount ≥ 1.
- `/api/recipes/{id}/get-link/` — short link: generate a short base62
  code per recipe (stored field or deterministic from id), resolved by a
  tiny redirect view to the recipe's frontend URL.
- `/api/recipes/download_shopping_cart/` — aggregate
  `RecipeIngredient` rows across the user's `ShoppingCart` recipes
  (`group by ingredient, sum(amount)`), render as a `.txt` attachment.
- Ingredient search — `/api/ingredients/?name=` filters
  case-insensitive, "starts with".
- Pagination — DRF `PageNumberPagination`, `page_size_query_param =
  "limit"` (matches Foodgram's conventional `?page=&limit=`).
- Permissions — read endpoints open to anyone; write/delete on a recipe
  restricted to its author; favorite/cart/subscribe require
  authentication.

## Infra (full checklist)

Three containers per `infra/docker-compose.yml` (extended from the
provided skeleton, which only has `frontend`+`nginx`):
- `db` — `postgres:13`, named volume for data.
- `backend` — Django + Gunicorn, `entrypoint.sh` runs `migrate`,
  `collectstatic`, `load_ingredients` management command, then
  `gunicorn pdd_service... ` (project name TBD at scaffold time).
- `nginx` — extended to proxy `/api/` and `/admin/` to `backend`, serve
  `/media/` and `/static/` from shared volumes, keep serving the built
  frontend as the skeleton already does.
Image gets pushed to Docker Hub as part of finishing up (`docker build`
+ `docker push`) — needs Матвей's Docker Hub account/credentials when we
get there; not blocking initial development (use local build first).

Local dev before everything is containerized: run against the same
Postgres via `docker compose up db` + `manage.py runserver`, to catch
Postgres-specific issues early instead of discovering them only at the
end inside containers.

## Testing / verification

- Postman collection already in `postman_collection/` — run it against
  the running stack as the main functional check (matches what the
  course review process uses).
- `flake8` via existing `setup.cfg` for PEP 8 (explicit course
  requirement).
- Django admin registered for all models (explicit checklist item:
  "Демонстрация админки и её настройки").
- No automated test suite is required by the course (no autotests per
  the course's own README) — skip writing a pytest suite; manual
  Postman + admin + Postman is the verification loop here, given the
  Thursday deadline.

## Out of scope / explicitly deferred

- React frontend changes — frontend is provided pre-built, not touched.
- Tags/multi-category recipes — not in this course variant's OpenAPI
  spec (unlike some public Foodgram forks), so not implemented.
