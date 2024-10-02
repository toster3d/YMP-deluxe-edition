from datetime import datetime, timedelta
from typing import List


def generate_date_list(start_date: datetime, end_date: datetime) -> List[datetime]:
    """
    Generate a list of dates from start_date to end_date, inclusive.

    Args:
        start_date (datetime): The starting date of the range.
        end_date (datetime): The ending date of the range.

    Returns:
        List[datetime]: A list of datetime objects representing each day in the range.

    Example:
        >>> from datetime import datetime
        >>> start = datetime(2023, 1, 1)
        >>> end = datetime(2023, 1, 5)
        >>> generate_date_list(start, end)
        [datetime(2023, 1, 1), datetime(2023, 1, 2), datetime(2023, 1, 3),
         datetime(2023, 1, 4), datetime(2023, 1, 5)]
    """
    date_list: List[datetime] = []
    current_date = start_date
    while current_date <= end_date:
        date_list.append(current_date)
        current_date += timedelta(days=1)
    return date_list
