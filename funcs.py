# requirements

import cv2
from tkinter import filedialog, Tk, ttk, DoubleVar
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


# calculate current time in video


def current_time(video):
    """Calculate current time in video"""

    try:
        # Get video properties

        fps = video.get(cv2.CAP_PROP_FPS)
        current_frame = int(video.get(cv2.CAP_PROP_POS_FRAMES))
        current_time = current_frame / fps

        return current_time

    except Exception as e:
        print(f"Error calculating current time: {e}")

        return False


# time seek functiono


def seek(video):
    """Seek to specific time in video"""

    try:
        # Get video properties

        fps = video.get(cv2.CAP_PROP_FPS)
        total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps

        # create a window

        root = Tk()
        root.title("Seek Time")
        root.geometry("200x200")

        # Variables

        time_var = DoubleVar()
        ttk.Label(root, text=f"Enter time (0-{duration:.1f} seconds):").pack(pady=5)
        time_box = ttk.Entry(root, textvariable=time_var)
        time_box.pack(pady=5)

        # Ok and Cancel buttons

        def on_ok():
            try:
                target_seconds = int(time_var.get())

                # Calculate target frame

                target_frame = int(target_seconds * fps)

                # Validate target

                if target_frame < 0 or target_frame > total_frames:
                    print(f"Invalid time. Video duration: {duration:.2f}s")

                    return False

                # Set position

                video.set(cv2.CAP_PROP_POS_FRAMES, target_frame)

                # destroy the window

                root.destroy()

                return True

            except Exception as e:
                print(f"Error seeking video: {e}")

                root.destroy()

                return False

        def on_cancel():
            root.destroy()

            return True

        # Buttons

        ttk.Button(root, text="OK", command=on_ok).pack(pady=5)
        ttk.Button(root, text="Cancel", command=on_cancel).pack(pady=5)

        root.mainloop()

    except Exception as e:
        print(f"Error seeking video: {e}")

        return False
