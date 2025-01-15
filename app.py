# Processing video 
# requirements

import cv2
import os
from funcs import resize_frame

# open all the videos in a folder

folder = "/home/cheesesnakes/Storage/large-files/chapter-4/videos/20250114/barracuda"

# set environment variables

os.environ['OPENCV_FFMPEG_READ_ATTEMPTS'] = '100000'

# get all the files in the folder

files = os.listdir(folder)

# loop through the files

for file in files:
    
    # get the full path of the file
    
    path = os.path.join(folder, file)
    
    # open the video
    
    video = cv2.VideoCapture(path)
    
    # print parent folder and file name
    
    print(f"Parent folder: {folder}", f"File name: {file}", sep="\n")
    
    # loop through the frames
    
    while True:
    
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
                
        # show the frame
    
        cv2.imshow("fish-behavior-video", frame)
    
        # play the video
        
        key = cv2.waitKey(1) & 0xFF
    
        # if the user presses 'q', break
    
        if key == ord("q"):
            
            break
    
    # release the video
    
    video.release()
    
    # close the window
    
    cv2.destroyAllWindows()