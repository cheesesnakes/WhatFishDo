#!/usr/bin/env python

# Processing video 
# requirements

import time
import cv2
import os
from funcs import select_file
from stream import VideoStream

def app():

    # welcome message
    
    print("Fish Behavior Video Annotation Tool v0.01")
    
    # open all the videos in the selected file

    file = select_file()
    
    # set deployment id

    deployment_id = file.split("/")
    deployment_id = deployment_id[-2:]
    deployment_id = "_".join(deployment_id[::-1])

    # set environment variables

    os.environ['OPENCV_FFMPEG_READ_ATTEMPTS'] = '150000'

    # create a dictionary to store the data

    data = {}
        
    # get the full path of the file
        
    path = os.path.join(file, file)
    
    # print parent file and file name
    
    print(f"Deployment: {deployment_id}", f"File: {file}", sep="\n")
    
    # initialize the video stream
    
    video = VideoStream(data, deployment_id, path).start()
    
    # read frames
    
    video.read()
    
    time.sleep(2)
    
    # process the video
    
    video.process()
    
    return

if __name__ == "__main__":
    
    app()