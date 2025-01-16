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

# save the image within the rectangle

def save_image(frame, coordinates, fish_id):
    
    x1, y1, x2, y2 = coordinates
    
    # get the fish image
    
    fish_image = frame[y1:y2, x1:x2]
    
    # save the image
    
    cv2.imwrite(f"fish_images/{fish_id}.png", fish_image)
    
    print(f"Image saved successfully as fish_images/{fish_id}.png")

# save data to json

def save_to_json(data):
    try:
        # Load existing data if file exists
        existing_data = {}
        if os.path.exists('data.json'):
            with open('data.json', 'r') as f:
                existing_data = json.load(f)
        
        # Update with new data
        existing_data.update(data)
        
        # Write back to file
        with open('data.json', 'w') as f:
            json.dump(existing_data, f, indent=4)
        
    except Exception as e:
        print(f"Error saving to JSON: {e}")

# enter data on fish individuals

def enter_data(frame, data, file, deployment_id):
    
    global drawing_state

    if drawing_state['pt1'] and drawing_state['pt2'] and not drawing_state['drawing']:
        
        # prompt user if they want to enter data
        
        user = input("Do you want to enter data for this fish? (y/n): ")
        
        if user.lower() != 'y':
            
            clear_points()
            
            return False
        
        # Variables
        fish_id = '_'.join([deployment_id, str(len(data) + 1)])

        # Get user input from the terminal
        species = input("Enter species: ")
        group = input("Enter group: ")
        size_class = input("Enter size class (cm): ")
        remarks = input("Enter remarks: ")

        x1, y1 = drawing_state['pt1']
        x2, y2 = drawing_state['pt2']

        data[fish_id] = {
            'species': species,
            'size_class': size_class,
            'remarks': remarks,
            'coordinates': (x1, y1, x2, y2),
            'file': file
        }

        save_image(frame, (x1, y1, x2, y2), fish_id)
        save_to_json(data)
        clear_points()


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