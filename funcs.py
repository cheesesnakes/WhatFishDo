# requirements

import cv2
from tkinter import filedialog, Tk, ttk, simpledialog 
import json
import os
import sys

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


# draw rectangle on frame

drawing_state = {"drawing": False, "pt1": None, "pt2": None}


def draw_rectangle(event, x, y, flags, param):
    global drawing_state

    if event == cv2.EVENT_LBUTTONDOWN:
        drawing_state["drawing"] = True
        drawing_state["pt1"] = (x, y)

    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing_state["drawing"]:
            drawing_state["pt2"] = (x, y)

    elif event == cv2.EVENT_LBUTTONUP:
        drawing_state["drawing"] = False
        drawing_state["pt2"] = (x, y)


def get_points():
    global drawing_state

    return drawing_state["pt1"], drawing_state["pt2"]


def clear_points():
    global drawing_state

    drawing_state["pt1"] = None
    drawing_state["pt2"] = None

# time seek functiono

class seekDialog(simpledialog.Dialog):

    def body(self, master):
    
        self.title("Skip to seconds")

        ttk.Label(master, text = "Enter position in seconds:").grid(row = 0)

        self.secondsEntry = ttk.Entry(master)

        self.secondsEntry.grid(row=0, column=1)

        return self.secondsEntry

    def apply(self):

        self.seconds = self.secondsEntry.get()

def seek(video):

    root = Tk()
    root.withdraw()

    dialog = seekDialog(root)

    if dialog.seconds is None:
        root.destroy()
        return

    seconds = int(dialog.seconds)

    root.destroy()

    video.skip(seconds)
    


    
