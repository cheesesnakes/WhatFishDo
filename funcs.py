import cv2
import tkinter as tk
from tkinter import filedialog
from uuid import uuid4
import json

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

def select_folder():
    
    root = tk.Tk()
    root.withdraw()
    
    folder = filedialog.askdirectory()
    
    return folder

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
    return drawing_state['pt1'], drawing_state['pt2']

def clear_points():
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
    
# enter data on fish individuals

def enter_data(frame, data, file):
    
    global drawing_state
    
    # if a rectangle is drawn
    
    if drawing_state['pt1'] and drawing_state['pt2'] and drawing_state['drawing'] == False:
        
        # give the individual a unique id
        
        fish_id = str(uuid4())
        
        # get the coordinates of the rectangle
        
        x1, y1 = drawing_state['pt1']
        x2, y2 = drawing_state['pt2']
        
        # enter the species of the fish
        
        species = input("Enter the species of the fish: ")
        
        # enter the size class between 0 - 80 in steps of 10
        
        size_class = input("Enter the size class of the fish (0 - 80 in steps of 10): ")
        
        # enter any remarks
        
        remarks = input("Enter any remarks: ")
        
        # add the data to the dictionary
        
        data[fish_id] = {
            'species': species,
            'size_class': size_class,
            'remarks': remarks,
            'coordinates': (x1, y1, x2, y2),
            'file': file
        }
        
        # clear the rectangle
        
        clear_points()
        
        print(f"Fish {fish_id} added successfully!", f"Total fish: {len(data)}", sep="\n")
        
        # save 
        
        save_image(frame, (x1, y1, x2, y2), fish_id)
        
        with open('data.json', 'w') as f:
            json.dump(data, f, indent=4)
            
        
        
        
        