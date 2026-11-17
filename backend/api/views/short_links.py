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
