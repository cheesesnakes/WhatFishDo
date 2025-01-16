#!/usr/bin/env python

# Processing video 
# requirements

import cv2
import os
from funcs import resize_frame, select_folder, draw_rectangle, get_points, enter_data, seek

def app():

    # welcome message
    
    print("Fish Behavior Video Annotation Tool v0.01")
    
    # open all the videos in the selected folder

    folder = select_folder()
    
    # set deployment id

    ## seperate folder by '/'

    deployment_id = folder.split("/")

    ## get last two elements

    deployment_id = deployment_id[-2:]

    ## join the elements in reverse order separated by '_'

    deployment_id = "_".join(deployment_id[::-1])

    # set environment variables

    os.environ['OPENCV_FFMPEG_READ_ATTEMPTS'] = '150000'
    os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "video_codec;hevc"


    # get all the files in the folder

    files = os.listdir(folder)

    # create a dictionary to store the data, if data exists, load it

    data = {}
    
    if os.path.exists("data.json"):
        
        import json
        
        with open("data.json", "r") as file:
            
            data = json.load(file)

    # loop through the files

    for file in files:
        
        # get the full path of the file
        
        path = os.path.join(folder, file)
        
        # open the video
        
        video = cv2.VideoCapture(path, cv2.CAP_FFMPEG)
        
        # print parent folder and file name
        
        print(f"Deployment: {deployment_id}", f"File: {file}", sep="\n")
        
        # set vdieo state
        
        paused = False
        SKIP_SECONDS = 2
        speed = 1
        i=0
        
        # loop through the frames
        
        while True:
            
            # check pause state
            
            if not paused:
                
                # read the frame
                    
                ret = video.grab()
                
                i += 1
            
                if not ret:
                    
                    break
                    
                # set playback speed
                
                if i % speed == 0:
                    
                    ret, frame = video.retrieve()
                    
                    if not ret:
                        
                        break
                    
                    # resize the frame
                    
                    cv2.namedWindow("fish-behavior-video", cv2.WINDOW_NORMAL)
                    
                    # Area selection (bbox)
                    
                    cv2.setMouseCallback("fish-behavior-video", draw_rectangle)
                    
                    pt1, pt2 = get_points()
                    
                    if pt1 and pt2:
                        
                        frame_copy = frame.copy()
                        
                        cv2.rectangle(frame_copy, pt1, pt2, (0, 255, 0), 2)
                        
                        cv2.putText(frame_copy, f"Playback Speed = {speed}x", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                                                
                        enter_data(frame=frame, data=data, file=path, deployment_id=deployment_id)

                        cv2.imshow("fish-behavior-video", frame_copy)
                        
                    else:
                        
                        cv2.putText(frame, f"Playback Speed = {speed}x", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                        
                        cv2.imshow("fish-behavior-video", frame)                 
                        
                        # handle key presses
                        
                        fps = video.get(cv2.CAP_PROP_FPS)
            
                        key = cv2.waitKey(int(1000/(fps*speed))) & 0xFF
        
            # handle key presses
            
            fps = video.get(cv2.CAP_PROP_FPS)
            
            key = cv2.waitKey(int(1000/(fps*speed))) & 0xFF
        
            # key press logic
        
            if key == ord("q"): #quit
                
                print("Quitting...")
                
                break 
            
            elif key == ord(" "): #pause
                
                paused = not paused
            
            elif key == ord(","):  # Skip backward 

                current_frame = video.get(cv2.CAP_PROP_POS_FRAMES)
                
                fps = video.get(cv2.CAP_PROP_FPS)
                
                frames_to_skip = int(fps * SKIP_SECONDS)
                
                target_frame = max(0, current_frame - frames_to_skip)
                
                video.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
            
            elif key == ord("."):  # Skip backward

                current_frame = video.get(cv2.CAP_PROP_POS_FRAMES)
                
                fps = video.get(cv2.CAP_PROP_FPS)
                
                frames_to_skip = int(fps * SKIP_SECONDS)
                
                target_frame = max(0, current_frame + frames_to_skip)
                
                video.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
                
            elif key == ord("["): # decrease speed
                
                speed = max(0.5, speed - 0.5)
            
            elif key == ord("]"): # increase speed
                
                speed = min(10, speed + 0.5)
            
            elif key == ord("t"): # seek
                
                seek(video)
                
        # release the video
        
        video.release()
        
        # close the window
        
        cv2.destroyAllWindows()

if __name__ == "__main__":
    
    app()