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

# project loader and initializer

class projectDialog(widgets.QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Project Selection")

        layout = widgets.QFormLayout()

        self.project = widgets.QLineEdit()
        self.project.setReadOnly(True)

        self.select = widgets.QPushButton("Select Existing")
        self.new_project = widgets.QPushButton("Create New")
        self.cancel = widgets.QPushButton("Cancel")

        layout.addRow("Project:", self.project)
        layout.addRow("Select", self.select)
        layout.addRow("New Project", self.new_project)
        layout.addRow("Cancel", self.cancel)

        self.select.clicked.connect(self.select_project)
        self.new_project.clicked.connect(self.init_project)
        self.cancel.clicked.connect(self.reject)

        self.setLayout(layout)

    def select_project(self):
        project = widgets.QFileDialog.getExistingDirectory(self, "Select Project")

        self.project.setText(project)

    def return_project(self):
        if os.path.exists(self.project.text()):
            with open(self.project.text(), "r") as f:
                self.project_info = json.load(f)
            self.accept()
        else:
            message = widgets.QMessageBox()
            message.setText("Invalid Project. Please select a valid project file.")
            message.exec_()
            return
        
    def init_project(self):
        init = projectInit()
        init.exec_()

        if init.result() == 1:
            self.project_info = init.project_info
            self.accept()
        
class projectInit(widgets.QDialog):
    
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Initialize Project")
        self.project_info = {}

        layout = widgets.QFormLayout()

        self.project_name = widgets.QLineEdit()
        self.project_name.setPlaceholderText("Project Name")

        self.project_type = widgets.QComboBox()
        self.project_type.addItem("Individual")
        self.project_type.addItem("Plot")

        self.video_folder = widgets.QPushButton("Select Folder")
        
        self.replicates = widgets.QSpinBox()
        self.replicates.setMinimum(1)

        self.plots = widgets.QSpinBox()
        self.plots.setMinimum(1)

        self.samples = widgets.QSpinBox()
        self.samples.setMinimum(0)

        self.init = widgets.QPushButton("Initialize")
        self.cancel = widgets.QPushButton("Cancel")

        layout.addRow("Project:", self.project_name)
        layout.addRow("Project Type:", self.project_type)
        layout.addRow("Video Folder:", self.video_folder)
        layout.addRow("Replicates:", self.replicates)
        layout.addRow("Plots or Treatments:", self.plots)
        layout.addRow("Subsamples:", self.samples)

        layout.addRow("Initialize", self.init)
        layout.addRow("Cancel", self.cancel)

        self.init.clicked.connect(self.init_project)
        self.cancel.clicked.connect(self.reject)
        self.video_folder.clicked.connect(self.select_folder)

        self.setLayout(layout)

    def init_project(self):
    
        # check if project name or video
    
        if not self.project_name.text() or not self.video_folder_path:
            message = widgets.QMessageBox()
            message.setText("Please fill in the project name and video folder.")
            message.exec_()
            return
        

        self.project_info["name"] = self.project_name.text()
        self.project_info["type"] = self.project_type.currentText()
        self.project_info["video_folder"] = self.video_folder.text()
        self.project_info["replicates"] = self.replicates.value()
        self.project_info["plots"] = self.plots.value()
        self.project_info["samples"] = self.plots.value()

        # hidden fields
        self.project_info["last_plot"] = ""
        self.project_info["last_replicate"] = ""
        self.project_info["last_sample"] = ""

        with open("project" + ".json", "w") as f:
            json.dump(self.project_info, f)

        self.accept()
    
    def select_folder(self):
        folder = widgets.QFileDialog.getExistingDirectory(self, "Select Folder")

        self.video_folder_path = folder

def load_project():
    
    project = projectDialog()
    project.exec_()

    if project.result() == 1:
        return project.project_info
    else:
        sys.exit()