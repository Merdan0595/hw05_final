from django.core.paginator import Paginator

POSTS_ON_PAGE = 10


def get_page_number(value, request):
    paginator = Paginator(value, POSTS_ON_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
