import cv2
import json
import os
import tkinter as tk
from tkinter import simpledialog
from tkinter import ttk
from funcs import drawing_state, clear_points, current_time


# save the image within the rectangle
def save_image(frame, coordinates, fish_id):
    x1, y1, x2, y2 = coordinates

    # save the image
    cv2.imwrite(f"fish_images/frames/{fish_id}_frame.png", frame)

    # get the fish image
    fish_image = frame[y1:y2, x1:x2]

    # save the image
    cv2.imwrite(f"fish_images/cropped/{fish_id}.png", fish_image)

    print(f"\nImage saved successfully as fish_images/{fish_id}.png")


# save data to json
def save_to_json(data):
    try:
        # Load existing data if file exists
        existing_data = {}

        if os.path.exists("data.json"):
            with open("data.json", "r") as f:
                existing_data = json.load(f)

        # Update with new data
        existing_data.update(data)

        # Write back to file
        with open("data.json", "w") as f:
            json.dump(existing_data, f, indent=4)

    except Exception as e:
        print(f"\nError saving to JSON: {e}")


class DataEntryDialog(simpledialog.Dialog):
    def body(self, master):
        self.title("Enter Fish Data")

        ttk.Label(master, text="Species:").grid(row=0)
        ttk.Label(master, text="Group:").grid(row=1)
        ttk.Label(master, text="Size Class (cm):").grid(row=2)
        ttk.Label(master, text="Remarks:").grid(row=3)

        self.species_entry = ttk.Entry(master)
        self.group_entry = ttk.Entry(master)
        self.size_entry = ttk.Entry(master)
        self.remarks_entry = ttk.Entry(master)

        self.species_entry.grid(row=0, column=1)
        self.group_entry.grid(row=1, column=1)
        self.size_entry.grid(row=2, column=1)
        self.remarks_entry.grid(row=3, column=1)

        return self.species_entry  # initial focus

    def apply(self):
        self.result = {
            "species": self.species_entry.get(),
            "group": self.group_entry.get(),
            "size_class": self.size_entry.get(),
            "remarks": self.remarks_entry.get(),
        }


# enter data on fish individuals
def enter_data(frame, video, data, file, deployment_id):
    global drawing_state
    
    if drawing_state["pt1"] and drawing_state["pt2"] and not drawing_state["drawing"]:
        # Variables
        fish_id = "_".join([deployment_id, str(len(data) + 1)])
        time_in = current_time(video.stream)
        print(f"\n Fish: {fish_id}, Time in: {time_in}")

        root = tk.Tk()
        root.withdraw()  # Hide the root window

        dialog = DataEntryDialog(root)
        if dialog.result is None:
            clear_points()
            root.destroy()
            video.speed = 1
            return

        species = dialog.result["species"]
        group = dialog.result["group"]
        size = dialog.result["size_class"]
        remarks = dialog.result["remarks"]

        root.destroy()  # Destroy the root window after input

        # Coordinates
        x1, y1 = drawing_state["pt1"]
        x2, y2 = drawing_state["pt2"]

        data[fish_id] = {
            "species": species,
            "group": group,
            "size_class": size,
            "remarks": remarks,
            "coordinates": (x1, y1, x2, y2),
            "file": file,
            "time_in": time_in,
            "time_out": 0,
        }

        save_image(frame, (x1, y1, x2, y2), fish_id)
        save_to_json(data)
        clear_points()

        video.stream.set(cv2.CAP_PROP_POS_MSEC, time_in)
        video.speed = 1
        video.paused = True
        # alert on screen
        print(f"\nObserving fish {fish_id}, species: {species}, size: {size}cm.\n")


# calculate time the individual has been in the frame
def time_out(video):
    """After enter_data is run, continue until click and record time out"""

    # Get the last fish id
    fish_id = list(video.data.keys())[-1]

    # Get the time out
    time_out = current_time(video.stream)

    # Update the data
    video.data[fish_id]["time_out"] = time_out

    # Save to json
    save_to_json(video.data)

    # Get lock
    with video.lock:
        # Clear queue
        while not video.Q.empty():
            video.Q.get()

        # Reset frame to time in
        video.stream.set(cv2.CAP_PROP_POS_MSEC, video.data[fish_id]["time_in"])

        # Pause
        video.paused = True

    # Clear points
    clear_points()

    print(
        f"\nFish {fish_id} has been recorded from {round(video.data[fish_id]['time_in'], 2)} to {round(time_out, 2)}\n"
    )


# predator data entry
def predators(video):
    # load predator data from file, if it exists
    predators = {}

    # get deployment id
    deployment_id = video.deployment_id

    # make window
    # Variables
    predator_id = "_".join(["PRED", deployment_id, str(len(predators) + 1)])
    time_in = current_time(video.stream)
    species = input("\nSpecies: ")
    size = input("Size Class (cm): ")

    # Save data
    predators[predator_id] = {
        "species": species,
        "size_class": size,
        "time": time_in,
    }

    # Get and save image
    frame = video.Q
    cv2.imwrite(f"predator/{predator_id}.png", frame)

    # Save to json
    if os.path.exists("predators.json"):
        with open("predators.json", "r") as f:
            existing_data = json.load(f)
            existing_data.update(predators)
        with open("predators.json", "w") as f:
            json.dump(existing_data, f, indent=4)
    else:
        with open("predators.json", "w") as f:
            json.dump(predators, f, indent=4)

    # Alert on screen
    print(f"\nPredator {predator_id}, species: {species}, size: {size}cm.\n")


# record behaviour
behaviors = {
    "1": "Feeding",
    "2": "Vigilance",
    "3": "Moving",
    "4": "Bite",
    "5": "Predator avoidance",
    "6": "Conspecific agression",
    "7": "Escape from agression",
    "8": "Escape from predator",
    "9": "Aggression against predator",
}


def record_behaviour(video, key):
    global behaviors

    # Get the last fish id
    fish_id = list(video.data.keys())[-1]

    # Get the current time
    time = current_time(video.stream)

    # Get the current behaviour
    bhv = behaviors[key]

    behaviour = {"time": time, "behaviour": bhv}

    # Update the data
    if "behaviour" in video.data[fish_id]:
        video.data[fish_id]["behaviour"].append(behaviour)
    else:
        video.data[fish_id]["behaviour"] = [behaviour]

    # Save to json
    save_to_json(video.data)

    # Alert on screen
    print(f"Fish {fish_id} has been recorded to be {bhv} at {time}")
