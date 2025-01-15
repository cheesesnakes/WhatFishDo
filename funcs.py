import cv2
import tkinter as tk
from tkinter import filedialog
import json
import os
import tkinter as tk
from tkinter import ttk

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
        
        # Create main window
        
        root = tk.Tk()
        root.title("Fish Data Entry")
        root.geometry("400x400")
        
        # Variables
        
        species_var = tk.StringVar()
        group_var = tk.StringVar()
        size_var = tk.StringVar()
        remarks_var = tk.StringVar()
        fish_id = '_'.join([deployment_id, str(len(data)+1)])
        
        # Species dropdown
        
        ttk.Label(root, text="Species:").pack(pady=5)
        species_box = ttk.Entry(root, textvariable=species_var)
        species_box.pack(pady=5)
        
        # Group dropdown
        
        ttk.Label(root, text="Group:").pack(pady=5)
        group_box = ttk.Entry(root, textvariable=group_var)
        group_box.pack(pady=5)
        
        # Size class slider
        ttk.Label(root, text="Size Class (cm):").pack(pady=5)
        size_classes = ['0-10', '10-20', '20-30', '30-40', '40-50', '50-60', '60-70', '70-80', '80+']
        size_slider = ttk.Combobox(root, values=size_classes, textvariable=size_var)
        size_slider.pack(pady=5)
        
        # Remarks
        ttk.Label(root, text="Remarks:").pack(pady=5)
        remarks_entry = ttk.Entry(root, textvariable=remarks_var)
        remarks_entry.pack(pady=5)
        
        def save_and_close():
            x1, y1 = drawing_state['pt1']
            x2, y2 = drawing_state['pt2']
            
            data[fish_id] = {
                'species': species_var.get(),
                'size_class': size_var.get(),
                'remarks': remarks_var.get(),
                'coordinates': (x1, y1, x2, y2),
                'file': file
            }
            
            save_image(frame, (x1, y1, x2, y2), fish_id)
            save_to_json(data)
            clear_points()
            root.destroy()
        
        def cancel():
            clear_points()
            root.destroy()
        
        # Buttons
        ttk.Button(root, text="Save", command=save_and_close).pack(pady=10)
        ttk.Button(root, text="Cancel", command=cancel).pack(pady=5)
        
        root.mainloop()

        
        