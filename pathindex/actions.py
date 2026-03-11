from __future__ import annotations

import os
import platform
import shutil
import subprocess
from pathlib import Path


def open_path(path: str) -> None:
    p = str(Path(path).expanduser())
    system = platform.system().lower()
    if "windows" in system:
        os.startfile(p)  # type: ignore[attr-defined]
        return
    if "darwin" in system:
        subprocess.run(["open", p], check=False)
        return
    subprocess.run(["xdg-open", p], check=False)


def copy_to_clipboard(text: str) -> bool:
    if shutil.which("wl-copy"):
        subprocess.run(["wl-copy"], input=text.encode("utf-8"), check=False)
        return True
    if shutil.which("xclip"):
        subprocess.run(["xclip", "-selection", "clipboard"], input=text.encode("utf-8"), check=False)
        return True
    if shutil.which("pbcopy"):
        subprocess.run(["pbcopy"], input=text.encode("utf-8"), check=False)
        return True
    return False


def open_terminal(path: str) -> None:
    p = str(Path(path).expanduser())
    term = os.getenv("TERMINAL")
    if term:
        subprocess.Popen([term], cwd=p)
        return
    for candidate in ("x-terminal-emulator", "gnome-terminal", "konsole", "kitty", "alacritty"):
        if shutil.which(candidate):
            subprocess.Popen([candidate], cwd=p)
            return
