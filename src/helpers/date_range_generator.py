from datetime import date, timedelta


def generate_date_list(start_date: date, end_date: date) -> list[date]:
    """Generate list of dates between start_date and end_date inclusive."""
    date_list: list[date] = []
    current_date: date = start_date
    while current_date <= end_date:
        date_list.append(current_date)
        current_date += timedelta(days=1)
    return date_list
