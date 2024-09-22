from datetime import datetime, timedelta

class DateService:
    @staticmethod
    def parse_date(date_str, date_format="%A %d %B %Y"):
        """Parses a date string into a datetime object."""
        return datetime.strptime(date_str, date_format)

    @staticmethod
    def generate_date_list(start_date, end_date):
        """Generates a list of dates between start_date and end_date."""
        date_list = []
        while start_date <= end_date:
            date_list.append(start_date.strftime("%A %d %B %Y"))
            start_date += timedelta(days=1)
        return date_list

    @staticmethod
    def get_today():
        """Returns today's date formatted as a string."""
        today = datetime.now().strftime("%A %d %B %Y")
        print(f"Today's date: {today}")  # Debugowanie
        return today
