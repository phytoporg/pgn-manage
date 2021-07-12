import os
import sys
from game_details import *

def _err(filename, line, msg, do_raise = False):
    error_string = f"{filename}:{line}: {msg}"
    if do_raise:
        raise ValueError(error_string)
    else:
        print(error_string, file=sys.stderr)

def _parse_tag_line(line, line_number):
    # PGN metadata tags are formatted as:
    # [Key "Value"]
    #
    # The spec allows for multiple tags per line, or compound values
    # delimited by colons. Supported platforms don't appear to do
    # this though, so we'll simplify the implementation and just
    # assert where our assumptions break.
    close_bracket_location = line.find(']')
    if close_bracket_location < 1:
        _err(self.pgn_file, line_number, 'Expected closing bracket', do_raise=True)

    if line.find('[', close_bracket_location) > 0:
        # Valid per the PGN spec, but not supported.
        _err(self.pgn_file, line_number, 'Found multiple tags per line.', do_raise=True)

    # Check quotes for the tag value                            
    opening_quote_location = line.find('"')
    closing_quote_location = line.rfind('"') 

    if (opening_quote_location < 0) or \
       (closing_quote_location <= opening_quote_location) or \
       (closing_quote_location >= close_bracket_location):
        _err(self.pgn_file, line_number, 'Malformed tag value quotes', do_raise=True)
                                
    # Okay, we should be all set
    key = line[1:opening_quote_location].strip()
    value = line[(opening_quote_location + 1):closing_quote_location]

    return key, value

class PGNParser:
    def __init__(self, pgn_file):
        # Do some basic sanity checks
        if not os.path.exists(pgn_file):
            raise FileExistsError(f'Could not find path: {pgn_file}')

        if not pgn_file.endswith('.pgn'):
            raise ValueError(f'Expected pgn extension for file {pgn_file}')

        self.pgn_file = pgn_file

    def get_games(self, include_partial_games=False):    
        # Yield at each line containing move information.
        with open(self.pgn_file, 'r') as fr:
            metadata = {}

            # Search for tags
            line_number = 0
            for line in fr:
                line = line.strip()
                if not line:
                    continue

                if line[0] == '[':
                    key, value = _parse_tag_line(line, line_number)
                    if key in metadata:
                        _err(self.pgn_file, line_number, 'Duplicate tag. Overwriting previous value.')

                    metadata[key] = value
                else:
                    # Does the line start with a move number?
                    success = True
                    period_location = line.find('.')
                    if period_location:
                        try:
                            starting_move = int(line[:period_location])
                        except ValueError:
                            success = False

                    if not success:                            
                        _err(self.pgn_file, line_number, 'Unexpected start of line', do_raise=True)

                    if starting_move == 1 or include_partial_games:
                        # Assuming moves exist on one single line for each game.
                        yield GameDetails(metadata, line)
                    else:
                        _err(self.pgn_file, line_number, 'Skipping partial game.')

                    # Clear out the state after parsing a game
                    metadata = {}

                line_number += 1
