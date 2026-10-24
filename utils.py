import subprocess
import os
from pathlib import Path
import re

ADB = ["adb", "-s", "2053449"]



def take_ss(save_path: str = "images/screen.png") -> str:
    """
    Takes a screenshot and saves it without overwriting existing files.
    Uses filenames like screen.png, screen(1).png, screen(2).png.
    """
    original_path = Path(save_path)
    original_path.parent.mkdir(parents=True, exist_ok=True)

    path = original_path
    while path.exists():
        match = re.search(r"\((\d+)\)(?=\.)", str(path)) # check till "." in the file (file ending) and increment the number part

        if match:
            counter = int(match.group(1)) + 1
            path = Path(re.sub(r"\(\d+\)(?=\.)", f"({counter})", str(path)))
        else:
            path = Path(re.sub(r"\.", "(1).", str(path)))
    print(path)
    # Capture and save
    result = subprocess.run(
        ADB + ["exec-out", "screencap", "-p"],
        capture_output=True,
        check=True
    )
    
    with open(path, "wb") as f:
        f.write(result.stdout)
        
    return str(path)

def click(x: int, y: int):
    """Taps the screen at the given (x, y) coordinates."""
    subprocess.run(ADB + ["shell", "input", "tap", str(x), str(y)], check=True)
    print(f"Clicked at ({x}, {y})")
    return