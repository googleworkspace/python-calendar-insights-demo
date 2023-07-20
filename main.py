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

"""
Sample for generating insights from a user's primary calendar. Requires
an access token authorized with any of the following scopes:

    https://www.googleapis.com/auth/calendar.events.readonly
    https://www.googleapis.com/auth/calendar.events
    https://www.googleapis.com/auth/calendar.readonly
    https://www.googleapis.com/auth/calendar

Use the the OAuth Playground (https://developers.google.com/oauthplayground)
or gcloud CLI (https://cloud.google.com/sdk/gcloud/reference/auth/application-default)
to obtain an access token.

Usage:

    python main.py <access_token>

Adjust the working hours and timezone
"""

from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo

import sys
import google.oauth2.credentials

from googleapiclient.discovery import build
from insights import Insights, WorkingHours
from report import print_report


# Adjust as necessary
TIME_ZONE = 'America/Denver'
START_OF_DAY = 9 # 24 hour clock
END_OF_DAY = 18 # 24 hour clock

tz = ZoneInfo(TIME_ZONE)
working_hours = WorkingHours(
    time(hour=START_OF_DAY, tzinfo=tz),
    time(hour=END_OF_DAY, tzinfo=tz),
    tz
)

insights = Insights(working_hours)

# Create the credentials & API client
credentials = google.oauth2.credentials.Credentials(sys.argv[1])
service = build('calendar', 'v3', credentials=credentials)

# Limit the calendar search to current week
now = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
start = now - timedelta(days=now.weekday())
end = start + timedelta(days=7)

next_page_token = None
while True:
    # Fetch events
    results = service.events().list(calendarId='primary', # pylint: disable=no-member
                                    pageToken=next_page_token,
                                    timeMin=start.isoformat() + 'Z',
                                    timeMax=end.isoformat() + 'Z',
                                    maxResults=1000,
                                    singleEvents=True,
                                    orderBy='startTime').execute()
    events = results.get('items', [])

    for event in events:
        insights.process(event)

    next_page_token = results.get('nextPageToken', None)
    if next_page_token is None:
        break

# Generate and print the insights
data = insights.generate()
print_report(data)
