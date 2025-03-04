# requirements

from tkinter import filedialog, Tk, ttk, simpledialog
import json
import os
import sys
import argparse

# resume session function


def session():
    start_time = 0

    # prompt user if they want to resume

    user = input("Do you want to resume from previous session? (y/n): ")

    if user.lower() != "y":
        sys.stdout.write("\r")
        sys.stdout.flush()

        print("Starting new session. Please select a file.\n")

        file = select_file()

        # create a dictionary to store the data, if data exists, load it

        data = {}

        if os.path.exists("data.json"):
            data = json.load(open("data.json", "r"))

        return file, data, start_time

    # Load data

    if os.path.exists("data.json"):
        sys.stdout.write("\r")
        sys.stdout.flush()

        data = json.load(open("data.json", "r"))

        print(f"\nResumed from previous session. {len(data)} fish data loaded.\n")

        file = list(data.values())[-1]["file"]

        start_time = list(data.values())[-1]["time_in"]

        print(f"The last fish encountered was at {round(start_time, 2)} seconds\n")

        return file, data, start_time

    else:
        sys.stdout.write("\r")

        sys.stdout.flush()

        data = {}

        print("No previous data found. Starting new session. \n")

        print("Please select a file. \n")

        file = select_file()

        return file, data, start_time


# dialog for selecting folder


def select_file():
    root = Tk()

    root.withdraw()

    # set size

    root.geometry("0x0")

    # select file

    file = filedialog.askopenfilename()

    # handle no file selected

    if not file:
        print("No file selected")

        exit()

    return file

# help description
def cmdargs():

    epilog = (
        "Key bindings:\n "
        "Press '[space]' to pause the video\n "
        "Press 'q' to quit the video\n "
        "Press ',' to skip backward\n "
        "Press '.' to skip forward\n "
        "Press ']' to increase speed\n "
        "Press '[' to decrease speed\n\n"
        "Data and images are saved automatically in the root folder\n\n"
        "Data collection\n"
        "Click and drag to draw a bounding box around the fish and start an observation\n"
        "Use the number keys to record the fish's behavior\n"
        "Press 'z' to stop the observation \n"
        "Press 'p' to record a predator in frame."
    )

    parser = argparse.ArgumentParser(
        prog="Fish Behavior Video Annotation Tool v0.1",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=epilog,
    )

    parser.add_argument(
        "-g", "--gpu", help="Run detection model with CUDA.", action="store_true"
    )
    parser.add_argument(
        "-d", "--detect", help="Run with detection model.", action="store_true"
    )
    parser.add_argument(
        "-t", "--track", help="Run with tracking algorythm.", action="store_true"
    )
    parser.add_argument(
        "-s", "--scale", help="Scale the video by factor.", type=int, default=2
    )

    args = parser.parse_args()

    return args
