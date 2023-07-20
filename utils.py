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
        return False
    start = start_time(event)
    return start is not None


def attendees_without_resources(event):
    """Gets the human attendees for an event."""
    attendees = event.get('attendees', [])
    attendees = [a for a in attendees if not a.get('resource', False)]
    return attendees


def did_attendee_accept(attendee):
    """ Check if the given attendee accepted """
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
    return did_attendee_accept(attendee)


def is_confirmed(event):
    """Check if the event has been confirmed or not."""
    return event.get('status', 'tentative') == 'confirmed'


def is_one_on_one(event):
    """Check if the event is (probably) a 1-on-1 meeting.
    
    Note there are edge cases where this check is not accurate, such
    as a meeting where one of the two participants is a group.
    """
    if not is_meeting(event):
        return False

    attendees = attendees_without_resources(event)
    if len(attendees) != 2:
        return False
    
    return True


def is_group_meeting(event):
    """Check if the event is a group meeting with 3+ attendees.
    
    Note there are edge cases where this check is not accurate, such
    as a meeting where one of the two participants is a group.
    """
    if not is_meeting(event):
        return False

    attendees = attendees_without_resources(event)
    if len(attendees) <= 2:
        return False
        
    return True

