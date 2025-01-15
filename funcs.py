import cv2
import tkinter as tk
from tkinter import filedialog

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