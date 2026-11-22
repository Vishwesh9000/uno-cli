# UNO-CLI

## Description
An UNO simulator you can play directly in your CLI. Play with your friends by passing around the device, or add bots to challenge yourself.

## Getting Started
1. Clone the repository:
```
git clone https://github.com/Vishwesh9000/uno-cli
cd uno-cli 
```
2. Run the game:
```
python uno.py
```
## Features
- Special Unicode characters and ANSI color codes to make visually appealing graphical cards and a fun player experience
- Humorous bots (up to 10), letting you play by yourself
- CLI clears after every turn, dissuading peeking at others' cards
- The deck refills from the discard pile, enabling ivnfinite play

## Ruleset
My implementation of the game follows most of the Classic UNO rules, with some quirks. (Rules may change with future commits)

### Setup
- **Deck:** Standard 108-card deck
    - 4x colors (red, blue, green, and yellow)
    - 1x 0 card per color
    - 2x 1-9 cards per color
    - 2x Skip, Reverse, and +2 cards per color
    - 4x Wild +4 and Wild cards
- **Dealing:** Each person and bot gets 7 cards.
- **Starting Card:** A random numbered card is drawn to begin the discard pile (action and wild cards are returned to the deck during setup).

### Gameplay
- **Match the discard pile:** On your turn, play a card from your hand that matches the top discard card's color or value, or play a +4 or Wild card.
- **Drawing and Passing:** If you cannot or choose not to play a card, you will be forced to draw exactly once. If you still can't or don't want to play a card, you can pass, ending your turn.
- **Deck Reshuffle:** If the draw pile runs out, all buried cards from the discard pile (except the top card) are automatically reshuffled back into the deck.

### Action and Special Cards
- **Skip:** The next player loses their turn.
- **Reverse:** Reverses the direction of play. In a two player game, it functions as a Skip card.
- **Draw Two (+2):** The next player must draw two cards from the deck and forfeit their turn.
- **Wild:** The player who played this can choose the next color to be played. The next player must play a card matching that color or a +4 or Wild card.
- **Wild Draw Four (+4):** The player who played this can choose the next color to be played. The next player must draw four cards and forfeit their turn. The following player must play a card that matches the chosen color or a +4 or Wild card.

### Winning
- The first player or bot to empty their hand (0 cards remaining) wins the game.