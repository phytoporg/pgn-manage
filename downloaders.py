from codecs import open
from datetime import date
from datetime import datetime
import os
import requests
import sys
import time

import lichess.api
from lichess.format import JSON

CHESSCOM_URL_TEMPLATE = 'https://api.chess.com/{}'
LICHESS_URL_TEMPLATE  = 'https://lichess.org/api/{}'

# chess.com

# Helper functions
def _get(uri):
    r = requests.get(uri)
    return r.json() if r.status_code == 200 else None

# Download driver
class ChessComPGNDownloader:
    def __init__(self, user, where):
        self.user = user
        self.where = where

    def get_where(self):
        return self.where

    # Actually perform the download
    def do_download(self):
        uri = CHESSCOM_URL_TEMPLATE.format(f'pub/player/{self.user}/games/archives')
        archives_result = _get(uri)
        if not archives_result:
            print(f'Failed to retrieve archives from {uri}', file=sys.stderr)
            return False

        for archive_uri in archives_result['archives']:
            archive = _get(archive_uri)
            if not archive:
                print(f'Failed to retrieve games from {archive_uri}', file=sys.stderr)
                return False

            games = archive['games']
            d = date.fromtimestamp(games[0]['end_time'])
            year, month = d.year, d.month

            filename = os.path.join(self.where, f'{year}-{month:02}.pgn')
            print(f'Downloading {filename}...')

            try:
                with open(filename, 'w', encoding='utf-8') as fw:
                    for game in games:
                        if 'pgn' not in game:
                            print("skipping game", game['rules'])
                            continue
                        print(game['pgn'], file=fw)
                        print('', file=fw)
            except Exception as e:
                print(e, file=sys.stderr)
                return False

        return True
        
# lichess.org

# Helper functions

# lichess.api.user_games doesn't support all of the parameters supported by the actual API,
# and won't let us filter by begin/end times, so we'll do it ourselves
def _lichess_get_api_text(url_template, endpoint, params):
    get_path = url_template.format(endpoint)

    params_string = '&'.join([f'{k}={v}' for k, v in params.items()])
    full_request_url = f'{get_path}?{params_string}' if params_string else get_path

    r = requests.get(full_request_url)
    if r.status_code != 200:
        print(f'GET failed for {full_request_url}', file=sys.stderr)
        return None
    else:
        return r.text

def _lichess_download_all_from_month(year, month, user, where):
    # Start at the previous month
    if month == 1:
        year -= 1
        month = 12
    else:
        month -= 1

    today = datetime.today()
    while datetime(year=year, month=month, day=1) <= today:
        print(f'Downloading games for {year}-{month:02}...')
        _lichess_download_pgn_for_month(year, month, user, where)

        if month == 12:
            year += 1
            month = 1
        else:
            month += 1

def _lichess_download_pgn_for_month(year, month, user, where):
    start_dt = datetime(year=year, month=month, day=1)
    start_time_ms = int(time.mktime(start_dt.timetuple()) * 1000)

    if month == 12:
        end_dt = datetime(year=year+1, month=1, day=1)
    else:
        end_dt = datetime(year=year, month=month+1, day=1)

    end_time_ms = int(time.mktime(end_dt.timetuple()) * 1000)
    params = { 'since' : start_time_ms, 'until' : end_time_ms }
    pgn_text = _lichess_get_api_text(LICHESS_URL_TEMPLATE, f'games/user/{user}', params)

    if pgn_text:
        target_pgn_filepath = os.path.join(where, f'{year}-{month:02}.pgn')
        with open(target_pgn_filepath, 'w') as f:
            f.write(pgn_text)

def _lichess_get_yearmonth_from_games(user):
    # Try and get all of the games. Hopefully this user doesn't have too many
    # games on record!
    games = lichess.api.user_games(user, format=JSON)
    games_list = list(games)

    if len(games_list) < 1:
        return None

    earliest_game = min(games_list, key=lambda x: x['createdAt'])
    earliest_dt = datetime.fromtimestamp(earliest_game['createdAt'] / 1000)

    return (earliest_dt.year, earliest_dt.month)

def _lichess_get_yearmonth_from_dir(user, where):
    # Assuming we store PGNs in this path in the format: YYYY-MM.pgn
    pgns_in_path = sorted([pgn for pgn in os.listdir(where) if pgn.endswith('.pgn')])

    # Nothin' found
    if len(pgns_in_path) < 1:
        return None

    # We're assuming here that this is all being updated at least once a month.
    # Here's hoping I don't lose interest in chess anytime soon :P

    newest_pgn = pgns_in_path[-1]
    newest_pgn_date = newest_pgn[:-4]
    year, month = (int(x) for x in newest_pgn_date.split('-'))

    return (year, month)

# Download driver
class LichessPGNDownloader:
    def __init__(self, user, where):
        self.user = user
        self.where = where

    def get_where(self):
        return self.where

    # Actually perform the download
    def do_download(self):
        # Default to the month before the last stored PGN file
        yearmonth_tuple = _lichess_get_yearmonth_from_dir(self.user, self.where)
        if not yearmonth_tuple:
            # Download as many games as possible
            yearmonth_tuple = _lichess_get_yearmonth_from_games(self.user)

            if not yearmonth_tuple:
                print(f'Failed to retrieve games for {self.user}', file=sys.stderr)
                return False

        print(f"Downloading {self.user}'s lichess games to {self.where}:")
        # Update all games since and including the latest month for which
        # there is already data.
        year, month = yearmonth_tuple
        _lichess_download_all_from_month(year, month, self.user, self.where)

        return True
