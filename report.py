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

""" Simple pretty-printing of generated insights. """

import humanize

def print_daily_totals(data):
    # Print insights in the form of date -> timedelta
    for (day, minutes) in data.items():
        date = humanize.naturaldate(day)
        total_time = humanize.precisedelta(minutes, minimum_unit='minutes')
        print(f"{date}: {total_time}")

def print_labeled_totals(data):
    # Print insights in the form of string -> timedelta
    for (label, minutes) in data.items():
        total_time = humanize.precisedelta(minutes, minimum_unit='minutes')
        print(f"{label}: {total_time}")

def print_report(data):
    """ Pretty-print known generated insights """
    print("Time per day in all meetings:")
    print_daily_totals(data.get('dailyTimeInMeetings', {}))
    print("\n")

    print("Time per day in 1-on-1 meetings:")
    print_daily_totals(data.get('dailyTimeInOneOnOne', {}))
    print("\n")

    print("Time per day in group meetings:")
    print_daily_totals(data.get('dailyTimeInGroupMeetings', {}))
    print("\n")

    print("Time per day lost to < 1 hour gaps between meetings:")
    print_daily_totals(data.get('dailyTimeWasted', {}))
    print("\n")

    print("Total time with people:")
    print_labeled_totals(data.get('totalTimePerPerson', {}))
