"""Methods for dealing with OCF lab hours.

All times are assumed to be OST (OCF Standard Time).

Usage:

    >>> from ocflib.lab.hours import Day
    >>> Day.from_date(date(2015, 10, 12))
    Day(
        date=datetime.date(2015, 10, 12),
        weekday='Monday',
        holiday=None,
        hours=[Hour(open=9, close=21)],
    )
"""
from collections import namedtuple
from datetime import date
from datetime import datetime
from datetime import time
from datetime import timedelta

import requests

HOURS_URL = 'https://ocf.berkeley.edu/api/hours'


def _pull_hours():
    """small helper to make testing easier"""
    return requests.get(HOURS_URL).json()


def _generate_regular_hours():
    """produce hours in the manner previously exposed by the hardcoded REGULAR_HOURS variable,
       but pull the data from ocfweb instead, where the hours come from a Google Spreadsheet."""

    regular_hours = {}

    for day, hours in _pull_hours().items():
        regular_hours[int(day)] = [Hour(open=_parsetime(hour[0]),
                                        close=_parsetime(hour[1]),
                                        staffer=hour[2]) for hour in hours]

    return regular_hours


def _parsetime(t):
    return datetime.strptime(t, '%H:%M:%S').time()


class Hour(namedtuple('Hours', ['open', 'close', 'staffer'])):
    """duplicating class to ocfweb until this can be refactored"""

    def __contains__(self, when):
        if isinstance(when, time):
            return self.open <= when < self.close
        return self.open <= when.time() < self.close


class Day(namedtuple('Day', ['date', 'weekday', 'holiday', 'hours'])):

    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6

    @classmethod
    def from_date(cls, when=None):
        """Return whether a Day representing the given day.

        If not provided, when defaults to today.
        """
        if not when:
            when = date.today()

        if isinstance(when, datetime):
            when = when.date()

        # check if it's a holiday
        my_holiday = None
        my_hours = REGULAR_HOURS[when.weekday()]

        for start, end, name, hours in HOLIDAYS:
            if start <= when <= end:
                my_holiday = name
                my_hours = hours
                break

        return cls(
            date=when,
            weekday=when.strftime('%A'),
            holiday=my_holiday,
            hours=my_hours,
        )

    def is_open(self, when=None):
        """Return whether the lab is open at the given time.

        If not provided, when defaults to now.
        """
        if not when:
            when = datetime.now()

        if not isinstance(when, datetime):
            raise ValueError('{} must be a datetime instance'.format(when))

        if self.date != when.date():
            raise ValueError('{} is on a different day than {}'.format(when, self))

        return any(when in hour for hour in self.hours)

    def time_to_open(self, when=None):
        """Return timedelta object representing time until the lab is open from the given time.

        If not provided, defaults to now"""
        if not when:
            when = datetime.now()

        if not isinstance(when, datetime):
            raise ValueError('{} must be a datetime instance'.format(when))

        if self.date != when.date():
            raise ValueError('{} is on a different day than {}'.format(when, self))

        if self.is_open(when=when):
            return timedelta()

        def date_opens(date):
            return [datetime.combine(date, h.open) for h in Day.from_date(date).hours]
        opens = date_opens(self.date)
        # because we assume when is in the current day, any hours in future dates don't need to be filtered
        opens = [o for o in opens if o > when]
        date = self.date
        while not opens:
            date += timedelta(days=1)
            opens = date_opens(date)

        return opens[0] - when

    def time_to_close(self, when=None):
        """Return timedelta object representing time until the lab is closed from the given time.

        If not provided, defaults to now"""
        if not when:
            when = datetime.now()

        if not isinstance(when, datetime):
            raise ValueError('{} must be a datetime instance'.format(when))

        if self.date != when.date():
            raise ValueError('{} is on a different day than {}'.format(when, self))

        # because hour intervals should not overlap this should be length 0 or 1
        hours = [hour for hour in self.hours if when in hour]
        if not hours:
            return timedelta()
        return datetime.combine(self.date, hours[0].close) - when

    @property
    def closed_all_day(self):
        return not self.hours


REGULAR_HOURS = _generate_regular_hours()


HOLIDAYS = [
    # start date, end date, holiday name, list of hours (date ranges are inclusive)
    (date(2017, 5, 13), date(2017, 8, 23), 'Summer Break', []),
    (date(2017, 9, 4), date(2017, 9, 4), 'Labor Day', []),
    (date(2017, 11, 10), date(2017, 11, 10), 'Veterans Day', []),
    (date(2017, 11, 22), date(2017, 11, 26), 'Thanksgiving Break', []),
    (date(2017, 12, 15), date(2017, 12, 15), 'Last Day Fall 2017', [Hour(time(9), time(12), 'staff')]),
    (date(2017, 12, 16), date(2018, 1, 15), 'Winter Break', []),
    (date(2018, 2, 19), date(2018, 2, 19), 'Presidents\' Day', []),
    (date(2018, 3, 24), date(2018, 4, 1), 'Spring Break', []),
    (date(2017, 12, 15), date(2017, 12, 15), 'Last Day Fall 2017', [Hour(time(9), time(12), 'staff')]),
    (date(2017, 12, 16), date(2017, 1, 16), 'Winter Break', []),
]
