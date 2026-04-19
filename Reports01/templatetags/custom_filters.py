from django import template

from datetime import datetime

register = template.Library()

@register.filter(name='user_in_group')
def user_in_group(user, group_name):
    return user.groups.filter(name=group_name).exists()


@register.filter
def split_sentences(value):
    sentences = value.split(';')
    return sentences

@register.simple_tag
def page_url(value, field_name, urlencode=None):
    url = '?{}={}'.format(field_name, value)

    if urlencode:
        querystring = urlencode.split('&')
        filtered_querystring = filter(lambda p: p.split('=')[0]!=field_name, querystring)
        encoded_querystring = '&'.join(filtered_querystring)
        url = '{}&{}'.format(url, encoded_querystring)
    return url

@register.filter
def convert_date_format(value):
    date_obj = datetime.strptime(value, "%Y-%m")
    formatted_date = date_obj.strftime('%b-%Y')
    return formatted_date

@register.filter
def get_quarter(date):
    if isinstance(date,datetime):
        quarter = (date.month -1) // 3 + 1
        return quarter
    return None

@register.filter
def excel_date_format(value):
    formatted_date = value.strftime('%d-%b-%Y')
    return formatted_date

@register.filter(name='get_month_name')
def get_month_name(month):
    month_names = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]

    try:
        numeric_month = int(month)
    except Exception:
        return ""

    return month_names[numeric_month - 1] if 1 <= numeric_month <= 12 else ""

@register.filter
def get_week_from_date(value):
    day_number = value.day
    day_name = value.strftime('%a')
    week = []
    if day_number <= 7:
        week = 'Week 1'
    elif day_number <= 14:
        week = 'Week 2'
    elif day_number <= 21:
        week = 'Week 2'
    else:
        week = 'Week 4'
    return week


