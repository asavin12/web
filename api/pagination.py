from rest_framework.pagination import PageNumberPagination


class FlexiblePageNumberPagination(PageNumberPagination):
    """Pagination class that allows custom page_size from query params"""
    page_size = 20  # default
    page_size_query_param = 'page_size'
    max_page_size = 100
