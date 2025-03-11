# requirements


import json
import os
import argparse
from PyQt5 import QtWidgets as widgets
import cv2
import random


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
        "Use the number keys to record the fish's behaviour\n"
        "Press 'z' to stop the observation \n"
        "Press 'p' to record a predator in frame."
    )

    parser = argparse.ArgumentParser(
        prog="Fish Behaviour Video Annotation Tool v2.0",
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

    args = parser.parse_args()

    return args


# project loader and initializer


class projectDialog(widgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Project Selection")

        layout = widgets.QHBoxLayout()

        self.project = widgets.QLineEdit()
        self.project.setReadOnly(True)

        self.select = widgets.QPushButton("Select")
        self.cancel = widgets.QPushButton("Cancel")

        layout.addWidget(self.project)
        layout.addWidget(self.select)
        layout.addWidget(self.cancel)

        self.select.clicked.connect(self.select_project)
        self.cancel.clicked.connect(self.reject)

        self.setLayout(layout)

    def select_project(self):
        project = widgets.QFileDialog.getOpenFileName(self, "Select Project File")
        self.project.setText(project[0])

        self.return_project()

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
        self.data_folder = widgets.QPushButton("Select Data Folder")

        self.data_file = widgets.QPushButton("Select Data File")
        self.size_file = widgets.QPushButton("Select file with sizes")
        self.behaviour_file = widgets.QPushButton("Select file with behaviours")

        self.replicates = widgets.QSpinBox()
        self.replicates.setMinimum(1)

        self.plots = widgets.QSpinBox()
        self.plots.setMinimum(1)

        self.sample_n = widgets.QSpinBox()
        self.sample_n.setMinimum(0)

        self.sample_s = widgets.QSpinBox()
        self.sample_s.setMinimum(0)

        self.init = widgets.QPushButton("Initialize")
        self.cancel = widgets.QPushButton("Cancel")

        layout.addRow("Project:", self.project_name)
        layout.addRow("Project Type:", self.project_type)
        layout.addRow("Video Folder:", self.video_folder)
        layout.addRow("Data Folder:", self.data_folder)
        layout.addRow("Data File:", self.data_file)
        layout.addRow("Size File:", self.size_file)
        layout.addRow("Behaviour File:", self.behaviour_file)
        layout.addRow("Replicates:", self.replicates)
        layout.addRow("Plots or Treatments:", self.plots)
        layout.addRow("Number of samples:", self.sample_n)
        layout.addRow("Sample Size:", self.sample_s)

        layout.addRow("Initialize", self.init)
        layout.addRow("Cancel", self.cancel)

        self.init.clicked.connect(self.init_project)
        self.cancel.clicked.connect(self.reject)
        self.video_folder.clicked.connect(self.select_folder)
        self.data_folder.clicked.connect(self.select_folder)
        self.data_file.clicked.connect(self.select_file)
        self.size_file.clicked.connect(self.select_file)
        self.behaviour_file.clicked.connect(self.select_file)

        self.setLayout(layout)

    def init_project(self):
        # check if project name or video

        if not self.project_name.text() or not self.video_folder.text():
            message = widgets.QMessageBox()
            message.setText("Please fill in the project name and video folder.")
            message.exec_()
            return

        self.project_info["name"] = self.project_name.text()
        self.project_info["type"] = self.project_type.currentText()
        self.project_info["video_folder"] = self.video_folder.text()
        self.project_info["data_folder"] = self.data_folder.text()
        self.project_info["data_file"] = self.data_file.text()
        self.project_info["size_file"] = self.size_file.text()
        self.project_info["behaviour_file"] = self.behaviour_file.text()
        self.project_info["replicates"] = self.replicates.value()
        self.project_info["plots"] = self.plots.value()
        self.project_info["sample_n"] = self.sample_n.value()
        self.project_info["sample_s"] = self.sample_s.value()

        # calculate project status

        self.project_stats()

        # prompt to save project file

        project_file = widgets.QFileDialog.getSaveFileName(self, "Save Project File")

        with open(project_file, "w") as f:
            json.dump(self.project_info, f)

        self.accept()

    def project_stats(self):
        if self.project_type.currentText() == "Individual":
            self.project_info["total_plots"] = 1
            self.project_info["total_samples"] = 0
            self.project_info["total_time"] = 0
            self.project_info["plot_info"] = None

            # determine number of individuals

            self.project_info["total_individuals"] = len(os.listdir(self.video_folder))

            # determine time per individuals

            individual_info = {}

            for individual in os.listdir(self.video_folder.text()):
                video = cv2.VideoCapture(individual)
                time = video.get(cv2.CAP_PROP_FRAME_COUNT) / video.get(cv2.CAP_PROP_FPS)

                individual_info[individual] = time
                self.project_info["total_time"] += time

        else:
            # total number of plots

            self.project_info["total_plots"] = (
                self.plots.value() * self.replicates.value()
            )

            # total number of samples

            self.project_info["total_samples"] = (
                self.sample_n.value() * self.project_info["total_plots"]
            )

            # caluculate total time of videos captured per plot

            plot_info = {}

            for replicate in os.listdir(self.video_folder.text()):
                for plot in os.listdir(self.video_folder.text() + "/" + replicate):
                    time = []
                    n_videos = 0
                    plot_id = str.join("_", [replicate, plot])
                    plot_info[plot_id] = {}

                    for video in os.listdir(
                        self.video_folder.text() + "/" + replicate + "/" + plot
                    ):
                        video_path = (
                            self.video_folder.text()
                            + "/"
                            + replicate
                            + "/"
                            + plot
                            + "/"
                            + video
                        )

                        video = cv2.VideoCapture(video_path)

                        try:
                            if video.get(cv2.CAP_PROP_FPS) > 0:
                                fps = video.get(cv2.CAP_PROP_FPS)
                            else:
                                fps = 60

                            time.append(video.get(cv2.CAP_PROP_FRAME_COUNT) / fps)

                            n_videos += 1

                        except ValueError:
                            raise ValueError(f"Error reading video file{video_path}")

                    plot_info[plot_id]["time"] = sum(time)
                    plot_info[plot_id]["min_vid"] = min(time)
                    plot_info[plot_id]["max_vid"] = max(time)
                    plot_info[plot_id]["n_videos"] = n_videos
                    plot_info[plot_id]["path"] = (
                        self.video_folder.text() + "/" + replicate + "/" + plot
                    )

            self.project_info["plot_info"] = plot_info

            # calculate total time of all videos captured

            self.project_info["total_time"] = sum(
                [plot["time"] for plot in plot_info.values()]
            )

            # calculate subsample times

            samples = {}

            if self.sample_n.value() > 0:
                for plot in plot_info.keys():
                    samples[plot] = {}

                    start_times = []

                    available_space = int(
                        plot_info[plot]["time"]
                        - 10 * 60  # discard first 10 minutes
                        - self.sample_s.value() * self.sample_n.value()
                    )

                    if available_space < 0:
                        raise ValueError(f"Sample size too large for plot {plot}")

                    gaps = sorted(
                        random.sample(range(0, available_space), self.sample_n.value())
                    )

                    start_times = [
                        gaps[i] + i * self.sample_s.value() + 10 * 60
                        for i in range(0, self.sample_n.value())
                    ]

                    for i in range(0, self.sample_n.value()):
                        sample_id = str.join("_", [plot, str(i)])

                        samples[plot][sample_id] = {
                            "start_time": start_times[i],
                            "video": None,
                            "status": "pending",
                        }

                    # find sample video path

                    def find_video(self, start_time, plot_path):
                        end_time = start_time + self.sample_s.value()

                        vid_start = 0
                        vid_end = 0

                        found = False

                        for video in os.listdir(plot_path):
                            # load video

                            video_path = plot_path + "/" + video
                            stream = cv2.VideoCapture(video_path)

                            # check if video path is null

                            if not video_path:
                                raise ValueError(
                                    f"Error reading video file {video_path}"
                                )

                            # check if video is valid

                            if not stream.isOpened():
                                raise ValueError(
                                    f"Error reading video file {video_path}"
                                )

                            # check if start time is within video

                            if stream.get(cv2.CAP_PROP_FPS) > 0:
                                fps = stream.get(cv2.CAP_PROP_FPS)
                            else:
                                fps = 60

                            vid_end += stream.get(cv2.CAP_PROP_FRAME_COUNT) / fps

                            if vid_start <= start_time + 1 and vid_end + 1 >= end_time:
                                found = True
                                return video_path, start_time + 1 - vid_start
                            else:
                                vid_start = vid_end

                        if not found:
                            # adjust start time
                            start_time = start_time + 30
                            return find_video(self, start_time, plot_path)

                    for sample in samples[plot].keys():
                        video_path, start_time = find_video(
                            self,
                            samples[plot][sample]["start_time"],
                            plot_info[plot]["path"],
                        )

                        samples[plot][sample]["video"] = video_path
                        samples[plot][sample]["start_time"] = start_time

                        # check if video is found

                        if samples[plot][sample]["video"] is None:
                            raise ValueError(
                                f"Error finding video for sample {sample} in plot {plot}"
                            )

                self.project_info["samples"] = samples

    def select_folder(self):
        folder = widgets.QFileDialog.getExistingDirectory(self, "Select Folder")

        self.video_folder = folder

    def select_file(self):
        file = widgets.QFileDialog.getOpenFileName(self, "Select File")[0]

        if self.sender() == self.data_file:
            self.data_file = file
        elif self.sender() == self.size_file:
            self.size_file = file
        elif self.sender() == self.behaviour_file:
            self.behaviour_file = file
