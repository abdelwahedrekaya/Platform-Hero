# Platform Hero

A complete, original side-scrolling platformer built with Python + pygame —
run, jump, stomp enemies, collect coins, and reach the flag.

> Note: this is an original game inspired by the classic run‑and‑jump
> platformer genre. It doesn't use Nintendo's Mario characters, names, or
> artwork (those are copyrighted) — everything here, including the
> character and enemy designs, is drawn from scratch with simple shapes.

## Setup

1. Make sure you have **Python 3.8+** installed.
2. Install pygame:
   ```
   pip install pygame
   ```
3. Run the game:
   ```
   python platform_hero.py
   ```

## Controls

| Key                | Action              |
|---------------------|---------------------|
| ← / →  or  A / D    | Move left / right   |
| Space / ↑ / W       | Jump                |
| P                    | Pause / unpause     |
| Enter                | Start (from menu)   |
| R                    | Restart (after win/game over) |
| Esc                  | Quit                |

## How it works

- **Stomp** enemies by landing on top of them for +100 points. Hitting one
  from the side costs you a life.
- Collect **coins** for +50 points each.
- You have **3 lives** and **300 seconds** per life — reach the flag before
  time runs out.
- Falling into a pit costs a life; you'll respawn at the last checkpoint
  (start of each ground section) rather than all the way back at the
  beginning.
- Reaching the **flag** wins the level and adds a time bonus to your score.

## Notes on this build

The level (platforms, coin placement, enemy patrol routes, checkpoints) is
generated from data rather than a hand-typed map, which keeps the geometry
consistent. All visuals are drawn procedurally with pygame's shape functions
— no external image or sound files are required, so there's nothing that
can go missing when you run it.

Before delivery, the game's logic (physics, collision resolution, stomp/hit
detection, checkpoints, win/lose state transitions, pausing, and level
boundaries) was exercised with an automated test harness across thousands
of simulated frames to confirm it runs cleanly. If you hit anything odd on
your machine, it's most likely pygame/display related rather than game
logic.
