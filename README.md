# Texas Hold'em Terminal Game

[简体中文说明](docs/readme-zh.md)

A local No-Limit Texas Hold'em practice game. Play against one to five computer opponents with different styles, then review your hands and training feedback. The app runs in a terminal and asks you to choose English or Chinese each time it starts.

## Requirements and start

- Python 3.12 or a compatible Python 3 version
- A terminal that supports UTF-8
- No third-party packages are required to play

From the project directory:

```bash
./scripts/start.sh
```

The script also works when called by its path from another directory. Alternatively, run `python3 main.py` from the project directory. At the first prompt, enter `2` for English or `1` for Chinese.

## Play

Choose **New game** from the main menu. Enter a player name, select one to five computer opponents, and choose the blinds and starting stack. The computer opponents use distinct playing styles.

On your turn, use these commands:

| Command | Action |
| --- | --- |
| `check` | Pass when no bet is due. |
| `call` | Match the current bet. |
| `bet` or `raise` | Put chips in or increase the bet; follow the amount prompt. |
| `fold` | Give up the current hand. |
| `status` | Show the table state. |
| `help` | Show decision advice. |

Chinese action commands also work in English mode. Confirmation prompts accept `y`, `n`, and `back` as well as their Chinese equivalents.

The main menu also offers hand history, quick replay, a local training center, game instructions, and a player style review. Decision advice and equity figures are estimates for practice, not guarantees of the best move.

## Local data

Hand history, player statistics, the SQLite database, and logs are stored in the local project directory. These runtime files are excluded by `.gitignore`. Playing does not require an account or a network connection.

## Development

Run the test suite from the project directory:

```bash
python3 -m pytest -q
```

The entry point is `main.py`. Terminal translations are in `localization.py`; game flow is in `game.py`; history and replay are in `game_history.py` and `quick_replay_system.py`. See the [project index](docs/index.md) for the file map and the [Chinese user guide](docs/user-guide.md) for more detailed play instructions.
