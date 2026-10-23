"""
Usage:
    python move.py right 2          # 2 longpresses of DPAD_RIGHT
    python move.py right 5 jump 2 2 left
    python move.py loop right 5 jump 2 10 # (repeat "5 right, 2 jump + 1 jump" 10 times )
"""
import subprocess
import sys

"""
Notes:
- For now loop keyword is expected to be first word after move.py, and last character is loop count, later I'll add more flexible parsing.
"""

"""
To add:
- Detection for angel/merchant screen and selecting appropriate option.
- Draw projectories of enemy bullets (first assume bullets only go straight), find a path to avoid projectories.
- Detection for level up screen (for choosing perks, which can be avoided by turning on auto perks).
"""

ADB = ["adb", "-s", "2053449"]

KEY_UP    = 19
KEY_DOWN  = 20
KEY_LEFT  = 21
KEY_RIGHT = 22
KEY_JUMP = 62

ALL_COMMANDS_SET = {"right", "left", "up", "down", "jump", "loop"}

""" NOTE: Unfortunately, in input keyevent, --duration and --longpress cannot be used at the same time. 
Thus, we can't just make a key hold for specific duration. We instead use longpress, which has about 0.5s duration.
"""
DEFAULT_N = 1 # default number of longpresses if not specified (for arrow keys; up down left right)
DEFAULT_JUMP_DURATION = 1 # default jump duration if not specified (1 for short jump, 2 for long jump)


def get_direction_key(dx, dy):
    """Return the keycode for the direction (dx, dy). Here dx, dy are -1, 0, or 1 for left/right and up/down."""
    if dx > 0: return KEY_RIGHT
    if dx < 0: return KEY_LEFT
    if dy > 0: return KEY_DOWN
    if dy < 0: return KEY_UP
    return None

def move(dx, dy, n=DEFAULT_N):
    """Send `n` longpresses of the direction key in one adb call."""
    key = get_direction_key(dx, dy)
    if not key or n <= 0:
        return
    # repeat the keycode n times, e.g. for diag: 22 22 22 20 20 20
    codes = " ".join(str(key) for _ in range(n))
    subprocess.run(
        ADB + ["shell", "input", "keyevent", "--longpress", *codes.split()],
        check=True,
    )

def right(n=DEFAULT_N): move( 1,  0, n)
def left (n=DEFAULT_N): move(-1,  0, n)
def up   (n=DEFAULT_N): move( 0, -1, n)
def down (n=DEFAULT_N): move( 0,  1, n)


def jump(duration=DEFAULT_JUMP_DURATION):
    """Send a jump key event. 1 for short jump, 2 for long jump."""
    if duration == 1:
        subprocess.run(ADB + ["shell", "input", "keyevent", str(KEY_JUMP)], check=True)
    elif duration == 2:
        subprocess.run(ADB + ["shell", "input", "keyevent", "--longpress", str(KEY_JUMP)], check=True)


def parse_cmd(tokens):
    """Group cmd into list of [key_word, *args] chunks."""
    commands, current = [], None
    for token in tokens:
        if token in ALL_COMMANDS_SET:
            if current:
                commands.append(current) # finish the previous command and start a new one
            current = [token] # start a new command with the current token
        elif current is not None:
            current.append(token) # should be an argument for the current command
    if current:
        commands.append(current) # add the last command if it exists
    return commands


if __name__ == "__main__":
    if len(sys.argv) >= 2:
        tokens = sys.argv[1:]

        # special-case: loop (...) N  ->  loop_tokens, repeat_count
        repeat = 1
        if tokens[0] == "loop":
            print(tokens)
            repeat = int(tokens[-1])
            tokens = tokens[1:-1]
            print(tokens)

        parsed_cmds = parse_cmd(tokens)
        print(f"Parsed commands: {parsed_cmds}")

        for counter in range(repeat):
            print(f"Executing loop: {counter + 1}")
            for cmd in parsed_cmds:
                name, *args = cmd
                if name == "jump":
                    if args:
                        for arg in args:
                            n = int(arg)
                            jump(n)
                    else:
                        jump(DEFAULT_JUMP_DURATION)
            
                elif name in ("left", "right", "up", "down"):
                    n = int(args[0]) if args else DEFAULT_N
                    {"left": left, "right": right, "up": up, "down": down}[name](n)
                else:
                    print(f"Unknown command: {name}")
                    sys.exit(1)
    else:
        print(__doc__); sys.exit(1)
