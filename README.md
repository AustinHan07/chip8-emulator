# CHIP-8 emulator

A CHIP-8 interpreter in Python, using pygame for the window and keyboard. Two ROMs are in the repo to try it with.

## Running it

```
pip install -r requirements.txt
python chip8.py PONG
python chip8.py snake.ch8
```

Press Esc to quit.

## Controls

CHIP-8 had a 16-key hex keypad. It maps onto the left side of a normal keyboard like this:

```
CHIP-8        Keyboard
1 2 3 C       1 2 3 4
4 5 6 D       Q W E R
7 8 9 E       A S D F
A 0 B F       Z X C V
```

## How it works

Everything is in `chip8.py`. The `Chip8` class holds the 4 KB of memory, the sixteen V registers, the index register, program counter, stack, timers, and the 64x32 framebuffer. Each call to `cycle()` reads two bytes at the program counter, decodes them, and runs the matching branch of a long if/elif chain in `execute_instruction`.

`Chip8Display` wraps pygame. It scales every CHIP-8 pixel up to a 15x15 square, polls the keyboard, and redraws the screen whenever the CPU sets `draw_flag`.

The main loop runs ten CPU cycles per frame at 60 frames per second, which is a rough stand-in for the original hardware's speed. If a game feels too fast or too slow, change the 10 in `main()`.

## Known gaps

- FX0A (wait for a key press) is a stub and doesn't block.
- Timers tick every CPU cycle instead of once per frame, and the sound timer never actually makes noise.
