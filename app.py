# Processing video 
# requirements

import cv2
import os
from funcs import resize_frame, select_folder, draw_rectangle, get_points, clear_points, enter_data

# open all the videos in a folder

folder = "/home/cheesesnakes/Storage/large-files/chapter-4/videos/20250114/barracuda"

#folder = select_folder()

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
    
    # loop through the frames
    
    while True:
        
        if not paused:
            
            # read the frame
        
            ret, frame = video.read()

            # get length of the video
            
            length = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # get fps of the video
            
            fps = int(video.get(cv2.CAP_PROP_FPS))
            
            # if the frame is empty, break
        
            if not ret:
                
                break
            
            # resize frame to fit screen
            
            frame = resize_frame(frame = frame, window_name="fish-behavior-video")
            
            cv2.setMouseCallback("fish-behavior-video", draw_rectangle)
            
            # Draw rectangle if points exist
            pt1, pt2 = get_points()
            
            if pt1 and pt2:
                
                frame_copy = frame.copy()
                
                cv2.rectangle(frame_copy, pt1, pt2, (0, 255, 0), 2)
                
                cv2.imshow("fish-behavior-video", frame_copy)
                
                enter_data(frame=frame, data=data, file=path)
            
            else:
                cv2.imshow("fish-behavior-video", frame)
            
        # play the video
        
        key = cv2.waitKey(1) & 0xFF
    
        # if the user presses 'q', break
    
        if key == ord("q"):
            
            break 
        
        elif key == ord(" "):
            
            paused = not paused
        
        elif key == ord("c"):  # Clear rectangle
            
            clear_points()  
    
    # release the video
    
    video.release()
    
    # close the window
    
    cv2.destroyAllWindows()