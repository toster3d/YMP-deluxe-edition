from datetime import date, datetime, timedelta


def generate_date_list(start_date: datetime, end_date: datetime) -> list[date]:
    date_list: list[date] = []
    current_date: datetime = start_date
    while current_date <= end_date:
        date_list.append(current_date)
        current_date += timedelta(days=1)
    return date_list
