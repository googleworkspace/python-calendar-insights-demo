# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

""" Helpers for information about a calendar event. """

from datetime import datetime

class TimeInterval:
    """ Utility class for time ranges """
    def __init__(self, start, end):
        self.start = start
        self.end = end

    def overlaps(self, interval):
        """ Check if this overlaps with another range """
        return max(self.start, interval.start) < min(self.end, interval.end)

    def merge(self, interval):
        """ Creates a new range spanning the total time """
        return TimeInterval(min(self.start, interval.start), max(self.end, interval.end))

    def duration(self):
        """ Calculates the duration of the range """
        return self.end - self.start

    def date(self):
        """ Gets the day the range starts on """
        return self.start.date()

    def __str__(self):
        return f"range({self.start}-{self.end}"


def time_range(event):
    """ Gets a time range representing the event. Returns None for all-day events """
    start = start_time(event)
    end = end_time(event)

    if None in [start, end]:
        return None

    return TimeInterval(start, end)


def start_time(event):
    """Gets the start time of an event if present.
    
    Returns None for all-day events.
    """
    start = event.get('start', {}).get('dateTime', None)
    if start is None:
        return None
    return datetime.fromisoformat(start)


def end_time(event):
    """Gets the end time of an event if present.
    
    Returns None for all-day events.
    """
    end = event.get('end', {}).get('dateTime', None)
    if end is None:
        return None
    return datetime.fromisoformat(end)


def is_meeting(event):
    """Checks if an event represent a meeting.
    
    This excludes all-day events as well as non-meeting events like focus time
    or working location indicators
    """
    event_type = event.get('eventType', 'default')
    if event_type in ['outOfOffice', 'focusTime', 'workingLocation']:
        # Ignore non-meeting events
        return False

    start = start_time(event)
    return start is not None


def is_busy(event):
    """ Check if event is marked busy vs free """
    if event.get('transparency', 'opaque') == 'transparent':
        return False
    if not is_accepted(event):
        return False
    return True


def is_pending(event):
    """ Check if event is pending confirmation/acceptance """
    if event.get('status', 'tentative') == 'tentative':
        return True

    attendee = self_attendee(event)
    if attendee is not None:
        return attendee.get('responseStatus', 'needsAction') in ['needsAction', 'tentative']

    return False


def count_attendees(event):
    """ Count the number of attendees """
    count = 0

    if is_organizer_attendee(event):
        count += 1

    attendees = attendees_without_resources(event)
    for attendee in attendees:
        count += 1 + attendee.get('additionalGuests', 0)

    return count


def is_organizer_attendee(event):
    """ Check if the organizer should be considered an attendee or not """
    is_self = event.get('organizer', {}).get('self', False)
    organizer_email = event.get('organizer', {}).get('email', '')
    is_secondary_calendar = organizer_email.endswith('calendar.google.com')
    is_in_attendee_list =  find_attendee(event, organizer_email) is not None

    return not is_self and not is_secondary_calendar and not is_in_attendee_list


def find_attendee(event, email):
    """ Finds an attendee by email """
    attendees = event.get('attendees', [])
    return next((attendee for attendee in attendees if attendee.get('email') == email), None)


def attendees_without_resources(event):
    """Gets the human attendees for an event."""
    attendees = event.get('attendees', [])
    attendees = [a for a in attendees if not a.get('resource', False)]
    return attendees


def did_attendee_accept(attendee):
    """ Check if the given attendee accepted. """
    return attendee.get('responseStatus', 'needsAction') == 'accepted'


def self_attendee(event):
    """Gets the response status for the current user/event."""
    attendees = event.get('attendees', [])
    for attendee in attendees:
        if attendee.get('self', False):
            return attendee
    return None


def is_accepted(event):
    """Check if the current user accepted the event."""
    attendee = self_attendee(event)
    if attendee is None:
        # Possible self is not in attendee list if event was just created
        # to block out time
        return True
    return did_attendee_accept(attendee)


def is_confirmed(event):
    """Check if the event has been confirmed or not."""
    return event.get('status', 'tentative') == 'confirmed'


def are_attendees_missing(event):
    """ Check if attendees are potentially excluded from the event """
    if event.get('attendeesOmitted', False):
        # API explicitly says attendee list incomplete
        return True

    if not is_organizer(event) and not event.get('guestsCanSeeOtherGuests', True):
        # Guests can't see others and not organizer, list may be incomplete
        return True

    return False


def is_organizer(event):
    """ Check if current user is the event organizer """
    return event.get('organizer', {}).get('self', False)


def is_one_on_one(event):
    """Check if the event is (probably) a 1-on-1 meeting.
    
    Note there are edge cases where this check is not accurate, such
    as a meeting where one of the two participants is a group.

    See https://b.corp.google.com/issues/134133842
    """
    if not is_meeting(event):
        return False

    if are_attendees_missing(event):
        return False

    return count_attendees(event) == 2


def is_group_meeting(event):
    """Check if the event is a group meeting with 3+ attendees.
    
    Note there are edge cases where this check is not accurate, such
    as a meeting where one of the two participants is a group.

    See https://b.corp.google.com/issues/134133842
    """
    if not is_meeting(event):
        return False

    if are_attendees_missing(event):
        return True

    return count_attendees(event) >= 3


def is_recurring(event):
    """ Check if the event is a recurring event or not. """
    return event.get('recurringEventId') is not None
