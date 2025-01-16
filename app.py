#!/usr/bin/env python

# Processing video 
# requirements

import os
import json
from funcs import select_file
from stream import VideoStream

def app():

    # welcome message
    
    print("Fish Behavior Video Annotation Tool v0.01")
    
    # Print instructions and key bindings
    
    print("Instructions:")
    
    print("1. Press '[space]' to pause the video")
    print("2. Press 'q' to quit the video")
    print("3. Press ',' to skip backward")
    print("4. Press '.' to skip forward")
    print("5. Press ']' to increase speed")
    print("6. Press '[' to decrease speed")
    print("7. Data and images are saved automatically in the root folder")
    
    
    # open all the videos in the selected file

    file = select_file()
    
    # set deployment id
    deployment_id = file.split("/")
    deployment_id = deployment_id[-3:-1]
    deployment_id = "_".join(deployment_id[::-1])

    # set environment variables

    os.environ['OPENCV_FFMPEG_READ_ATTEMPTS'] = '150000'
    os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS'] = 'threads;1|video_codec;hevc'

    # create a dictionary to store the data, if data exists, load it

    data = {}
    
    if os.path.exists(f"data.json"):
        
        data = json.load(open(f"data.json", "r"))     
    
    # print parent file and file name
    
    print(f"Deployment: {deployment_id}", f"File: {file}", sep="\n")
    
    # open the video
    
    video = VideoStream(data=data, deployment_id=deployment_id, path=file).start()
    
    # initialize the read
    
    video.read()
            
    # initialize the process
    
    video.process()
    
    print("Done")
            
if __name__ == "__main__":
    
    app()