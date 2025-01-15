# Processing video 
# requirements

import cv2
import os
from funcs import resize_frame, select_folder, draw_rectangle, get_points, clear_points, enter_data

# open all the videos in a folder

folder = "/home/cheesesnakes/Storage/large-files/chapter-4/videos/20250114/barracuda"

#folder = select_folder()

# set deployment id

## seperate folder by '/'

deployment_id = folder.split("/")

## get last two elements

deployment_id = deployment_id[-2:]

## join the elements in reverse order separated by '_'

deployment_id = "_".join(deployment_id[::-1])

# set environment variables
os.environ['OPENCV_FFMPEG_READ_ATTEMPTS'] = '100000'

# get all the files in the folder

files = os.listdir(folder)

# create a dictionary to store the data

data = {}

# loop through the files

for file in files:
    
    # get the full path of the file
    
    path = os.path.join(folder, file)
    
    # open the video
    
    video = cv2.VideoCapture(path)
    
    # print parent folder and file name
    
    print(f"Parent folder: {folder}", f"File name: {file}", sep="\n")
    
    # set vdieo state
    
    paused = False
    SKIP_SECONDS = 2
    speed = 1
    i=0
    
    # loop through the frames
    
    while True:
        
        if not paused:
            
            ret = video.grab()
            
            i += 1
        
            if not ret:
                
                break
            
            if i % speed == 0:
                
                ret, frame = video.retrieve()
                
                if not ret:
                    
                    break
                
                frame = resize_frame(frame = frame, window_name="fish-behavior-video")
                
                cv2.setMouseCallback("fish-behavior-video", draw_rectangle)
                
                # Draw rectangle if points exist
                pt1, pt2 = get_points()
                
                if pt1 and pt2:
                    
                    frame_copy = frame.copy()
                    
                    cv2.rectangle(frame_copy, pt1, pt2, (0, 255, 0), 2)
                    
                    cv2.putText(frame_copy, f"Playback Speed = {speed}x", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    
                    cv2.imshow("fish-behavior-video", frame_copy)
                    
                    enter_data(frame=frame, data=data, file=path, deployment_id=deployment_id)

                else:
                    
                    cv2.putText(frame, f"Playback Speed = {speed}x", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    
                    cv2.imshow("fish-behavior-video", frame)
                    
                    
                    
        # play the video
        
        fps = video.get(cv2.CAP_PROP_FPS)
        
        key = cv2.waitKey(int(1000/(fps*speed))) & 0xFF
    
        # if the user presses 'q', break
    
        if key == ord("q"):
            
            break 
        
        elif key == ord(" "):
            
            paused = not paused
        
        elif key == ord(","):  # Skip backward 5s

            current_frame = video.get(cv2.CAP_PROP_POS_FRAMES)
            
            fps = video.get(cv2.CAP_PROP_FPS)
            
            frames_to_skip = int(fps * SKIP_SECONDS)
            
            target_frame = max(0, current_frame - frames_to_skip)
            
            video.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
        
        elif key == ord("."):  # Skip backward 5s

            current_frame = video.get(cv2.CAP_PROP_POS_FRAMES)
            
            fps = video.get(cv2.CAP_PROP_FPS)
            
            frames_to_skip = int(fps * SKIP_SECONDS)
            
            target_frame = max(0, current_frame + frames_to_skip)
            
            video.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
            
        elif key == ord("["):
            
            speed = max(0.5, speed - 0.5)
        
        elif key == ord("]"):
            
            speed = min(10, speed + 0.5)
    # release the video
    
    video.release()
    
    # close the window
    
    cv2.destroyAllWindows()