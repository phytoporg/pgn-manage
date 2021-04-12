# pgn-manage
Some basic python tools to fetch and manage PGNs from various chess platforms. Currently supports only chess.com and lichess.org. Optimized for my personal workflow, but maybe someone else will find it useful.

## Usage

There's only the `download` command for the moment, which will download all PGN files for a user across one or all supported chess platforms.
```
Usage: pgn_manage.py download [OPTIONS]

Options:
  --user TEXT                     [required]
  --source [all|chesscom|lichess]
  --output PATH
  --help                          Show this message and exit.
```

- `user` refers to the username on a given platform. If no argument is specified, `pgn_manage` will pull this value from the `CHESS_USERNAME` environment variable if it is defined.
- `source` is the target chess platform, or `all` to pull games from all supported platforms
- `output` refers to the path to which PGN files will be downloaded. You may also set the `CHESS_PGN_DIR` environment variable. The specified path must already exist.

Example output directory structure from `python pgn_manage.py download --user philjo5000 --source all`

```
.
|   all_merged.pgn
|
+---chesscom
|       2021-03.pgn
|       2021-04.pgn
|
\---lichess
        2020-12.pgn
        2021-01.pgn
        2021-03.pgn
        2021-04.pgn
```

All individual PGN files capture games from a particular month, and `all_merged.pgn` is a consolidated file containing each games from all platforms.
