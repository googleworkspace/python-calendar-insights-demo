# Calendar Insights Demo

This is a small python demo that calculates insights using the
Google Calendar API.

Note: This is not an official Google product. 

## Usage

Requires an access token authorized with any of the following scopes:

    https://www.googleapis.com/auth/calendar.events.readonly
    https://www.googleapis.com/auth/calendar.events
    https://www.googleapis.com/auth/calendar.readonly
    https://www.googleapis.com/auth/calendar

Use the the [OAuth Playground](https://developers.google.com/oauthplayground)
or [gcloud CLI](https://cloud.google.com/sdk/gcloud/reference/auth/application-default)
to obtain an access token.

Usage:

    python main.py <access_token>

Adjust the working hours and timezone in main.py as needed.
