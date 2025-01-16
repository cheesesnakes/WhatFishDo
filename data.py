import cv2
import json
import os
from funcs import drawing_state, clear_points, current_time

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

def enter_data(frame, video, data, file, deployment_id):
    
    global drawing_state

    if drawing_state['pt1'] and drawing_state['pt2'] and not drawing_state['drawing']:
        
        # prompt user if they want to enter data
        
        user = input("Do you want to enter data for this fish? (y/n): ")
        
        if user.lower() != 'y':
            
            clear_points()
            
            return False
        
        # Variables
        fish_id = '_'.join([deployment_id, str(len(data) + 1)])

        # time in
        
        time_in = current_time(video)
        
        # Get user input from the terminal
        species = input("Enter species: ")
        group = input("Enter group: ")
        size_class = input("Enter size class (cm): ")
        remarks = input("Enter remarks: ")

        x1, y1 = drawing_state['pt1']
        x2, y2 = drawing_state['pt2']

        data[fish_id] = {
            'species': species,
            'group': group,
            'time_in': time_in,
            'size_class': size_class,
            'remarks': remarks,
            'coordinates': (x1, y1, x2, y2),
            'file': file
        }

        save_image(frame, (x1, y1, x2, y2), fish_id)
        save_to_json(data)
        clear_points()
