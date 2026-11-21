import random
from collections import deque
from collections.abc import Iterable
import copy

card_types: list[str] = ["red", "green", "blue", "yellow", "special"]
card_vals: list[int | str] = [*range(10), "+2", "reverse", "skip", "wild", "+4"]

class Card:
    class Type:
        def __init__(self, color: str | int):
            color = color.lower()
            if color not in card_types:
                raise ValueError(f"Unexpected value: {color}")
            self.value = color

        def __eq__(self, other: object):
            if not isinstance(other, Card.Type): return NotImplemented
            elif self.value != other.value: return False
            else: return True

        def __str__(self):
            return self.value.capitalize()

        def __repr__(self):
            return f"Card.Type({self.value})"

        def __format__(self, format_spec: str):
            format_spec = format_spec.strip()
            if format_spec == "short":
                return self.value[0].upper()
            elif format_spec == "long":
                return self.value.capitalize()
            elif format_spec == "":
                return self.__str__()
            else:
                raise ValueError(f"Unknown format specifier: \"{format_spec}\"")

    class Value:
        def __init__(self, value: str | int):
            if isinstance(value, str):
                value = value.lower()
            if value not in card_vals:
                raise ValueError(f"Unexpected value: {value}")
            self.value: str | int = value
        def __eq__(self, other: object):
            if not isinstance(other, Card.Value): return NotImplemented
            elif self.value != other.value: return False
            else: return True

        def __str__(self):
            return str(self.value).capitalize()

        def __repr__(self):
            return f"Card.Value({self.value})"

        def __format__(self, format_spec: str):
            format_spec = format_spec.strip()
            t: str = str(self.value)
            if format_spec == "short":
                if len(t) > 2:
                    return t[0].upper()
                else:
                    return t
            elif format_spec == "long":
                return t.capitalize()
            elif format_spec == "":
                return self.__str__()
            else:
                raise ValueError(f"Unknown format specifier: \"{format_spec}\"")

    def __init__(self, color: Type, value: Value):
        self.type: Card.Type = color
        self.value: Card.Value = value

    def __eq__(self, other: object):
        if not isinstance(other, Card):
            return NotImplemented
        elif self.value != other.value or self.type != other.type: return False
        else: return True

    def __str__(self):
        return f"{self.type} {self.value}"

    def __repr__(self):
        return f"Card({self.type}, {self.value})"
    
    def __format__(self, format_spec: str):
        return f"{self.type:{format_spec}} {self.value:{format_spec}}"

class GamePile:
    def __init__(self, starting_card: Card):
        if starting_card.type == Card.Type("special") or starting_card.value not in [Card.Value(i) for i in range(10)]:
            raise ValueError("Invalid Starting Card")
        
        self.cards: deque[Card] = deque([starting_card])
        self.last_color: Card.Type = starting_card.type
        self.last_value: Card.Value = starting_card.value
        self.draw_count: int = 0
        self.dir: int = 1 # Gameplay direction (1 or -1)
        self.skip_next_player: bool = False
        self.direction_recently_reversed: bool = False # Used to turn reverse cards into skips if game only has two players
    
    def place(self, card: Card):
        if not self.can_place_card(card):
            raise ValueError("Invalid Card Placed")
        self.cards.append(card)
        self.last_color = card.type
        self.last_value = card.value

        if self.last_color == Card.Type("special"):
            while True:
                new_color = input(f"Pick next color ({", ".join(card_types[0:-1])}): ").strip()
                if new_color.lower() not in card_types[0:-1]:
                    print("Invalid color")
                else:
                    self.last_color = Card.Type(new_color.lower())
                    break

        match card.value.value:
            case "+2":
                self.draw_count = 2
            case "+4":
                self.draw_count = 4
            case "reverse":
                self.dir *= -1
                self.direction_recently_reversed = True
            case "skip":
                self.skip_next_player = True
            
    def can_place_card(self, card: Card):
        if card.type == Card.Type("special"):
            return True
        
        if self.last_color == card.type:
            return True
        if self.last_value == card.value:
            return True
        return False

    def pop_buried_cards(self):
        buried_cards = []
        while len(self.cards) > 1:
            buried_cards.append(self.cards.popleft())

        return buried_cards
    
    def print_state(self):
        extra_str: str = "" if self.cards[-1].type != Card.Type("special") else f" (Color to play: {self.last_color.value.capitalize()})"
        print(f"Last Card: {self.cards[-1]}{extra_str}")

class Deck:
    def __init__(self):
        # 108 cards
        # 1 '0' per color
        # 2 '1-9'|'skip'|'reverse'|'+2' per color
        # 4 'wild'|'+4' cards
        self.full_card_set: deque[Card] = deque()
        for color in [Card.Type(type) for type in card_types if type != "special"]:
            # 1 '0' per color
            self.full_card_set.append(Card(color, Card.Value(0)))

            for value in [Card.Value(value) for value in card_vals if value not in [0, "wild", "+4"]]:
                # 2 of every other card thats not 0/wild/+4 per color
                self.full_card_set.append(Card(color, value))
                self.full_card_set.append(Card(color, value))

        for _ in range(4):
            # 4 of each special card
            self.full_card_set.append(Card(Card.Type("special"), Card.Value("wild")))
            self.full_card_set.append(Card(Card.Type("special"), Card.Value("+4")))

        self.cards: deque[Card] = copy.deepcopy(self.full_card_set)
        self.game_pile: GamePile | None = None # For restocking

    def get_top_card(self):
        if len(self.cards) > 0:
            return self.cards.pop()
        else:
            print("Deck Empty")
            if self.game_pile is None:
                print("No GamePile available to refill from")
                return None
            else:
                new_cards = self.game_pile.pop_buried_cards()
                self.cards.extend(new_cards)
                self.shuffle()
                if len(self.cards) == 0:
                    print("Failed to restock deck: game pile empty")
                    return None
                else:
                    print("Restocked deck from game pile")
                    return self.cards.pop()

    def return_card_to_bottom(self, card: Card):
        self.cards.appendleft(card)

    def shuffle(self):
        random.shuffle(self.cards)


class Hand:
    def __init__(self, cards: Iterable[Card] | None = None):
        if cards:
            self.cards: list[Card] = list(cards)
        else:
            self.cards: list[Card] = []

    def pick_from_deck(self, deck: Deck):
        card: Card | None = deck.get_top_card()
        if card is not None:
            self.cards.append(card)
            return card
        else:
            print("Couldn't pick card")
            return None

    def play_card(self, game: GamePile, card_index: int):
        game.place(self.cards[card_index])
        self.cards.pop(card_index)

    def print_state(self):
        print("Cards: " + ", ".join([f"{i+1}: {card}" for i, card in enumerate(self.cards)]))

    def play_turn(self, game: GamePile, deck: Deck):
            game.print_state()
            self.print_state()
            if game.skip_next_player:
                print("Turn Skipped")
                game.skip_next_player = False
                return
            
            if game.draw_count > 0:
                print(f"You have to draw {game.draw_count} cards")
                while game.draw_count > 0:
                    print("Drawing Card...")
                    drawn_card: Card | None = self.pick_from_deck(deck)
                    if drawn_card is None:
                        print("Couldn't draw from deck")
                        break
                    else:
                        print(f"You drew: {drawn_card}")
                    game.draw_count -= 1
                print("Final Cards:")
                self.print_state()
                print("Moving to next person")
                return
    
            # Loop until complete turn
            has_drawn: bool = False
            while True:
                index = 0
                try:
                    index = int(input(f"What card do you want to play (0 to {"pass" if has_drawn else "draw"})? ")) - 1

                    if index == -1: # Drawing or passing
                        if has_drawn:
                            print("Passing...")
                            print("Moving to next player")
                            break

                        else:
                            print("Drawing...")
                            draw_successful: bool = self.pick_from_deck(deck)
                            if not draw_successful:
                                print("Couldn't draw from deck")
                            has_drawn = True
                            # TODO: print drawn card
                            self.print_state()
                            continue
                    elif index < -1:
                        raise IndexError("Negative Index")
                    else: # Selected a card
                        if game.can_place_card(self.cards[index]):
                            self.play_card(game, index)
                            break

                        else:
                            raise ValueError("Can't place this card")

                except ValueError as e:
                    print(e)
                    print("Pick another card:")
                    self.print_state()
                    continue
                except IndexError as e:
                    if index < -1:
                        print(f"Can't input \"{index+1}\": Negative Index")
                    else:
                        print(f"Selected Index out of bounds: Picked {index} when there's only {len(self.cards)} cards")
                    print("Repick Card:")
                    self.print_state()
                    continue
        
            return

    

        




deck: Deck = Deck()
# print([f"[{card.type: short},{card.value: short}]" for card in deck.cards])
deck.shuffle()

card: Card | None = deck.get_top_card()
if card is None:
    raise RuntimeError("Can't pick starting card: Deck is empty")

rejected_starting_cards = []
while card.type == Card.Type("special") or card.value not in [Card.Value(i) for i in range(10)]:
    print(f"{card} rejected as starting card")
    rejected_starting_cards.append(card)
    card = deck.get_top_card()
    if card is None:
        raise RuntimeError("No suitable starting card found")

while len(rejected_starting_cards) > 0:
    deck.return_card_to_bottom(rejected_starting_cards.pop(0))

print(f"Starting card: {card}")

game: GamePile = GamePile(card)
deck.game_pile = game

players: list[list[str | Hand]] = [[f"Player{i+1}", Hand([deck.cards.pop() for _ in range(7)])] for i in range(2)]


player_index = 0
player_direction = 1

# Circle between players
while True:
    if player_index == -1:
        player_index = len(players)-1
    elif player_index == len(players):
        player_index = 0


    player = players[player_index]
    print("\n")
    print(f"{player[0]}'s turn")
    
    player[1].play_turn(game, deck)

    if game.direction_recently_reversed:
        if len(players) == 2:
            game.skip_next_player = True
        game.direction_recently_reversed = False

    
    if len(player[1].cards) == 0:
        print(f"{player[0]} wins")
        break

    player_index += game.dir



    
        


# TODO: Implement secrecy (Players can't see others cards via terminal clearing and waiting for player consent before displaying card info)
# TODO: Game Menu
#           Select number of players
#           Custom player names
#           Select number of bots
# TODO: Better card visualization (e.g. ascii art + colored text vs "red 5")
# TODO: Bots

