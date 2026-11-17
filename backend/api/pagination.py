from rest_framework.pagination import PageNumberPagination


class LimitPageNumberPagination(PageNumberPagination):
    """Placeholder pagination class.

    Fleshed out in Task 8; exists here only so
    REST_FRAMEWORK["DEFAULT_PAGINATION_CLASS"] (set in Task 1) resolves and
    `manage.py check` can pass.
    """

    page_size_query_param = "limit"
