
import random
import copy

VALUE_OF_PICURE_CARD = 5  # How is a picture card valued?
GAIN_ALWAYS_ACCEPTED = 2  # The gain you always accept
TAKE_THE_RISK_TO_SWAP_UNKNOWN = 4  # If the open card is less then this, you take the chance to swap unknown
CALL_BEVER = 8  # At how many points do we call BeverBende
ASSUMED_VALUE_OF_UNKNOWN_CARD = 6  # How much points do you give an unknown card?

VERBOSE = True


class Card:

    def __init__(self, card_type):
        self.card_type = card_type
        self.visible = False

    def set_visible(self, value):
        self.visible = value

    def get_value(self):
        if self.is_number_card():
            return self.card_type
        else:
            return VALUE_OF_PICURE_CARD

    def is_number_card(self):
        return self.card_type not in ('look', 'switch', 'double')


class Deck:

    def __init__(self, empty=False):

        self.deck = []

        freq = [(4, 0), (4, 1), (4, 2), (4, 3), (4, 4), (4, 5), (4, 6), (4, 7),
                (4, 8), (9, 9), (7, 'look'), (9, 'switch'), (5, 'double')]

        if empty is False:
            for f, c in freq:
                for i in range(0, f):
                    self.deck.append(Card(c))

            self.shuffle_deck()

    def get_card_from_deck(self):

        if len(self.deck) > 0:
            c = self.deck[0]
            self.deck.pop(0)
            return c
        else:
            return None

    def add_card_to_deck(self, c):

        self.deck.append(c)

    def shuffle_deck(self):

        nrcards = len(self.deck)
        for i in range(0, 2 * nrcards):
            c = random.choice(self.deck)
            self.deck.remove(c)
            self.deck.append(c)


class Player:

    def __init__(self, nr_players, pn, c0, c1, c2, c3):

        self.cards = [[0] * 4 for i in range(nr_players)]

        for i in range(0, nr_players):
            for j in range(0, 4):
                self.cards[i][j] = Card(-1)
                self.cards[i][j].visible = False

        self.cards[pn][0] = c0
        self.cards[pn][1] = c1
        self.cards[pn][2] = c2
        self.cards[pn][3] = c3

        self.cards[pn][0].visible = True
        self.cards[pn][3].visible = True


class Game:

    def __init__(self, nr_players):

        # Create the closed deck and the open deck
        self.closed_deck = Deck(empty=False)
        self.open_deck = Deck(empty=True)
        self.globally_known = []
        self.bever_called = False
        self.bever_called_by = -1
        self.nr_players = nr_players

        self.open_card = self.closed_deck.get_card_from_deck()
        self.open_deck.add_card_to_deck(self.open_card)

        # Create the number of players and hand them the cards
        # Note that in this stage you do not have to test if get_card_from_deck() returns a Card

        self.players = []
        for i in range(0, nr_players):
            p = Player(nr_players, i, self.closed_deck.get_card_from_deck(), self.closed_deck.get_card_from_deck(),
                       self.closed_deck.get_card_from_deck(), self.closed_deck.get_card_from_deck())
            self.players.append(p)

    def swap_card(self):
        pass

    def print_player(self, pn):

        print('')
        for i in range(0, 4):
            str1 = '%-10s' % self.players[pn].cards[pn][i].card_type
            print(f'Player {pn}, position {i}: card is: {str1}, '
                  f'known: {self.players[pn].cards[pn][i].visible}')
        print(f'\nOpen card is {self.open_card.card_type}')
        print('')

    def player_move(self, pn):

        # First check if the first card that has been turned is worth swapping.
        # Note this is only relevant if it is a number card

        if self.review_open_card(pn, visible_to_all=True):
            return

        # Draw a card from the closed_deck, add it to the open_deck and analyse again
        self.get_card_from_closed_desk()

        if VERBOSE:
            print(f'New card drawn is {self.open_card.card_type}')

        nr_of_moves_left = 1
        while nr_of_moves_left > 0:
            if self.open_card.is_number_card():
                self.review_open_card(pn, visible_to_all=False)
                nr_of_moves_left = 0
            elif self.open_card.card_type == 'look':
                # Open one of the cards that was not yet visible
                for i in range(0, 4):
                    if self.players[pn].cards[pn][i].visible is False:
                        self.players[pn].cards[pn][i].visible = True
                        break
                nr_of_moves_left = 0

                count = 0
                for i in range(0, 4):
                    if self.players[pn].cards[pn][i].visible:
                        count += self.players[pn].cards[pn][i].get_value()
                    else:
                        count += ASSUMED_VALUE_OF_UNKNOWN_CARD
                if count < CALL_BEVER:
                    self.bever_called = True
                    print("Call Bever!!!!!!!!")

            elif self.open_card.card_type == 'double':
                self.get_card_from_closed_desk()
                nr_of_moves_left = 2
                pass
            elif self.open_card.card_type == 'switch':
                nr_of_moves_left = 0
                self.find_best_switch_pair(pn)
                pass  # implement the switch
            else:
                pass
        return self.bever_called

    def review_open_card(self, pn, visible_to_all):

        index = 0
        max_gain = 0
        swapped = False
        save_open_card = self.open_card

        # Only do this when it is a number card

        if not self.open_card.is_number_card():
            return False

        # If it is a number card, check if it makes sense to swap it for one of the known cards
        # Return True if you did actually swap

        # First check how much gain you can make in the visible cards

        for i in range(0, 4):
            if self.players[pn].cards[pn][i].visible is True:
                gain = self.players[pn].cards[pn][i].get_value() - self.open_card.get_value()
                if gain > max_gain:
                    max_gain = gain
                    index = i

        # If the gain is considerable than just take it
        if max_gain > GAIN_ALWAYS_ACCEPTED:
            card = self.players[pn].cards[pn][index]
            self.players[pn].cards[pn][index] = self.open_card
            self.players[pn].cards[pn][index].visible = True
            if visible_to_all:
                for i in range(0, self.nr_players):
                    self.set_card_visibility(i, pn, index, self.open_card)
            self.open_card = card
            self.open_deck.get_card_from_deck()
            self.open_deck.add_card_to_deck(card)
            swapped = True
            print (f'Player swapped card - 1')

        elif self.open_card.card_type < TAKE_THE_RISK_TO_SWAP_UNKNOWN:
            # Else, if the open card is sufficiently low, we take the risk of swapping out an unknown
            for i in range(0, 4):
                if self.players[pn].cards[pn][i].visible is False:
                    card = self.players[pn].cards[pn][i]
                    self.players[pn].cards[pn][i] = self.open_card
                    self.players[pn].cards[pn][i].visible = True
                    self.open_card = card
                    self.open_deck.add_card_to_deck(card)

                    swapped = True
                    print (f'Player swapped card - 2')

                    break
        else:
            # No use swapping
            swapped = False

        if swapped and visible_to_all:
            print(f'Player {pn} took the open card {save_open_card.card_type}, and put it visibly on position {index} ')

        if swapped:
            count = 0
            for i in range(0, 4):
                if self.players[pn].cards[pn][i].visible:
                    count += self.players[pn].cards[pn][i].get_value()
                else:
                    count += ASSUMED_VALUE_OF_UNKNOWN_CARD
            if count < CALL_BEVER:
                self.bever_called = True
                print("Call Bever!!!!!!!!")

        return swapped

    def get_card_from_closed_desk(self):

        # If there are cards left on closed deck, get one and add it to open deck
        # If the close deck is empty shuffle the open deck and make that the closed deck
        #
        # In any case after the function returns, there is a new open card

        if len(self.closed_deck.deck) != 0:
            self.open_card = self.closed_deck.get_card_from_deck()
            self.open_deck.add_card_to_deck(self.open_card)
        else:
            print('New deck New deck New deck New deck New deck New deck New deck New deck New deck New deck')
            self.open_deck.shuffle_deck()
            self.closed_deck = copy.deepcopy(self.open_deck)
            self.open_deck = Deck(empty=True)
            self.open_card = self.closed_deck.get_card_from_deck()
            self.open_deck.add_card_to_deck(self.open_card)

    def evaluate_player(self, pn):
        score = 0
        for i in range(0, 4):
            if self.players[pn].cards[pn][i].is_number_card():
                score += self.players[pn].cards[pn][i].card_type
            else:
                found = False
                while not found:
                    self.get_card_from_closed_desk()
                    if self.open_card.is_number_card():
                        score += self.open_card.card_type
                        found = True

        return score

    def find_best_switch_pair(self, pn):

        # First find the card that you'd like to loose

        max_score = -1
        max_index = -1
        max_card = None

        min_score = 10
        min_index = -1
        min_player = -1
        min_card = None

        # What cards are visible to player pn?
        visible_list = self.get_card_visibility(pn)

        # Determine the best own visible card to switch
        for vplayer, vpos, vcard in visible_list:
            if vplayer == pn:
                if vcard.get_value() > max_score:
                    max_score = vcard.get_value()
                    max_index = vpos
                    max_card = vcard
            else:
                if vcard.get_value() < min_score:
                    min_score = vcard.get_value()
                    min_index = vpos
                    min_player = vplayer
                    min_card = vcard

        # There is always a best own card to change out
        # But it is not guaranteed that there is a card visible from other players

        print('_' * 80)
        print(f'I would change out my card {max_score} on {max_index} with card {min_score} on position {min_index} of player {min_player}')
        print('_' * 80)

        if min_player != -1:
            for i in range(0, self.nr_players):
                self.update_visible_cards(i, pn, max_index, max_card, min_player, min_index, min_card)
            self.print_visible(pn)
        else:
            pass

    def set_card_visibility(self, pn, player, index, card):
        self.players[pn].cards[player][index] = card
        self.players[pn].cards[player][index].visible = True

    def get_card_visibility(self, pn):

        visible_set = []
        for p in range(0, self.nr_players):
            for i in range(0, 4):
                if self.players[pn].cards[p][i].visible:
                    visible_set.append((p, i, self.players[pn].cards[p][i]))
        return visible_set

    def update_visible_cards(self, pn, player1, index1, card1, player2, index2, card2):
        self.players[pn].cards[player1][index1] = card2
        self.players[pn].cards[player2][index2] = card1

    def print_visible(self, pn):
        for i in range(0, self.nr_players):
            str1 = ''
            for j in range(4):
                if self.players[pn].cards[i][j].visible:
                    str1 += '%-3s' % self.players[pn].cards[i][j].card_type
                else:
                    str1 += '-  '
            print(str1)


def main():
    # Set up the game for the first to start

    nr_players = 3
    winding_down_count = nr_players
    cg = Game(nr_players)

    # Ready for the first player.....
    for i in range(1, 1000):
        for pn in range(0, nr_players):
            if winding_down_count > 0:
                print('_' * 80)
                print(f'\nRound {i} - Player {pn}')
                cg.print_player(pn)
                cg.player_move(pn)
                if cg.bever_called:
                    if cg.bever_called_by == -1:
                        cg.bever_called_by = pn
                    winding_down_count -= 1
                cg.print_player(pn)

    print('\nGame ended')

    min_score = 1000
    min_pn = -1
    for pn in range(0, nr_players):
        score = cg.evaluate_player(pn)
        if score < min_score:
            min_score = score
            min_pn = pn
    print(f'Player {min_pn} wins with {min_score} points')


if __name__ == '__main__':
    main()
