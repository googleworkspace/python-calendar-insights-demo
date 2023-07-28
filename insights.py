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

""" Generates insights from a series of calendar events. """
from datetime import datetime, timedelta, time
from dataclasses import dataclass

from utils import attendees_without_resources, end_time, is_accepted, is_busy, is_confirmed
from utils import is_group_meeting, is_pending, time_range
from utils import is_meeting, is_one_on_one, start_time, did_attendee_accept


class Insight:
    """ Base class for calculating an insight."""

    def __init__(self, name, working_hours):
        self.name = name
        self._working_hours = working_hours

    def filter(self, event):
        """ Check if an event is relevant for the insight.
        
        Default behavior restricts to accepted/confirmed events with defined start/ends.
        """
        if not is_meeting(event):
            print("Not meeting")
            print(event)
            return False

        if not is_accepted(event):
            print("Not accepted")
            print(event)
            return False

        if not is_confirmed(event):
            print("Not confirmed")
            print(event)
            return False

        if not is_busy(event):
            print("Not busy")
            print(event)
            return False

        return True

    def process(self, event):
        """ Processes a calendar event.
        
        Events are expected to be processed in chronological order.
        Implementations should override _onEvent instead of this.
        """
        if self.filter(event) is False:
            return
        self._on_event(event)

    def _on_event(self, event):
        """ Process the event after filtering has been applied. """

    def generate(self):
        """ Generates the insight data. """
        return {}


class DailyTimeInMeetings(Insight):
    """ Computes the total time spent in meetings for each day. """

    def __init__(self, name, working_hours):
        super().__init__(name, working_hours)
        self._days = {}
        self._previous_interval = None

    def _on_event(self, event):
        interval = time_range(event)

        if interval is None:
            return

        if self._previous_interval is None or not interval.overlaps(self._previous_interval):
            # Non overlapping range, add as is
            self._previous_interval = interval
            day = interval.date()
            self._days[day] = interval.duration() + self._days.get(day, timedelta(minutes=0))
            return

        # Range overlaps, add only the additional time from the new event
        merged_interval = self._previous_interval.merge(interval)
        duration = merged_interval.duration() - self._previous_interval.duration()

        day = merged_interval.date()
        self._days[day] = duration + self._days.get(day, timedelta(minutes=0))
        self._previous_interval = merged_interval

    def generate(self):
        return self._days


class DailyTimeInOneOnOne(DailyTimeInMeetings):
    """ Computes the total time spent in 1-on-1 meetings for each day. """

    def filter(self, event):
        if not is_one_on_one(event):
            return False
        return super().filter(event)


class DailyTimeInGroupMeetings(DailyTimeInMeetings):
    """ Computes the total time spent in group (3+ people) meetings for each day. """

    def filter(self, event):
        if not is_group_meeting(event):
            return False
        return super().filter(event)

class DailyTimeInUnconfirmedMeetings(DailyTimeInMeetings):
    """ Computes the total time spent in group (3+ people) meetings for each day. """

    def filter(self, event):
        return is_meeting(event) and is_pending(event)

class DailyTimeWasted(Insight):
    """ Computes the total time lost to short breaks between meetings for each day.
    
    This considers a short break to be anything less than 1 hour. This also includes
    meetings that are near the start and end of the user's working hours.
    """

    def __init__(self, name, working_hours):
        super().__init__(name, working_hours)
        self._days = {}

    def _on_event(self, event):
        start = start_time(event)
        day = start.date()

        events = self._days.get(day, [])
        events.append(event) # Defer calculation until generating data.
        self._days[day] = events

    def _calculate_day(self, day, events):
        """ Calculates the gaps for a given day. """
        start_of_day = datetime.combine(day, self._working_hours.start)
        previous_end = start_of_day
        duration = timedelta(minutes=0)

        def gap_if_wasted(start, end):
            gap = start - end
            gap_in_seconds = gap.total_seconds()
            if 0 < gap_in_seconds < 3600:
                return gap
            return timedelta(minutes=0)

        for event in events:
            start = start_time(event)
            duration = duration + gap_if_wasted(start, previous_end)
            previous_end = end_time(event)

        end_of_day = datetime.combine(day, self._working_hours.end)
        duration = duration + gap_if_wasted(end_of_day, previous_end)
        return duration

    def generate(self):
        return {day: self._calculate_day(day, events) for (day, events) in self._days.items()}


class MostFrequentAttendees(Insight):
    """ Calculates the total time spent with each person the user meets with. """

    def __init__(self, name, working_hours):
        super().__init__(name, working_hours)
        self._people = {}

    def _on_event(self, event):
        interval = time_range(event)
        duration = interval.duration()

        attendees = attendees_without_resources(event)
        for attendee in attendees:
            if not did_attendee_accept(attendee): # Ignore people that did not accept
                continue
            if attendee.get('self', False): # Ignore self
                continue
            key = attendee.get('email')
            total = self._people.get(key, timedelta(minutes=0)) + duration
            self._people[key] = total

    def generate(self):
        sorted_by_time = sorted(self._people.items(), key=lambda item: item[1], reverse=True)
        return dict(sorted_by_time)


@dataclass
class WorkingHours:
    """ Working hours for a user. """
    start: time
    end: time


class Insights:
    """ Calculates a set of insights from a user's calendar. """

    def __init__(self, working_hours):
        self._insights = [
            DailyTimeInMeetings('dailyTimeInMeetings', working_hours),
            DailyTimeInGroupMeetings('dailyTimeInGroupMeetings', working_hours),
            DailyTimeInOneOnOne('dailyTimeInOneOnOne', working_hours),
            DailyTimeInUnconfirmedMeetings('dailyTimeUnconfirmed', working_hours),
            DailyTimeWasted('dailyTimeWasted', working_hours),
            MostFrequentAttendees('totalTimePerPerson', working_hours),
        ]

    def process(self, event):
        """ Processes a calendar event.
        
        Events are expected to be processed in chronological order.
        """
        for insight in self._insights:
            insight.process(event)

    def generate(self):
        """ Generate the insight data. """
        return {insight.name:insight.generate() for insight in self._insights}
