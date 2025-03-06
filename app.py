#!/usr/bin/env python

# Processing video
# requirements

# setup imports
import sys
import os
from assets.funcs import cmdargs, load_project
import time
from assets.ui import MainWindow
from PyQt5 import QtWidgets


def app(detection=False, tracking=False, useGPU=False, scale=2, Test=False):
    os.system("clear")
    # set environment variables

    os.environ["OPENCV_FFMPEG_READ_ATTEMPTS"] = "150000"
    os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "threads;1|video_codec;hevc"

    # welcome message

    print("Fish Behavior Video Annotation Tool v0.1\n")

    print(
        f"Running with detection: {detection}, tracking {tracking}, and GPU:{useGPU}\n"
    )

    # start the app

    app = QtWidgets.QApplication([])

    # project loader

    project_info = load_project()

    # set stream properties

    stream_properties = {
        "detection": detection,
        "tracking": tracking,
        "useGPU": useGPU,
        "scale": scale,
        "sample_id": None,
        "Plot": None,
    }
    # initialize the process

    sys.stdout.write("\rStart main window...            ")
    time.sleep(0.5)
    sys.stdout.write("\r")
    sys.stdout.flush()

    # start the main MainWindow

    window = MainWindow(project_info, stream_properties)
    window.show()
    sys.exit(app.exec_())

    print("\nDone")


if __name__ == "__main__":
    args = cmdargs()

    # set default

    useGPU = False
    detection = False
    tracking = False

    # check args

    if args.gpu:
        useGPU = True

    if args.detect:
        detection = True

    if args.track:
        tracking = True

    # run

    app(useGPU=useGPU, detection=detection, tracking=tracking, scale=args.scale)
