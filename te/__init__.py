from .__info__ import VERSION

import click
import configparser
import os
import pendulum
import re
import requests
import sys


@click.command()
@click.argument('date')
@click.argument('time')
@click.argument('duration')
@click.argument('description', nargs=-1, required=True)
@click.version_option(version=VERSION)
def main(date, time, duration, description):

    config = configparser.ConfigParser()
    config.read(os.path.expanduser('~/.te.ini'))

    try:
        timezone = config.get('general', 'timezone')
        api_token = config.get('general', 'api_token')
    except (configparser.NoSectionError, configparser.NoOptionError) as err:
        click.echo('Invalid configuration file', err=True)
        click.echo(err, err=True)
        sys.exit(1)

    if date == '-':
        now = pendulum.now(timezone)
        date = '{:04d}-{:02d}-{:02d}'.format(now.year, now.month, now.day)

    m1 = re.match(r'^(20)?(\d{2})[-]?(\d{2})[-]?(\d{2})$', date)
    if m1 is None:
        click.echo('Invalid DATE entered', err=True)
        click.echo('Correct format is "YYYY-MM-DD" or "YYMMDD"', err=True)
        click.echo('If you use "-", it means today', err=True)
        sys.exit(1)

    m2 = re.match(r'^(\d{2})[:]?(\d{2})$', time)
    if m2 is None:
        click.echo('Invalid TIME entered', err=True)
        click.echo('Correct format is "HH:MM" or "HHMM"', err=True)
        sys.exit(1)

    m3 = re.match(r'^(\d+)([mh])$', duration)
    if m3 is None:
        click.echo('Invalid DURATION entered', err=True)
        sys.exit(1)

    try:
        dt = pendulum.datetime(year=2000 + int(m1.group(2)),
                               month=int(m1.group(3)),
                               day=int(m1.group(4)),
                               hour=int(m2.group(1)),
                               minute=int(m2.group(2)),
                               tz=timezone)
    except ValueError:
        click.echo('Invalid DATE or TIME value provided', err=True)
        sys.exit(1)

    auth = requests.auth.HTTPBasicAuth(api_token, 'api_token')
    data = {
        'time_entry': {
            'start': dt.in_timezone(pendulum.UTC).to_iso8601_string(),
            'duration': int(m3.group(1)) * 60 *
            (1 if m3.group(2) == 'm' else 60),
            'description': ' '.join(description),
            'created_with': 'te'
        }
    }

    r = requests.post(url='https://www.toggl.com/api/v8/time_entries',
                      auth=auth, json=data)
    if r.status_code != 200:
        click.echo('API request failed', err=True)
        sys.exit(1)
