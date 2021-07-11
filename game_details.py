from datetime import datetime, timezone

# Encapsulates game information. Initialized all at once, immutable.
class GameDetails:
    def __init__(self, metadata, game_contents):
        self.metadata = metadata
        self.game_contents = game_contents

    def get_tags(self):
        return (key for key in self.metadata.keys())

    def get_tag(self, tag_name):
        return self.metadata[tag_name] if tag_name in self.metadata else None

    def get_game_contents(self):
        return self.game_contents

    def get_pgn_string(self):
        builder_string = ''

        if len(self.metadata) > 0:
            builder_string += '\n'.join((f'[{key} "{value}"]' for key, value in self.metadata.items()))
            builder_string += '\n\n'

        builder_string += self.game_contents

        return builder_string

    def get_datetime(self):
        # Generally trying to keep the metadata tags opaque, but this is an
        # exception since the games are ultimately sorted by date played. Also
        # assuming no concurrent/overlapping games and that all games were played
        # serially by one person. We can't all be crushing chess scrubs in
        # blindfolded simuls or whatever.

        time_key = 'UTCTime'
        date_key = 'UTCDate'

        if time_key not in self.metadata:
            raise ValueError(f'Expected {time_key} in tags')

        if date_key not in self.metadata:
            raise ValueError(f'Expected {date_key} in tags')

        time_string = self.metadata[time_key]
        hh, mm, ss = (int(token) for token in time_string.split(':'))

        date_string = self.metadata[date_key]
        yyyy, mm, dd = (int(token) for token in date_string.split('.'))

        return \
            datetime(
                year=yyyy,
                month=mm,
                day=dd,
                hour=hh,
                minute=mm,
                second=ss,
                tzinfo=timezone.utc)
