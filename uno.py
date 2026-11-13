import random
from collections import deque
from collections.abc import Iterable
import copy

card_types: str = ["red", "green", "blue", "yellow", "special"]
card_vals: int | str = [*range(10), "+2", "reverse", "skip", "wild", "+4"]

class Card:
    class Type:
        def __init__(self, color: str | int):
            color = color.lower()
            if color not in card_types:
                raise ValueError("Unexpected argument to Color constructor")
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
                raise ValueError("Unexpected value in Card.Value.__init__()")
            self.value: str | int = value
        def __eq__(self, other: object):
            if not isinstance(other, Card.Value): return NotImplemented
            elif self.value != other.value: return False
            else: return True

        def __str__(self):
            return str(self.value).capitalize()

        def __repr(self):
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

    def __eq___(self, other: object):
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

    def get_top_card(self):
        return self.cards.pop()

    def return_card(self, card: Card):
        self.cards.appendleft(card)

    def shuffle(self):
        random.shuffle(self.cards)

class GamePile:
    def __init__(self, starting_card: Card):
        if starting_card.type == Card.Type("special") or starting_card.value not in [Card.Value(i) for i in range(10)]:
            raise ValueError("Invalid Starting Card")
        
        self.cards: deque[Card] = deque([starting_card])
        self.last_color: Card.Type = starting_card.type
        self.last_value: Card.Value = starting_card.value
    
    def place(self, card: Card):
        if not self.can_place_card(card):
            raise ValueError("Invalid Card Placed")
        self.cards.append(card)
        self.last_color = card.type
        self.last_value = card.value

    def can_place_card(self, card: Card):
        if card.type == Card.Type("special"):
            return True
        
        if self.last_color == card.type:
            return True
        if self.last_value == card.value:
            return True
        return False

        
        

class Hand:
    def __init__(self, cards: Iterable[Card] | None = None):
        if cards:
            self.cards: list[Card] = list(cards)
        else:
            self.cards: list[Card] = []

    def pick_from_deck(self, deck: Deck):
        self.cards.append(deck.get_top_card())

    def play_card(self, game: GamePile, card_index: int):
        game.place(self.cards.pop(card_index))




deck: Deck = Deck()
# print([f"[{card.type: short},{card.value: short}]" for card in deck.cards])
deck.shuffle()

card: Card = deck.get_top_card()
while card.type == Card.Type("special") or card.value not in [Card.Value(i) for i in range(10)]:
    print(f"{card} rejected as starting card")
    deck.return_card(card)
    card = deck.get_top_card()

print(f"Starting card: {card}")



deck.shuffle()
