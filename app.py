#!/usr/bin/env python

# Processing video 
# requirements

import os
import cv2
from funcs import session
from stream import VideoStream
import argparse
import sys
import time

def help():
    
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
    
def app(detection = False, tracking = False, useGPU = False):
    
    os.system('clear')
        
    # welcome message
    
    print("Fish Behavior Video Annotation Tool v0.1\n")
    
    help()
    
    print(f"Running with detection: {detection}, tracking {tracking}, and GPU:{useGPU}\n")
    
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
    
    sys.stdout.write("\rInitialising...")
    sys.stdout.flush()
    
    video = VideoStream(data=data, deployment_id=deployment_id, path=file, 
                        useGPU = useGPU, detection=detection, tracking = tracking).start()
    
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
            
            video.stream.set(cv2.CAP_PROP_POS_MSEC, start_time)

            sys.stdout.write("\rFound last fish!!!              ")
            sys.stdout.flush()
    
    # initialize the process
    
    sys.stdout.write("\rStart processing...            ")
    sys.stdout.flush()
    time.sleep(0.2)
    sys.stdout.write("\r                                 ")
    
    video.process()
    
    print("\nDone")
            
if __name__ == "__main__":
    
    epilog = "Key bindings:\n Press '[space]' to pause the video\n Press 'q' to quit the video\n Press ',' to skip backward\n Press '.' to skip forward\n Press ']' to increase speed\n Press '[' to decrease speed\n\nData and images are saved automatically in the root folder\n\nClick and drag to draw a bounding box around the fish and start an observation"
    
    parser = argparse.ArgumentParser(prog= "Fish Behavior Video Annotation Tool v0.1", formatter_class=argparse.RawTextHelpFormatter, epilog=epilog)
    
    parser.add_argument("-g", "--gpu", help="Run detection model with CUDA.", action="store_true")
    parser.add_argument("-d", "--detect", help="Run with detection model.", action="store_true")
    parser.add_argument("-t", "--track", help="Run with tracking algorythm.", action="store_true")
    
    
    
    args = parser.parse_args()
    
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
    
    app(useGPU=useGPU, detection=detection, tracking=tracking)