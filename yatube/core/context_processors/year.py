import datetime


def year(request):
    date = datetime.datetime.today()
    now = date.year
    return {
        'year': now,
    }
