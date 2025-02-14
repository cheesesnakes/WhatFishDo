import cv2
import json
import os
from funcs import drawing_state, clear_points, current_time
from tkinter import Tk, Label, Entry, Button, StringVar

# save the image within the rectangle


def save_image(frame, coordinates, fish_id):
    x1, y1, x2, y2 = coordinates

    # get the fish image

    fish_image = frame[y1:y2, x1:x2]

    # save the image

    cv2.imwrite(f"fish_images/{fish_id}.png", fish_image)

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


# enter data on fish individuals


def enter_data(frame, video, data, file, deployment_id):
    global drawing_state

    if drawing_state["pt1"] and drawing_state["pt2"] and not drawing_state["drawing"]:
        root = Tk()
        root.title("Fish Data Entry")
        root.geometry("400x400")

        # Variables
        fish_id = "_".join([deployment_id, str(len(data) + 1)])
        time_in = current_time(video)
        species_var = StringVar()
        group_var = StringVar()
        size_var = StringVar()
        remarks_var = StringVar()

        # Species input
        Label(root, text="Species:").pack(pady=5)
        Entry(root, textvariable=species_var).pack(pady=5)

        # Group input
        Label(root, text="Group:").pack(pady=5)
        Entry(root, textvariable=group_var).pack(pady=5)

        # Size class input
        Label(root, text="Size Class (cm):").pack(pady=5)
        Entry(root, textvariable=size_var).pack(pady=5)

        # Remarks input
        Label(root, text="Remarks:").pack(pady=5)
        Entry(root, textvariable=remarks_var).pack(pady=5)

        def save_and_close():
            x1, y1 = drawing_state["pt1"]
            x2, y2 = drawing_state["pt2"]

            data[fish_id] = {
                "species": species_var.get(),
                "group": group_var.get(),
                "size_class": size_var.get(),
                "remarks": remarks_var.get(),
                "coordinates": (x1, y1, x2, y2),
                "file": file,
                "time_in": time_in,
                "time_out": 0,
            }

            save_image(frame, (x1, y1, x2, y2), fish_id)
            save_to_json(data)
            clear_points()
            root.destroy()

        def cancel():
            clear_points()
            root.destroy()

        # Buttons
        Button(root, text="Save", command=save_and_close).pack(pady=10)
        Button(root, text="Cancel", command=cancel).pack(pady=5)

        root.mainloop()

        # alert on screen

        print(
            f"\nObserving fish {fish_id}, species: {species_var.get()}, size: {size_var.get()}cm.\n"
        )


# calculate time the individual has been in the frame


def time_out(video):
    """After enter_data is run, continue until click and record time out"""

    # get the last fish id

    fish_id = list(video.data.keys())[-1]

    # get the time out

    time_out = current_time(video.stream)

    # update the data

    video.data[fish_id]["time_out"] = time_out

    # save to json

    save_to_json(video.data)

    # get lock

    with video.lock:
        # clear queue

        while not video.Q.empty():
            video.Q.get()

        # reset frame to time in

        video.stream.set(cv2.CAP_PROP_POS_MSEC, video.data[fish_id]["time_in"])

        # pause

        video.paused = True

    # clear points

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

    root = Tk()
    root.title("Predator Data Entry")
    root.geometry("400x400")

    # Variables

    predator_id = "_".join(["PRED", deployment_id, str(len(predators) + 1)])
    time_in = current_time(video.stream)
    species_var = StringVar()
    size_var = StringVar()

    # Species input

    Label(root, text="Species:").pack(pady=5)
    Entry(root, textvariable=species_var).pack(pady=5)

    # Size class input

    Label(root, text="Size Class (cm):").pack(pady=5)
    Entry(root, textvariable=size_var).pack(pady=5)

    def save_and_close():
        # save data

        predators[predator_id] = {
            "species": species_var.get(),
            "size_class": size_var.get(),
            "time": time_in,
        }

        # get and save image

        frame = video.Q.get()

        cv2.imwrite(f"predator/{predator_id}.png", frame)

        # save to json

        if os.path.exists("predators.json"):
            with open("predators.json", "r") as f:
                existing_data = json.load(f)

                existing_data.update(predators)

            with open("predators.json", "w") as f:
                json.dump(existing_data, f, indent=4)

        else:
            with open("predators.json", "w") as f:
                json.dump(predators, f, indent=4)

        root.destroy()

    def cancel():
        root.destroy()

    # Buttons

    Button(root, text="Save", command=save_and_close).pack(pady=10)

    Button(root, text="Cancel", command=cancel).pack(pady=5)

    root.mainloop()

    # alert on screen

    print(
        f"\nPredator {predator_id}, species: {species_var.get()}, size: {size_var.get()}cm.\n"
    )


def record_behaviour(video, key):
    global behaviors

    """
    Behaviours to record
    
    States:
    
    1: Feeding
    2: Vigilance
    3: Moving
    
    Events:
    
    4: Bite
    5: Predato avoidance
    6: Conspecific agression
    7: Escape from agression
    8: Escape from 
    9: Aggression against predator
    
    """

    # get the last fish id

    fish_id = list(video.data.keys())[-1]

    # get the current time

    time = current_time(video.stream)

    # get the current behaviour

    bhv = behaviors[key]

    behaviour = {"time": time, "behaviour": bhv}

    # update the data

    if "behaviour" in video.data[fish_id]:
        video.data[fish_id]["behaviour"].append(behaviour)

    else:
        video.data[fish_id]["behaviour"] = [behaviour]

    # save to json

    save_to_json(video.data)

    # alert on screen

    print(f"Fish {fish_id} has been recorded to be {bhv} at {time}")
