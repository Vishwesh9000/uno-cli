import random
from collections import deque
from collections.abc import Iterable
import copy
import time
import sys
import shutil

# special Unicode Art Chars: ─│┌┐└┘

ANSI_CLEAR_SCREEN = "\033[H\033[2J\033[3J"
ANSI_RESET = "\033[0m"
ANSI_GREY = "\033[90m"
ANSI_RED = "\033[31m"
ANSI_GREEN = "\033[32m"
ANSI_YELLOW = "\033[33m"
ANSI_BLUE = "\033[34m"

LOADING_TIME = .4

game_settings: dict = {
    "players": [
        "Player1"
    ],
    "num_bots": 1,
    "enable_unicode_graphics": True,
    "supervise_bots": False
}


card_types: list[str] = ["red", "green", "blue", "yellow", "special"]
card_vals: list[int | str] = [*range(10), "+2", "reverse", "skip", "wild", "+4"]

str_to_ansi_color: dict[str, str] = {
    "grey": ANSI_GREY,
    "red": ANSI_RED,
    "green": ANSI_GREEN,
    "yellow": ANSI_YELLOW,
    "blue": ANSI_BLUE,
    "special": ANSI_GREY # For special cards like wild and +4
}


def mock_loading(prompt: str, repeats: int, progress_time: float = LOADING_TIME):
        print(prompt, end="", flush=True)
        for _ in range(repeats):
            time.sleep(progress_time)
            print(".", end="", flush=True)
        print()
class Card:
    class Type:
        def __init__(self, color: str):
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
            match format_spec:
                case "short":
                    return self.value[0].upper()
                case "long":
                    return self.value.capitalize()
                case "":
                    return self.__str__()
                case _:
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
            match format_spec:
                case "short":
                    if len(t) > 2:
                        return t[0].upper()
                    else:
                        return t
                case "long":
                    return t.capitalize()
                case "two_char":
                    if isinstance(self.value, int):
                        return f"{self.value:02d}"
                    match self.value:
                        case "+2" | "+4": return self.value
                        case "reverse": return "RV"
                        case "skip": return "SK"
                        case "wild": return "WC"
                case "":
                    return self.__str__()
                case _:
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

class Game:
    def __init__(self, starting_card: Card):
        if starting_card.type == Card.Type("special") or starting_card.value not in [Card.Value(i) for i in range(10)]:
            raise ValueError("Invalid Starting Card")
        
        self.played_cards: deque[Card] = deque([starting_card])
        self.last_color: Card.Type = starting_card.type
        self.last_value: Card.Value = starting_card.value
        self.draw_count: int = 0
        self.dir: int = 1 # Gameplay direction (1 or -1)
        self.skip_next_player: bool = False
        self.direction_recently_reversed: bool = False # Used to turn reverse cards into skips if game only has two players
    
    def place(self, card: Card, next_color: Card.Type | None = None):
        if not self.can_place_card(card):
            raise ValueError("Invalid Card Placed")
        self.played_cards.append(card)
        self.last_color = card.type
        self.last_value = card.value

        if self.last_color == Card.Type("special"):
            if next_color is None:
                while True:
                    colors_prompt = ", ".join(
                        [f"{str_to_ansi_color[color]}{color}{ANSI_RESET}" if game_settings["enable_unicode_graphics"] else "" for color in card_types[0:-1]]
                    )
                    new_color = input(f"Pick next color ({colors_prompt}): ").strip()
                    if new_color.lower() not in card_types[0:-1]:
                        print(f"Invalid color: \"{new_color}\"")
                        print("Try again")
                    else:
                        self.last_color = Card.Type(new_color.lower())
                        break
            else:
                self.last_color = next_color

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
        while len(self.played_cards) > 1:
            buried_cards.append(self.played_cards.popleft())

        return buried_cards
    
    def print_state(self):
        
        extra_str: str = "" if self.played_cards[-1].type != Card.Type("special") \
                            else f" (Color to play: {str_to_ansi_color[self.last_color.value]}{self.last_color.value.capitalize()}{ANSI_RESET})"
        # print(f"Last Card: {self.played_cards[-1]}{extra_str}")
        print("Last Card: " + convert_card_format(self.played_cards[-1]) + " " + extra_str)

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
        self.game_pile: Game | None = None # For restocking

    def get_top_card(self):
        if len(self.cards) > 0:
            return self.cards.pop()
        else:
            print("Deck Empty")
            if self.game_pile is None:
                print("No game pile available to refill from")
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
    def __init__(self, cards: Iterable[Card] | None = None, deck: Deck | None = None, is_bot: bool = False):
        self.is_bot: bool = is_bot
        if cards:
            self.cards: list[Card] = list(cards)
        elif deck is not None:
            self.cards = []
            for _ in range(7):
                card = deck.get_top_card()
                if card is None:
                    raise RuntimeError("Ran out of cards")
                else:
                    self.cards.append(card)
        else:
            self.cards = []

    def pick_from_deck(self, deck: Deck):
        card: Card | None = deck.get_top_card()
        if card is not None:
            self.cards.append(card)
            return card
        else:
            return None

    def play_card(self, game: Game, card_index: int, next_color: Card.Type | None = None):
        game.place(self.cards[card_index], next_color=next_color)
        self.cards.pop(card_index)

    def print_state(self):
        print_string = "Cards: "
        for i, card in enumerate(self.cards):
            print_string += f"{i+1}: " + convert_card_format(card) + " "
        print(print_string)

    def play_turn(self, game: Game, deck: Deck):
            game.print_state()
            if not self.is_bot or game_settings["supervise_bots"]:
                self.print_state()
            if game.skip_next_player:
                print("Turn Skipped")
                game.skip_next_player = False
                return
            
            if game.draw_count > 0:
                print(f"Draw {game.draw_count} cards")
                while game.draw_count > 0:
                    print("Drawing Card...")
                    drawn_card: Card | None = self.pick_from_deck(deck)
                    if drawn_card is None:
                        print("Couldn't draw from deck")
                        break
                    else:
                        # print(f"You drew: {drawn_card}")
                        if not self.is_bot or game_settings["supervise_bots"]:
                            print("You drew: " + convert_card_format(drawn_card))
                    game.draw_count -= 1
                if not self.is_bot or game_settings["supervise_bots"]:
                    print("Final Cards:")
                    self.print_state()
                print("Moving to next player")
                return
    
            # Loop until complete turn
            has_drawn: bool = False
            while True:
                index = 0
                try:
                    index = -1
                    next_color: Card.Type | None = None
                    if self.is_bot:
                        for i in range(len(self.cards)):
                            if game.can_place_card(self.cards[i]):
                                index = i
                                bot_message = random.choice([
                                    "Thinking",
                                    "Analyzing probabilities",
                                    "Calculating your cards",
                                    "Peeking at your cards",
                                    "Becoming sentient",
                                    "Considering alternate universes",
                                    "Asking ChatGPT for advice",
                                    "Simulating 14,000,605 outcomes",
                                    "Consulting StackOverflow",
                                    "Bribing the random number generator",
                                    "Swapping out my cards ;)",
                                    "Injecting a virus ;)",
                                    "Training a neural network on your playstyle"
                                ])
                                mock_loading(bot_message, 3)
                                if self.cards[index].type == Card.Type("special"):
                                    card_counts: dict[str, int] = {color: 0 for color in card_types[0:-1]}
                                    for card in self.cards:
                                        if card.type.value in card_counts.keys():
                                            card_counts[card.type.value] += 1
                                    max_count = 0
                                    next_color = Card.Type("red")
                                    for key, val in card_counts.items():
                                        if val > max_count:
                                            max_count = val
                                            next_color = Card.Type(key)
                                break
                    else:
                        # index = int(input(f"What card do you want to play (0 to {'pass' if has_drawn else 'draw'})? ")) - 1
                        index = user_select_number_in_range(f"What card do you want to play (0 to {'pass' if has_drawn else 'draw'})? ", 0, len(self.cards)) - 1

                    if index == -1: # Drawing or passing
                        if has_drawn:
                            print("Passed Turn")
                            break

                        else:
                            mock_loading("Drawing", 3)
                            drawn_card: Card | None = self.pick_from_deck(deck)
                            if drawn_card is None:
                                print("Couldn't draw from deck")
                            else:
                                if not self.is_bot or game_settings["supervise_bots"]:
                                    print("You drew: " + convert_card_format(drawn_card))
                            has_drawn = True
                            if not self.is_bot or game_settings["supervise_bots"]:
                                self.print_state()
                            continue
                    # elif index < -1:
                    #     raise IndexError("Negative Index")
                    else: # Selected a card
                        if game.can_place_card(self.cards[index]):
                            print("Played " + convert_card_format(self.cards[index]))
                            self.play_card(game, index, next_color=next_color)
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
                        print(f"Selected Index out of bounds: Picked {index+1} when there's only {len(self.cards)} cards")
                    print("Repick Card:")
                    self.print_state()
                    continue
            return

def make_card_graphic(card: Card):
    if not isinstance(card, Card):
        raise ValueError("Argument is not of type Card")
    color = str_to_ansi_color[card.type.value]
    return [
        color + "┌──┐" + ANSI_RESET,
        color + f"│{card.value: two_char}│" + ANSI_RESET,
        color + "└──┘" + ANSI_RESET
    ]
class GraphicalPrintLine:
    def __init__(self, init_param: "str | Card | GraphicalPrintLine"):
        self.lines = [[""] for _ in range(3)]
        if isinstance(init_param, str):
            self.lines[0] = " " * len(init_param)
            self.lines[1] = init_param
            self.lines[2] = " " * len(init_param)

        elif isinstance(init_param, Card):
            card_graphic = make_card_graphic(init_param)
            self.lines = card_graphic

        elif isinstance(init_param, GraphicalPrintLine):
            self.lines = init_param.lines.copy()
        else:
            raise ValueError(f"Unsupported argument of type {type(init_param)}")

    def __add__(self, other: "str | Card | GraphicalPrintLine"):
        new_obj = GraphicalPrintLine(self)

        if isinstance(other, str):
            new_obj.lines[0] += " " * len(other)
            new_obj.lines[1] += other
            new_obj.lines[2] += " " * len(other)
        elif isinstance(other, Card):
            card_graphic = make_card_graphic(other)
            for i in range(len(self.lines)):
                new_obj.lines[i] += card_graphic[i]
        elif isinstance(other, GraphicalPrintLine):
            new_obj.lines = [new_obj.lines[i] + other.lines[i] for i in range(len(new_obj.lines))]
        else:
            return NotImplemented
        return new_obj
    def __radd__(self, other: str | Card):
        new_obj = GraphicalPrintLine(self)

        if isinstance(other, str):
            new_obj.lines[0] = " " * len(other) + self.lines[0]
            new_obj.lines[1] = other + self.lines[1]
            new_obj.lines[2] =  " " * len(other) + self.lines[2]
        elif isinstance(other, Card):
            card_graphic = make_card_graphic(other)
            new_obj.lines = [card_graphic[i] + new_obj.lines[i] for i in range(len(card_graphic))]
        else:
            return NotImplemented
        return new_obj
    
    def __str__(self):
        final_list = ["" for _ in range(3)]
        i0, i1, i2 = 0, 1, 2
        terminal_width = shutil.get_terminal_size(fallback=(60,24)).columns
        visible_width = 0
        in_ansi = False
        for chars in zip(*self.lines):
            if "\033" in chars:
                in_ansi = True
            at_card_start = ("\033" in chars) or (not in_ansi and ("┌" in chars or "└" in chars))
            force_newline = at_card_start and visible_width > terminal_width-10

            if "\n" in chars or force_newline:
                if final_list[-1].strip() == "" and final_list[-3].strip() == "":
                    del final_list[-3]
                    del final_list[-1]
                    i0 -= 2
                    i1 -= 2
                    i2 -= 2
                final_list.extend(["" for _ in range(3)])
                i0 += 3
                i1 += 3
                i2 += 3
                visible_width = 0

            if "\n" not in chars:
                final_list[i0] += chars[0]
                final_list[i1] += chars[1]
                final_list[i2] += chars[2]
                if not in_ansi:
                    visible_width += 1

            if in_ansi and "m" in chars:
                in_ansi = False
            

        if final_list[-1].strip() == "" and final_list[-3].strip() == "":
            del final_list[-3]
            del final_list[-1]

        final_str = ("\n" + ANSI_RESET).join(final_list)
        return final_str

def convert_card_format(card: Card):
    if not game_settings["enable_unicode_graphics"]:
        return str(card)
    else:
        return GraphicalPrintLine(card)

def user_select_number_in_range(prompt: str, min: int, max: int):
    while True:
        response = input(prompt)

        try:
            num = int(response)
        except ValueError as e:
            print(f"Couldn't understand \"{response}\". Try again")
            continue

        if num not in range(min, max+1):
            print(f"{num} not in range {min}-{max}. Try again")
            continue

        return num

def print_welcome():
    print(ANSI_CLEAR_SCREEN, end="", flush=True)
    print("Welcome To Terminal-Based UNO")
    print()
    print("Default Settings:")
    print(f"  Number of players: {len(game_settings['players'])}")
    print(f"  Number of bots: {game_settings['num_bots']}")
    print(f"  Unicode Card Graphics: {'Enabled' if game_settings['enable_unicode_graphics'] else 'Disabled'} (Disable if your terminal doesn't support UTF-8/ANSI colors and shows gibberish)")
    print(f"  (Navigate to \"Edit Settings\" to view all settings)")
    print()
    input("Press Enter to continue")

def game_menu():
    while True:
        print(ANSI_CLEAR_SCREEN, end="", flush=True)
        print("Game Menu:")
        options = [
            ["Play game", init_game],
            ["Edit Settings", edit_settings],
            ["Quit Game", quit_game]
        ]

        for i, option in enumerate(options):
            print(f"  {i+1}: {option[0]}")

        index = user_select_number_in_range("Select an option: ", 1, len(options)) - 1
        options[index][1]()
            
def edit_settings():
    global game_settings

    while True:
        print(ANSI_CLEAR_SCREEN, end="", flush=True)
        print("Edit Settings:")
        print(f"  1: Edit Players:")
        print(f"     - Number of Players: {len(game_settings['players'])}")
        print(f"     - Player Names:")
        for name in game_settings["players"]:
            print(f"        \"{name}\"")
        print()
        print(f"  2: Number of bots: {game_settings['num_bots']}")
        print(f"  3: Unicode Card Graphics: {'Enabled' if game_settings['enable_unicode_graphics'] else 'Disabled'} \t(Disable if your terminal doesn't support UTF-8/ANSI colors and shows gibberish)")
        print(f"  4: Bot Supervision: {'Enabled' if game_settings['supervise_bots'] else 'Disabled'} \t(Allows you to view the bot's cards to ensure they're not cheating)")
        
        option_num = user_select_number_in_range("Select what to edit (0 to exit): ", 0, 4)
        match option_num:
            case 0:
                return
            case 1:
                edit_player_settings()
            case 2:
                num_bots = user_select_number_in_range("How many bots would you like (0-10)? ", 0, 10)
                game_settings["num_bots"] = num_bots
            case 3:
                game_settings["enable_unicode_graphics"] = not game_settings["enable_unicode_graphics"]
                input(f"Toggled Unicode Card Graphics {'on' if game_settings['enable_unicode_graphics'] else 'off'}\n(Enter to continue)")
            case 4:
                game_settings["supervise_bots"] = not game_settings["supervise_bots"]
                input(f"Toggled Bot Supervision {'on' if game_settings['supervise_bots'] else 'off'}\n(Enter to continue)")

def edit_player_settings():
    while True:
        print(ANSI_CLEAR_SCREEN, end="", flush=True)
        print("Player names:")
        for i, name in enumerate(game_settings["players"]):
            print(f"  {i+1}: {name}")

        print()
        print("Options:")
        print("  1: Edit player name")
        print("  2: Add player")
        print("  3: Remove player")
        option_num = user_select_number_in_range("Select option (0 to exit): ", 0, 3)

        match option_num:
            case 0:
                print()
                return
            case 1:
                player_index = user_select_number_in_range("Choose player to edit (0 to exit): ", 0, len(game_settings["players"])) - 1
                if player_index == -1:
                    continue
                new_name = input(f"Rename \"{game_settings['players'][player_index]}\" to (Leave blank to cancel): ").strip()
                if not new_name:
                    continue
                game_settings['players'][player_index] = new_name
                print(f"Player renamed to \"{game_settings['players'][player_index]}\"\n")

            case 2:
                name = input("Enter player name (Leave blank to cancel): ").strip()
                if not name:
                    continue
                game_settings["players"].append(name)
                print(f"Added player \"{game_settings['players'][-1]}\"\n")
            
            case 3:
                player_index = user_select_number_in_range("Choose player to remove (0 to exit): ", 0, len(game_settings["players"])) - 1
                if player_index == -1:
                    continue
                name = game_settings["players"].pop(player_index)

                print(f"Player \"{name}\" removed\n")

def init_game():
    global deck, game, players, game_settings, player_index
    
    print(ANSI_CLEAR_SCREEN, end="", flush=True)
    
    mock_loading("Preparing game", 3)

    mock_loading("Shuffling the deck", 3)
    deck = Deck()
    deck.shuffle()

    players.clear()
    for name in game_settings["players"]:
        players.append([name, Hand(deck=deck)])

    if game_settings["num_bots"] > 0:
        mock_loading("Booting up bots", 3)
    for i in range(game_settings["num_bots"]):
        players.append([f"Bot{i+1}", Hand(deck=deck, is_bot=True)])

    player_index = 0
    mock_loading("Passing out cards", 3)

    mock_loading("Selecting starting card", 3)
    card: Card | None = deck.get_top_card()
    if card is None:
        raise RuntimeError("Can't pick starting card: Deck is empty")

    rejected_starting_cards = []
    while card.type == Card.Type("special") or card.value not in [Card.Value(i) for i in range(10)]:
        print(convert_card_format(card) + " rejected as starting card")
        time.sleep(LOADING_TIME*2)
        rejected_starting_cards.append(card)
        card = deck.get_top_card()
        if card is None:
            raise RuntimeError("No suitable starting card found")

    while len(rejected_starting_cards) > 0:
        deck.return_card_to_bottom(rejected_starting_cards.pop(0))

    print("Starting card: " + convert_card_format(card) + "\n")
    time.sleep(LOADING_TIME*2)

    mock_loading("Starting game", 3)
    game = Game(card)
    deck.game_pile = game

    
    print()
    game_loop()

def game_loop():
    global deck, game, players, player_index
    while True:
        if player_index == -1:
            player_index = len(players)-1
        elif player_index == len(players):
            player_index = 0

        player = players[player_index]
        print(f"{player[0]}'s turn")
        if not player[1].is_bot:
            input("Start Turn? (Enter to continue)")

        player[1].play_turn(game, deck)

        input("\nEnd Turn? (Enter to continue)")
        print(ANSI_CLEAR_SCREEN, end="", flush=True)
        if game.direction_recently_reversed:
            if len(players) == 2:
                game.skip_next_player = True
            game.direction_recently_reversed = False

        if len(player[1].cards) == 0:
            print(f"{player[0]} wins!!!!!!")
            input("(Enter to continue)")
            break
    
        player_index += game.dir

def quit_game():
    print("\nThanks for playing!")
    sys.exit()


deck: Deck = Deck()

# Initialize game with a dummy starter card
game: Game = Game(Card(Card.Type("red"), Card.Value(0)))

players: list[list[str | Hand]] = []

player_index = 0


if __name__ == "__main__":
    try:
        print_welcome()
        game_menu()
    except KeyboardInterrupt:
        quit_game()



# TODO: Add game help/rules panel
# TODO: Implement logs so players can see what other have done despite secrecy
# TODO: Implement assisted playing: computer will determine playable cards, show them to the player, and auto move if there is only one choice

