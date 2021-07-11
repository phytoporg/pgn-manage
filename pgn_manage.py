import click
import os
import sys

from downloaders import *

PGN_SOURCES = ['chesscom', 'lichess']

# Factory helper function for downloader classes.
def _create_downloader(source, user, output):
    pgn_download_path = os.path.join(output, source)

    if not os.path.exists(pgn_download_path):
        print(f"Path not found: {pgn_download_path}. Creating.")
        os.makedirs(pgn_download_path)

    if source == 'chesscom':
        return ChessComPGNDownloader(user, pgn_download_path)
    elif source == 'lichess':
        return LichessPGNDownloader(user, pgn_download_path)

# Merge all PGNs in a list of directories (non-recursive) into a single PGN file.
def _merge_pgns(dirs_to_merge, merged_output_filepath):
    dir_to_pgnfiles = { d : [f for f in os.listdir(d) if f.endswith('.pgn')] for d in dirs_to_merge }

    with open(merged_output_filepath, 'w+', encoding='utf-8') as fw:
        for d in dir_to_pgnfiles:
            for f in dir_to_pgnfiles[d]:
                pgn_filepath = os.path.join(d, f)

                print(f'Merging {pgn_filepath} into {merged_output_filepath}...', end='')
                with open(pgn_filepath, 'r') as fr:
                    fw.write(fr.read())
                print(' done!')

    return True

# Download PGNs from various sources and merge them into one singular PGN file.
def _download_and_merge(downloaders, merged_output_filepath):
    dirs_to_merge = []
    for downloader in downloaders:
        download_directory = downloader.get_where()
        if not downloader.do_download():
            print(f'Failed to download to {download_directory}')
            continue

        dirs_to_merge.append(download_directory)

    return _merge_pgns(dirs_to_merge, merged_output_filepath)

@click.group()
def cli():
    pass

# I use the same username for all of my chess accounts, so there's just one param
# with one environment variable. No support for mix-and-match using the 'all' 
# option for the moment.
@cli.command()
@click.option('user', '--user', envvar='CHESS_USERNAME', type=str, required=True)
@click.option('source', '--source', type=click.Choice(['all', 'chesscom', 'lichess'], case_sensitive=False), default='all')
@click.option('output', '--output', envvar='CHESS_PGN_DIR', type=click.Path())
def download(user, source, output):
    source = source.lower()

    if source == 'all':
        downloaders = [ _create_downloader(s, user, output) for s in PGN_SOURCES]
    else:
        downloaders = [ _create_downloader(source, user, output) ]

    # No merge is done for a single source, but let's keep the language generic
    merged_output_filepath = os.path.join(output, f'{source}_merged.pgn')
    if not _download_and_merge(downloaders, merged_output_filepath):
        print(f'Failed to download and merge from source: {source}', file=sys.stderr)

if __name__ == '__main__':
    cli()
