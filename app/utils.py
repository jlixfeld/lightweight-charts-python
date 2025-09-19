"""Utility functions for the application."""


def sort_timeframes_chronologically(timeframes: list[str]) -> list[str]:
    """Sort timeframes chronologically: Xmin > Xh > Xd > Xw > Xm > Xq > Xy"""

    def timeframe_sort_key(tf: str) -> tuple[int, int]:
        # Extract number and unit
        tf_lower = tf.lower()

        # Find where the unit starts
        unit_start = 0
        for i, char in enumerate(tf_lower):
            if char.isalpha():
                unit_start = i
                break

        # Extract number (default to 1 if no number)
        number_part = tf_lower[:unit_start] if unit_start > 0 else "1"
        try:
            number = int(number_part)
        except ValueError:
            number = 1

        # Extract unit
        unit = tf_lower[unit_start:]

        # Define unit priority (lower number = shorter timeframe)
        unit_priority = {
            "min": 1,  # minutes
            "h": 2,  # hours
            "d": 3,  # days
            "w": 4,  # weeks
            "m": 5,  # months (in your setup)
            "q": 6,  # quarters
            "y": 7,  # years
        }

        priority = unit_priority.get(unit, 999)  # Unknown units go to end

        return (priority, number)

    return sorted(timeframes, key=timeframe_sort_key)
