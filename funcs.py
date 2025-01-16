# requirements

import cv2
import tkinter as tk
from tkinter import filedialog
import json
import os
import tkinter as tk
from tkinter import ttk

# resize the frame

def resize_frame(frame, window_name="Video"):
    
    
    # Get actual screen resolution
    root = tk.Tk()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    root.destroy()
    
    
    # Get frame dimensions
    frame_height, frame_width = frame.shape[:2]
    
    # Calculate resize ratio
    width_ratio = screen_width / frame_width
    height_ratio = screen_height / frame_height
    resize_ratio = min(width_ratio, height_ratio) * 0.8  # Use 80% of screen
    
    # Calculate new dimensions
    new_width = int(frame_width * resize_ratio)
    new_height = int(frame_height * resize_ratio)
    
    # Create resizable window
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    
    # Resize frame
    resized_frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)
    
    # Resize and position window
    cv2.resizeWindow(window_name, new_width, new_height)
    x = (screen_width - new_width) // 2
    y = (screen_height - new_height) // 2
    cv2.moveWindow(window_name, x, y)
    
    
    return resized_frame

# dialog for selecting folder

def select_file():
    
    root = tk.Tk()
    
    root.withdraw()
    
    # set size
    
    root.geometry("0x0")
    
    # select file
    
    file = filedialog.askopenfilename()
    
    # handle no file selected
    
    if not file:
        
        print("No file selected")
        
        exit()
    
    return file

# draw rectangle on frame

drawing_state = {
    'drawing': False,
    'pt1': None,
    'pt2': None
}

def draw_rectangle(event, x, y, flags, param):
    global drawing_state
    
    if event == cv2.EVENT_LBUTTONDOWN:
        drawing_state['drawing'] = True
        drawing_state['pt1'] = (x, y)
        
    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing_state['drawing']:
            drawing_state['pt2'] = (x, y)
            
    elif event == cv2.EVENT_LBUTTONUP:
        drawing_state['drawing'] = False
        drawing_state['pt2'] = (x, y)

def get_points():
    
    global drawing_state
    
    return drawing_state['pt1'], drawing_state['pt2']

def clear_points():
    
    global drawing_state
    
    drawing_state['pt1'] = None
    drawing_state['pt2'] = None

# calculate current time in video

def current_time(video):
    
    """Calculate current time in video"""
    
    try:
        
        # Get video properties
        
        fps = video.get(cv2.CAP_PROP_FPS)
        current_frame = int(video.get(cv2.CAP_PROP_POS_FRAMES))
        current_time = current_frame / fps
        
        return current_time
    
    except Exception as e:
        
        print(f"Error calculating current time: {e}")
        
        return False

# time seek functiono

def seek(video):
    
    """Seek to specific time in video"""
    
    try:
        
        # Get video properties
        
        fps = video.get(cv2.CAP_PROP_FPS)
        total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps
        
        # create a window
        
        root = tk.Tk()
        root.title("Seek Time")
        root.geometry("200x200")
        
        # Variables
        
        time_var = tk.DoubleVar()
        ttk.Label(root, text=f"Enter time (0-{duration:.1f} seconds):").pack(pady=5)
        time_box = ttk.Entry(root, textvariable=time_var)
        time_box.pack(pady=5)
        
        # Ok and Cancel buttons
        
        def on_ok():
            
            try:
                
                target_seconds = int(time_var.get())
                
                # Calculate target frame
                
                target_frame = int(target_seconds * fps)
                
                # Validate target
                
                if target_frame < 0 or target_frame > total_frames:
                    
                    print(f"Invalid time. Video duration: {duration:.2f}s")
                    
                    return False
                    
                # Set position
                
                video.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
                
                # destroy the window
                
                root.destroy()
                
                return True
            
            except Exception as e:
                
                print(f"Error seeking video: {e}")
                
                root.destroy()
                
                return False 
        
        def on_cancel():
            
            root.destroy()
            
            return True
        
        # Buttons
        
        ttk.Button(root, text="OK", command=on_ok).pack(pady=5)
        ttk.Button(root, text="Cancel", command=on_cancel).pack(pady=5)
        
        root.mainloop()
        
    except Exception as e:
        
        print(f"Error seeking video: {e}")
        
        return False
    
# resume session function

def session():
    
    # prompt user if they want to resume
    
    user = input("Do you want to resume from previous session? (y/n): ")
    
    if user.lower() != 'y':
        
        print("Starting new session. Please select a file.")
        
        file = select_file()
        
        # create a dictionary to store the data, if data exists, load it

        data = {}

        if os.path.exists(f"data.json"):
        
            data = json.load(open(f"data.json", "r"))
    
        return file, data
    
    # Load data
    
    if os.path.exists('data.json'):
        
        data = json.load(open('data.json', 'r'))
        
        print(f"Resumed from previous session. {len(data)} fish data loaded.")
        
        print(f"The last fish encountered was {list(data.keys())[-1]} at 'seconds'")
        
        file = list(data.values())[-1]['file']
        
        return file, data
        
    else:
        
        data = {}

        print("No previous data found. Starting new session.")
        
        print("Please select a file.")
        
        file = select_file()
        
        return file, data