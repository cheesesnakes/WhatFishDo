#!/usr/bin/env python

# Processing video 
# requirements

import os
import cv2
from funcs import session
from stream import VideoStream

def app():

    # welcome message
    
    print("Fish Behavior Video Annotation Tool v0.01")
    
    # Print instructions and key bindings
    
    print("Key bindings:")
    
    print("\n")
    
    print("Press '[space]' to pause the video")
    print("Press 'q' to quit the video")
    print("Press ',' to skip backward")
    print("Press '.' to skip forward")
    print("Press ']' to increase speed")
    print("Press '[' to decrease speed")
    
    print("\n")
    
    print("Data and images are saved automatically in the root folder")
    
    print("\n")
    
    print("Click and drag to draw a bounding box around the fish and start an observation")
    
    print("\n")
    
    # start or resume session
    
    file, data, start_time = session()
    
    # set deployment id
    deployment_id = file.split("/")
    deployment_id = deployment_id[-3:-1]
    deployment_id = "_".join(deployment_id[::-1])

    # set environment variables

    os.environ['OPENCV_FFMPEG_READ_ATTEMPTS'] = '150000'
    os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS'] = 'threads;1|video_codec;hevc'     
    
    # print parent file and file name
    
    print(f"Deployment: {deployment_id}", f"File: {file}", sep="\n")
    
    # open the video
    
    video = VideoStream(data=data, deployment_id=deployment_id, path=file).start()
        
    if start_time > 0:
        
        with video.lock:
            
            # clear the queue
            
            while not video.Q.empty():
                
                video.Q.get()
            
            # set  
            
            video.stream.set(cv2.CAP_PROP_POS_MSEC, start_time)

    # initialize the process
    
    video.process()
    
    print("Done")
            
if __name__ == "__main__":
    
    app()