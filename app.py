#!/usr/bin/env python

# Processing video
# requirements

# setup imports
import sys
import os
import json
from assets.funcs import cmdargs
import time
from assets.ui import MainWindow
from PyQt5 import QtWidgets


def app(detection=False, tracking=False, useGPU=False, project_path=None):
    # clear the screen
    os.system("clear")
    # set environment variables

    os.environ["OPENCV_FFMPEG_READ_ATTEMPTS"] = "150000"
    os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "threads;1|video_codec;hevc"

    # welcome message

    print("Fish Behavior Video Annotation Tool v2.0\n")

    print(
        f"Running with detection: {detection}, tracking {tracking}, and GPU:{useGPU}\n"
    )

    # start the app

    app = QtWidgets.QApplication([])

    # set stream properties

    stream_properties = {
        "detection": detection,
        "tracking": tracking,
        "useGPU": useGPU,
        "sample_id": None,
        "Plot": None,
    }
    # load project info

    if project_path is not None:
        if os.path.exists(project_path):
            print(f"Loading project file {project_path}...")
            with open(project_path, "r") as file:
                project_info = json.load(file)
        else:
            print(f"Project file {project_path} not found.")
            project_info = None
    else:
        project_info = None

    # initialize the process

    sys.stdout.write("\rStart main window...            ")
    time.sleep(0.5)
    sys.stdout.write("\r")
    sys.stdout.flush()

    # start the main MainWindow

    window = MainWindow(project_info, project_path, stream_properties)
    window.show()
    sys.exit(app.exec_())

    print("\nDone")


if __name__ == "__main__":
    args = cmdargs()

    # set default

    useGPU = False
    detection = False
    tracking = False
    project_path = None
    # check args

    if args.gpu:
        useGPU = True

    if args.detect:
        detection = True

    if args.track:
        tracking = True

    if args.project:
        project_path = args.project

    # run

    app(
        useGPU=useGPU, detection=detection, tracking=tracking, project_path=project_path
    )
