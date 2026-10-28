# Terminal Texas Hold'em

[简体中文](docs/readme-zh.md) · [Player guide](docs/user-guide.md) · [Project index](docs/index.md)

A local No-Limit Texas Hold'em game for one human and up to nine built-in computer opponents. Play a hand in your terminal, review it immediately, and use the history and training tools to study your decisions. Choose Chinese or English when the game starts.

## Computer opponents

The built-in AI has six playing-style profiles. They shape its tendencies rather than guaranteeing a particular move:

| Style | Typical tendency |
| --- | --- |
| Balanced | Mixes selective calls, raises, and folds. |
| Loose-aggressive | Enters more pots and raises more often. |
| Calling station | Prefers calling and stays in hands longer. |
| Tight-aggressive | Plays fewer hands, then bets more assertively. |
| Maniac | Plays many hands with frequent raises and bluffs. |
| Nit | Waits for stronger hands and folds more readily. |

Each new game randomly selects distinct opponent names and independently pairs them with these styles. A name does not imply that the corresponding product powers the opponent. Names and styles stay fixed during that game.

## Run locally

You need Python 3.12 or a compatible Python 3 version and a UTF-8 terminal. Playing does not require third-party Python packages, an account, or a network connection.

```bash
git clone https://github.com/JarvixGaby/terminal-texas-holdem.git
cd terminal-texas-holdem
./scripts/start.sh
```

You can also run `python3 main.py` from the project directory. Choose `1` for Chinese or `2` for English, then select **New game**. Set your name, 1–9 opponents, blinds, and starting stack. The total table size is 2–10 players.

## At the table

| Command | Action |
| --- | --- |
| `check` | Pass when no bet is due. |
| `call` | Match the amount owed. |
| `bet` or `raise` | Bet or raise; enter the amount when prompted. |
| `fold` | Give up the hand. |
| `status` | Show the full table state. |
| `help` | Show decision advice. |

Chinese commands also work in English mode. Confirmation prompts accept `y`, `n`, and `back`, along with their Chinese equivalents. After each hand you can open an immediate replay. The main menu also provides hand history, quick replay, a training center, and player-style review. Advice and equity figures are practice estimates.

## Development and evidence

The application entry point is `main.py`. Game flow lives in `texas_holdem/engine/`, built-in AI in `texas_holdem/ai/`, terminal rendering in `texas_holdem/ui/`, and evaluation tools in `texas_holdem/analytics/`. See the [project index](docs/index.md) for the full map.

The latest [10-seed × 500-hand AI benchmark](docs/reports/2026-10-26-calling-station-astra-medium-equity-check.md) passed its existing completion and legality gate. Opponent-style calibration is still in progress; the [calling-station opportunity diagnostic](docs/reports/2026-10-26-calling-station-opportunity-diagnostic.md) explains its remaining call-rate warning. These reports use faster equity sampling than normal terminal play unless stated otherwise.

To run the automated suite, install `pytest` in your development environment and run:

```bash
python3 -m pytest -q
```

Hand history, player statistics, the SQLite database, and logs stay in the project directory and are excluded from Git.
