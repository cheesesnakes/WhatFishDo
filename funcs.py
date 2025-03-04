# requirements


import json
import os
import sys
import argparse
from PyQt5 import QtWidgets as widgets

# user prompt for resume

class ResumeDialog(widgets.QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Session")

        layout = widgets.QFormLayout()

        self.resume = widgets.QPushButton("Resume")
        self.new = widgets.QPushButton("New")

        layout.addRow("Resume", self.resume)
        layout.addRow("New", self.new)

        self.resume.clicked.connect(self.resume_session)
        self.new.clicked.connect(self.new_session)

        self.setLayout(layout)

    def resume_session(self):
        self.accept()

    def new_session(self):
        self.reject()

# file selection dialog

class FileDialog(widgets.QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Select File")

        layout = widgets.QFormLayout()

        self.file = widgets.QLineEdit()
        self.file.setReadOnly(True)

        self.select = widgets.QPushButton("Select")
        self.cancel = widgets.QPushButton("Cancel")

        layout.addRow("File:", self.file)
        layout.addRow("Select", self.select)
        layout.addRow("Cancel", self.cancel)

        self.select.clicked.connect(self.select_file)
        self.cancel.clicked.connect(self.reject)

        self.setLayout(layout)

    def select_file(self):
        file = widgets.QFileDialog.getOpenFileName(self, "Select File")[0]

        self.file.setText(file)

    def return_file(self):
        return self.file.text()
    

# resume session function

def session():
    start_time = 0

    # prompt user if they want to resume

    resume = ResumeDialog()
    resume.exec_()

    if resume.result() == 0: # new session
        sys.stdout.write("\r")
        sys.stdout.flush()

        print("Starting new session. Please select a file.\n")
        
        filediaglog = FileDialog()
        filediaglog.exec_()
        file = filediaglog.return_file()

        if not file:
            print("No file selected. Exiting...")
            sys.exit()

        # create a dictionary to store the data, if data exists, load it

        data = {}

        if os.path.exists("data.json"):
            data = json.load(open("data.json", "r"))

        return file, data, start_time

    # resume session

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

        message = widgets.QMessageBox()
        message.setText("No previous session found. Please select a file.")
        message.exec_()

        filediaglog = FileDialog()
        filediaglog.exec_()
        file = filediaglog.return_file()

        if not file:
            print("No file selected. Exiting...")
            sys.exit()

        return file, data, start_time

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
