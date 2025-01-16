#!/usr/bin/env python

# Processing video 
# requirements

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
    os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS'] = 'threads;1|video_codec;hevc'

    # create a dictionary to store the data, if data exists, load it

    data = {}
            
    # get the full path of the file
    
    path = os.path.join(file, file)
    
    print(path)
    
    # print parent file and file name
    
    print(f"Deployment: {deployment_id}", f"File: {file}", sep="\n")
    
    # open the video
    
    video = VideoStream(data=data, deployment_id=deployment_id, path=path).start()
    
    # initialize the read
    
    video.read()
            
    # initialize the process
    
    video.process()
    
    print("Done")
            
if __name__ == "__main__":
    
    app()