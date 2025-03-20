from location import *
from board import *
from move import *
import itertools

ALL_TILES = [True] * 7
ALPHABET = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']


class ScrabbleBot:

    def __init__(self):
        self._gatekeeper = None
        self._board = None
        self._bag = list(
            'aaaaaaaaabbccddddeeeeeeeeeeeeffggghhiiiiiiiiijkllllmmnnnnnnooooooooppqrrrrrrssssttttttuuuuvvwwxyyz__')
        self._moves = []
        self._words = []
        self._blanks = ['-', '=', '+', '#', ' ']
        self._player_numbers = -1

    def __str__(self):
        return "Scrabble Bot Mk. 3"

    def set_gatekeeper(self, gatekeeper):
        self._gatekeeper = gatekeeper

    def _deal(self, hand, n):
        """
        Deals n tiles from the bag into hand.
        """
        for i in range(n):
            if not self._bag:  # Bag is empty!
                return
            hand.append(self._bag.pop())

    @staticmethod
    def can_be_drawn_from_hand(word, hand):
        """
        Returns true if word can be played from the tiles available in hand.
        """
        used = [False] * len(hand)
        for letter in word:
            if letter == ' ':
                continue
            found = False
            for i, tile in enumerate(hand):
                if (not used[i]) and ((letter == tile) or (letter.isupper() and tile == '_')):
                    used[i] = True
                    found = True
                    break
            if not found:
                return False
        return True

    def can_be_placed_on_board(self, word, location, direction):
        """
        Returns true if word can be placed on board, in the sence of not overlapping existing tiles, leaving no gaps,
        having no tiles right before or after it, and not extending beyond the edge of the board.
        """
        before = location - direction
        if before.is_on_board() and self.is_occupied(before):
            return False  # Tile right before word starts
        for letter in word:
            if not location.is_on_board():
                return False  # Off edge of board
            current = self.get_square(location)
            if (letter == ' ') != current.isalpha():
                return False  # Tile played on top of existing tile, or gap in word where there is no tile
            location += direction
        if location.is_on_board() and self.is_occupied(location):
            return False  # Tile right after word ends
        return True

    def get_square(self, location):
        return self._board[location.c + (location.r * 15)]

    def is_occupied(self, location):
        return self.get_square(location).isalpha()

    def _set_square(self, tile, location):
        self._board[location.c + (location.r * 15)] = tile

    def place_word(self, word, location, direction):
        for letter in word:
            if letter != ' ':
                self._set_square(letter, location)
            location += direction

    def would_be_connected(self, word, location, direction):
        """
        Returns True if word, placed at location in direction, would be connected. In other words, word must contain
        an existing tile, be beside an existing tile, or contain the center.
        """
        cross = direction.orthogonal()
        for letter in word:
            if letter == '':
                return True  # Contains a played tile
            if location == CENTER:
                return True  # Contains center
            for neighbor in location + cross, location - cross:
                if neighbor.is_on_board() and self.is_occupied(neighbor):
                    return True  # Letter next to word on one side
            location += direction
        return False

    def is_valid_word(self, word, location, direction):
        """
        Returns true if word, played at location in direction, forms a valid dictionary word of at least two letters.
        """
        if len(word) < 2:
            return False
        letters = ''
        for letter in word:
            if self.is_occupied(location):
                letters += self.get_square(location)
            else:
                letters += letter
            location += direction
        return letters.lower() in DICTIONARY

    def is_valid_cross_word(self, tile, location, direction):
        """
        Returns true if the cross word including location forms a valid dictionary word, or no new cross word is formed.
        """
        if tile == ' ':
            return True  # Word was already on board
        location = self.find_start_of_word(location, direction)
        word = ''
        tile_used = False
        while location.is_on_board():
            if self.is_occupied(location):
                word += self.get_square(location)
            elif tile_used:
                break  # Reached end of cross word
            else:
                word += tile
                tile_used = True
            location += direction
        if len(word) == 1:
            return True  # No cross word here
        return word.lower() in DICTIONARY

    def would_create_only_legal_words(self, word, location, direction):
        """
        Returns true if word, played at location in direction, would create only legal words.
        """
        if not self.is_valid_word(word, location, direction):
            return False
        cross = direction.orthogonal()
        for letter in word:
            if not self.is_valid_cross_word(letter, location, cross):
                return False
            location += direction
        return True

    def find_start_of_word(self, location, direction):
        """
        Returns the location of the first tile in a (cross) word that includes location and moves in direction.
        """
        while True:
            location -= direction
            if not (location.is_on_board() and self.is_occupied(location)):
                return location + direction

    def score_cross_word(self, tile, location, direction):
        """
        Returns the score for the cross word in direction including (but not necessarily starting with) tile played
        at location.
        """
        score = 0
        multiplier = 1
        location = self.find_start_of_word(location, direction)
        if (location + direction).is_on_board() and not self.is_occupied(location + direction):
            return 0  # One letter "cross word"
        tile_used = False
        while location.is_on_board():
            square = self.get_square(location)
            if self.is_occupied(location):
                score += TILE_VALUES[square]
            elif tile_used:
                break  # End of cross word
            else:
                score += TILE_VALUES[tile]
                bonus = self.get_square(location)
                if bonus == DOUBLE_LETTER_SCORE:
                    score += TILE_VALUES[tile]
                elif bonus == TRIPLE_LETTER_SCORE:
                    score += 2 * TILE_VALUES[tile]
                elif bonus == DOUBLE_WORD_SCORE:
                    multiplier *= 2
                elif bonus == TRIPLE_LETTER_SCORE:
                    multiplier *= 3
                tile_used = True
            location += direction
        return score * multiplier

    def score_word(self, word, location, direction):
        """
        Returns the points score for word, played at location in direction.
        """
        score = 0
        multiplier = 1
        for tile in word:
            square = self.get_square(location)
            if tile == ' ':
                score += TILE_VALUES[square]
            else:
                score += TILE_VALUES[tile]
                if square == DOUBLE_LETTER_SCORE:
                    score += TILE_VALUES[tile]
                elif square == TRIPLE_LETTER_SCORE:
                    score += 2 * TILE_VALUES[tile]
                elif square == DOUBLE_WORD_SCORE:
                    multiplier *= 2
                elif square == TRIPLE_WORD_SCORE:
                    multiplier *= 3
            location += direction
        return score * multiplier

    def score(self, word, location, direction):
        """
        Returns the score for playing word at location in direction, including any cross words.
        """
        score = self.score_word(word, location, direction)
        tiles_played = 0
        for tile in word:
            if tile != ' ':
                score += self.score_cross_word(tile, location, direction.orthogonal())
                tiles_played += 1
            location += direction
        if tiles_played == 7:
            score += 50
        return score

    def verify_legality(self, word, location, direction, hand):
        """
        Throws a ValueError if playing word at location in direction from hand would not be legal.
        """
        if len(word) < 2:
            raise ValueError('Word must be at least two letters long.')
        if all(tile == ' ' for tile in word):
            raise ValueError('Word must contain at least one new tile.')
        if not self.can_be_drawn_from_hand(word, hand):
            raise ValueError('Hand does not contains sufficient tiles to play word.')
        if not (self.can_be_placed_on_board(word, location, direction) and
                self.would_be_connected(word, location, direction)):
            raise ValueError('Board placement incorrect (gaps, overlapping tiles, edge of board).')
        if not self.would_create_only_legal_words(word, location, direction):
            raise ValueError('Invalid word created.')

    @staticmethod
    def remove_tiles(word, hand):
        """
        Removes the tiles used in word from and and returns them in a new str.
        """
        result = ''
        for tile in word:
            if 'A' <= tile <= 'Z':
                tile = '_'
            if tile != ' ':
                hand.remove(tile)
                result += tile
        return result

    def exchange(self, hand, tiles_to_exchange):
        """
        Exchanges 0 or more tiles from hand with the bag. Also toggles the current player and resolves the end of the
        game if applicable.
        :param tiles_to_exchange: An array of seven bools indicating which tiles to exchange. Any entries beyond the
        length of hand are ignored.
        """
        removed = [tile for i, tile in enumerate(hand) if tiles_to_exchange[i]]
        dumped = self.remove_tiles(removed, hand)
        self._deal(hand, 7 - len(hand))
        # Return dumped letters to bag
        for tile in dumped:
            self._bag.append(tile)
        random.shuffle(self._bag)
        # If there weren't enough tiles in bag, some dumped tiles may return to hand
        self._deal(hand, 7 - len(hand))

    def _disconnected_move(self, location, direction):
        usable = ''
        for char in self._gatekeeper.get_hand():
            usable += char
            # Get playable words
        playable = self._get_all_words(usable)
        # Create blanks
        for word in playable:
            result = self._contains_letters(word, usable)
            if result is not True:
                temp = word.replace(result, result.upper(), 1)
                playable.remove(word)
                playable.append(temp)
        for word in playable:
            try:
                self._gatekeeper.verify_legality(word, location, direction)
                self._moves.append([self._gatekeeper.score(word, location, direction), word, location, direction])
            except:
                pass
        return

    def _build_playable_word(self, word, s):
        if len(s) == 1 and s[0][0] in word:
            return word.replace(s[0][0], ' ', 1)
        i = 0
        while i != -1:
            i = word.find(s[0][0], i)
            start_i = i
            if i == -1:
                break
            k = i
            for j in range(1, len(s)):
                k += s[j][1]
                if k >= len(word):
                    i += 1
                    break
                if word[k] != s[j][0]:  # Won't fit with placed tiles
                    i += 1
                    break
            if i == start_i:
                w = ''
                k = i
                j = 1
                for index in range(len(word)):
                    if index == k:
                        w += ' '
                        if j < len(s):
                            k += s[j][1]
                            j += 1
                return w
        return None

    def _contains_letters_with_blanks(self, word, letters):
        hand = letters
        for char in word:
            if char not in hand:
                if '_' in hand:
                    hand = hand.replace('_', '', 1)
                else:
                    return False
            else:
                hand = hand.replace(char, '', 1)
        return True

    def _contains_letters(self, word, letters):
        hand = letters
        for char in word:
            if char not in hand:
                return char
            hand = hand.replace(char, '', 1)
        return True

    def _get_all_words(self, letters):
        return [word for word in DICTIONARY if self._contains_letters_with_blanks(word, letters)]

    def _vertical_check(self, hand):
        # Check vertical words
        direction = VERTICAL
        for col in range(15):
            placed = []
            last = 0
            for row in range(15):
                square = Location(row, col)
                if self.is_occupied(square):
                    placed.append([self.get_square(square), row - last])
                    last = row
            usable = ''
            for char in hand:
                usable += char
            for letter in placed:
                usable += letter[0]
            # Get combinations of placed letters
            combos = []
            for i in range(len(placed)):
                for j in range(i+1, len(placed)+1):
                    combos.append(placed[i:j])
            # Get playable words
            playable = self._get_all_words(usable)
            # Create blanks
            for word in playable:
                result = self._contains_letters(word, usable)
                if result is not True:
                    temp = word.replace(result, result.upper(), 1)
                    playable.remove(word)
                    playable.append(temp)
            for word in playable:
                attempt = []
                #  Check if word can be placed using board tiles
                for s in combos:
                    w = self._build_playable_word(word, s)
                    if w is not None and w not in attempt:
                        attempt.append(w)
                #  Check if word can be placed using only our hand
                h = str(hand)
                for letter in word:
                    if letter in h:
                        h.replace(letter, '', 1)
                if len(h) == 7 - len(word) and word not in attempt:
                    attempt.append(word)
                #  Try to place words
                for row in range(15):
                    location = Location(row, col)
                    for w in attempt:
                        try:
                            self._gatekeeper.verify_legality(w, location, direction)
                            self._moves.append(
                                [self._gatekeeper.score(w, location, direction), w, location, direction])
                        except:
                            pass

    def _horizontal_check(self, hand):
        # Check vertical words
        direction = HORIZONTAL
        for row in range(15):
            placed = []
            last = 0
            for col in range(15):
                square = Location(row, col)
                if self.is_occupied(square):
                    placed.append([self.get_square(square), col - last])
                    last = col
            usable = ''
            for char in hand:
                usable += char
            for letter in placed:
                usable += letter[0]
            # Get combinations of placed letters
            combos = []
            for i in range(len(placed)):
                for j in range(i+1, len(placed)+1):
                    combos.append(placed[i:j])
            # Get playable words
            playable = self._get_all_words(usable)
            # Create blanks
            for word in playable:
                result = self._contains_letters(word, usable)
                if result is not True:
                    temp = word.replace(result, result.upper(), 1)
                    playable.remove(word)
                    playable.append(temp)
            # Try to place words
            for word in playable:
                attempt = []
                #  Check if word can be placed using board tiles
                for s in combos:
                    w = self._build_playable_word(word, s)
                    if w is not None and w not in attempt:
                        attempt.append(w)
                #  Check if word can be placed using only our hand
                h = str(hand)
                for letter in word:
                    if letter in h:
                        h.replace(letter, '', 1)
                if len(h) == 7 - len(word) and word not in attempt:
                    attempt.append(word)
                #  Try to place words
                for col in range(15):
                    location = Location(row, col)
                    for w in attempt:
                        try:
                            self._gatekeeper.verify_legality(w, location, direction)
                            self._moves.append(
                                [self._gatekeeper.score(w, location, direction), w, location, direction])
                        except:
                            pass

    def _find_exchange_word(self, exchange):
        moves = []
        if not len(exchange):
            return None
        for option in exchange:
            hand = self._gatekeeper.get_hand()
            ex_hand = ''
            for i in range(len(hand)):
                if option[0][i]:
                    ex_hand += hand[i]
            moves = self._moves.copy()
            self._moves = []
            self._vertical_check(ex_hand)
            self._horizontal_check(ex_hand)
            for _ in range(len(self._moves)):
                j = -1
                for letter in ex_hand:
                    if letter not in self._moves[0][1]:
                        j += 1
                if j > 0:
                    self._moves.pop(0)
            for move in self._moves:
                if move not in moves:
                    moves.append(move)
            self._moves = moves
        if len(self._moves):
            self._moves = sorted(self._moves, key=lambda x: x[0], reverse=True)
            return self._moves[0]
        if len(moves):
            self._moves = moves
        return None

    def _best_exchange(self):
        # Possible exchange permutations
        options = list(itertools.product([True, False], repeat=7))
        options = [list(row) for row in options]

        # Set up bag
        self._bag = list(
            'aaaaaaaaabbccddddeeeeeeeeeeeeffggghhiiiiiiiiijkllllmmnnnnnnooooooooppqrrrrrrssssttttttuuuuvvwwxyyz__')
        for square in self._board:
            if square not in self._blanks:
                if 'A' <= square <= 'Z':
                    self._bag.remove('_')
                else:
                    self._bag.remove(square)
        temp_bag = self._bag.copy()

        # Number of simulations
        monty_carlo = 10
        best = []
        for option in options:
            avg_words = 0
            for i in range(monty_carlo):
                self._bag = temp_bag.copy()
                random.shuffle(self._bag)
                hand = self._gatekeeper.get_hand()
                self.exchange(hand, option)
                hand = ''.join(hand)
                avg_words += len(self._get_all_words(str(hand)))
            avg_words /= monty_carlo
            best.append([option, avg_words])
        best = sorted(best, key=lambda x: x[1])
        return best[:5]

    def _check_pass_win(self):
        if not isinstance(self._gatekeeper.get_last_move(), ExchangeTiles):
            return False
        hand_value = 0
        for tile in self._gatekeeper.get_hand():
            hand_value += TILE_VALUES[tile]
        difference = (self._gatekeeper.get_my_score() - hand_value) - (self._gatekeeper.get_opponent_score() - self._gatekeeper.get_opponent_hand_size())
        if difference > 0:
            return True
        return False

    def choose_move(self):
        self._moves = []
        self._board = list(str(self._gatekeeper).replace('\n', ''))
        if self._check_pass_win():
            return ExchangeTiles([False] * 7)
        if self._gatekeeper.get_square(CENTER) == DOUBLE_WORD_SCORE:
            self._disconnected_move(CENTER, HORIZONTAL)
        else:
            self._vertical_check(self._gatekeeper.get_hand())
            self._horizontal_check(self._gatekeeper.get_hand())
        self._moves = sorted(self._moves, key=lambda x: x[0], reverse=True)
        if len(self._moves):
            temp = self._moves.copy()
            if self._moves[0][0] < 11:
                exchange = self._best_exchange()
                word = self._find_exchange_word(exchange)
                if word is not None:
                    return PlayWord(word[1], word[2], word[3])
            self._moves = temp
            return PlayWord(self._moves[0][1], self._moves[0][2], self._moves[0][3])
        exchange = self._best_exchange()
        if len(exchange):
            return ExchangeTiles(exchange[0][0])
        return ExchangeTiles(ALL_TILES)
