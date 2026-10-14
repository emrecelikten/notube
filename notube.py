#!/usr/bin/env python3
"""Search YouTube and play audio in the terminal.

Delegates to the `yt-dlp` and `mpv` CLIs and uses only the standard library, so no extra packages are installed.
"""

import json
import readline  # noqa: F401  (enables line editing and history for input())
import subprocess
import sys

RESULT_COUNT = 15


def search(query: str) -> list[dict]:
    proc = subprocess.run(
        [
            "yt-dlp",
            "--flat-playlist",
            "--print",
            "%(.{id,title,channel,duration})j",
            f"ytsearch{RESULT_COUNT}:{query}",
        ],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        print(proc.stderr.strip(), file=sys.stderr)
    return [json.loads(line) for line in proc.stdout.splitlines()]


def show(results: list[dict]) -> None:
    for i, r in enumerate(results, 1):
        # Live streams have no duration.
        if r["duration"] is None:
            length = "live"
        else:
            minutes, seconds = divmod(int(r["duration"]), 60)
            length = f"{minutes}:{seconds:02d}"
        print(f"{i:>3}. [{length:>6}] {r['title']}  \033[2m{r['channel']}\033[0m")


def play(results: list[dict]) -> None:
    urls = [f"https://www.youtube.com/watch?v={r['id']}" for r in results]
    # mpv takes over the terminal while playing: space pauses, arrows seek, < > skip, q returns here.
    subprocess.run(["mpv", "--no-video", "--ytdl-format=bestaudio/best", *urls])


def main() -> None:
    query = " ".join(sys.argv[1:])
    results: list[dict] = []
    while True:
        if query:
            print(f"Searching: {query}")
            results = search(query)
            if not results:
                print("No results.")
            show(results)
        prompt = (
            "number(s) to play, text to search, q to quit> " if results else "search> "
        )
        answer = input(prompt).strip()
        query = ""
        if answer == "q":
            return
        if not answer:
            show(results)
        elif all(
            token.isdigit() and 1 <= int(token) <= len(results)
            for token in answer.split()
        ):
            play([results[int(token) - 1] for token in answer.split()])
            show(results)
        else:
            query = answer


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print()
