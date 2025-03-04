import cv2
import json
import os
from PyQt5 import QtWidgets as widgets

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


class DataEntryDialog(widgets.QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Enter Fish Data")

        layout = widgets.QFormLayout()

        self.species_entry = widgets.QLineEdit()
        self.group_entry = widgets.QLineEdit()
        self.size_entry = widgets.QLineEdit()
        self.remarks_entry = widgets.QLineEdit()

        layout.addRow("Species*:", self.species_entry)
        layout.addRow("Group*:", self.group_entry)
        layout.addRow("Size Class (cm)*:", self.size_entry)
        layout.addRow("Remarks:", self.remarks_entry)
        
        layout.addRow(widgets.QPushButton("Submit", clicked=self.accept))
        layout.addRow(widgets.QPushButton("Cancel", clicked=self.reject))
        self.setLayout(layout)

    def accept(self):
        
        # Check if all fields are filled

        if not all([
            self.species_entry.text(),
            self.group_entry.text(),
            self.size_entry.text()
        ]):
            widgets.QMessageBox.warning(self, "Error", "Please fill all required fields.")
            return
        
        super().accept()

        self.releaseKeyboard()

        self.result = {
            "species": self.species_entry.text(),
            "group": self.group_entry.text(),
            "size_class": self.size_entry.text(),
            "remarks": self.remarks_entry.text()
        }

        self.return_result()

    def reject(self):
        self.releaseKeyboard()
        self.result = None
        self.return_result()
        super().reject()
    
    def return_result(self):
        return self.result
    
# enter data on fish individuals
def enter_data(frame, video, data, file, deployment_id, coordinates, status_bar):
    
    # Variables
    fish_id = "_".join([deployment_id, str(len(data) + 1)])
    time_in = video.frame_time 
    print(f"\n Fish: {fish_id}, Time in: {time_in}")

    # Get data from dialog

    dialog = DataEntryDialog()
    dialog.exec_()
    result = dialog.return_result()

    if not result:

        return
    
    species = result["species"]
    group = result["group"]
    size = result["size_class"]
    remarks = result["remarks"]


    # Coordinates
    x1, y1, x2, y2 = coordinates

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

    video.stream.set(cv2.CAP_PROP_POS_MSEC, time_in)
    video.speed = 1
    video.paused = True
    # alert on screen
    status_bar.showMessage(f"\nObserving fish {fish_id}, species: {species}, size: {size}cm.\n")


# calculate time the individual has been in the frame
def time_out(video, status_bar):
    """After enter_data is run, continue until click and record time out"""

    # Get the last fish id
    fish_id = list(video.data.keys())[-1]

    # Get the time out
    time_out = video.frame_time 

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

    status_bar.showMessage(
        f"\nFish {fish_id} has been recorded from {round(video.data[fish_id]['time_in'], 2)} to {round(time_out, 2)}\n"
    )


# predator data entry

class predatorDialog(widgets.QDialog):

    def __init__(self, parent):
        self.result = None
        super().__init__(parent)

        self.setWindowTitle("Enter Predator Data")

        layout = widgets.QFormLayout()

        self.species_entry = widgets.QLineEdit()
        self.size_entry = widgets.QLineEdit()
        self.remarks_entry = widgets.QLineEdit()

        layout.addRow("Species*:", self.species_entry)
        layout.addRow("Size Class (cm)*:", self.size_entry)
        layout.addRow("Remarks:", self.remarks_entry)

        layout.addRow(widgets.QPushButton("Submit", clicked=self.accept))
        layout.addRow(widgets.QPushButton("Cancel", clicked=self.reject))
        self.setLayout(layout)

    def accept(self):

        # Check if all fields are filled

        if not all([
            self.species_entry.text(),
            self.size_entry.text()
        ]):
            widgets.QMessageBox.warning(self, "Error", "Please fill all required fields.")
            return

        super().accept()

        self.releaseKeyboard()

        self.result = {
            "species": self.species_entry.text(),
            "size_class": self.size_entry.text(),
            "remarks": self.remarks_entry.text()
        }

        self.return_result()

    def reject(self):

        self.releaseKeyboard()
        self.result = None
        self.return_result()
        super().reject()

    def return_result(self):
        return self.result

def predators(video, frame, status_bar):
    # load predator data from file, if it exists
    predators = {}

    # get deployment id
    deployment_id = video.deployment_id

    # make window
    # Variables
    predator_id = "_".join(["PRED", deployment_id, str(len(predators) + 1)])
    time_in = video.frame_time 
    
    dialog = predatorDialog(video)
    dialog.exec_()

    if not dialog.result:
        return
    
    # Save data
    predators[predator_id] = {
        "species": dialog.result["species"],
        "size_class": dialog.result["size_class"],
        "time": time_in,
        "remarks": dialog.result["remarks"]
    }
    
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
    status_bar.showMessage(f"\rPredator {predator_id}, species: {dialog.result["species"]}, size: {dialog.result["size_class"]}cm., time: {time_in}\n")


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
    time = video.frame_time 

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
