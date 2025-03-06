#!/usr/bin/env python

# Processing video
# requirements

import os
import cv2
from funcs import cmdargs, session, load_project
from stream import VideoStream
import sys
import time
from ui import MainWindow
from PyQt5 import QtWidgets
import json


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

    if not Test:
        project_info = load_project()

    else:

        with open("project.json", "r") as f:
            project_info = json.load(f)

    # start or resume session

    if not Test:
        file, data, start_time = session(project_info)

    else:

        file = "/home/cheesesnakes/Storage/files/Shawn/Work/PhD/Thesis/chapter-4/Analysis/video-annotation/videos/20250127/positive-control/GX030262.MP4"
        start_time = 0

        with open("data.json", "r") as f:
            data = json.load(f)

    if file is not None:

        # set deployment id
        deployment_id = file.split("/")
        deployment_id = deployment_id[-3:-1]
        deployment_id = "_".join(deployment_id[::-1])

        # print parent file and file name

        print(f"Deployment: {deployment_id}", f"File: {file}", sep="\n")

        # open the video

        sys.stdout.write("\rInitialising...")
        sys.stdout.flush()

        video = VideoStream(
            data=data,
            deployment_id=deployment_id,
            path=file,
            useGPU=useGPU,
            detection=detection,
            tracking=tracking,
            scale=scale,
        ).start()

        sys.stdout.write("\rInitialised.    ")
        sys.stdout.flush()

        if start_time > 0:
            sys.stdout.write("\rSearching for last fish...")
            sys.stdout.flush()

            with video.lock:
                # clear the queue

                while not video.Q.empty():
                    video.Q.get()

                # set

                video.stream.set(cv2.CAP_PROP_POS_MSEC, start_time * 1000)

                sys.stdout.write("\rFound last fish!!!              ")
                sys.stdout.flush()
                time.sleep(0.5)
                sys.stdout.write("\r")
                sys.stdout.flush()

    # initialize the process

    sys.stdout.write("\rStart main window...            ")
    time.sleep(0.5)
    sys.stdout.write("\r")
    sys.stdout.flush()
    time.sleep(0.2)
    sys.stdout.write("\r")
    sys.stdout.flush()

    # start the main MainWindow

    window = MainWindow(data, video)
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
