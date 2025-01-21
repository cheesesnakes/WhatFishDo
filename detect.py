# fish detection function etc.

import cv2
import numpy as np

# function to load model

def load_model(video):
    
    # load model
        
    # load the yolo model (https://github.com/tamim662/YOLO-Fish/tree/main)
    
    video.net = cv2.dnn.readNetFromDarknet('model.cfg', 'model.weights')
    
    if video.useGPU: # run on GPU
        
        # Set the backend and target to CUDA
        video.net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
        video.net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)

    # get the output layer names
    
    video.layer_names = video.net.getLayerNames()
    
    video.output_layers = [video.layer_names[i - 1] for i in video.net.getUnconnectedOutLayers()]
    
    # get the class labels
    
    video.model_classes = ["Fish"]

# function to detect fish

def detect_fish(video, frame):
    
    # get the height and width of the frame
        
    height, width, channels = frame.shape
    
    # create a blob from the frame
    
    blob = cv2.dnn.blobFromImage(frame, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
    
    # set the input
    
    video.net.setInput(blob)
    
    # get the output
    
    outs = video.net.forward(video.output_layers)
    
    # lists for non-max suppression
    
    boxes = []
    confidences = []
    class_ids = []
    
    # loop through the detections
    
    for out in outs:
        
        for detection in out:
            
            scores = detection[5:]
            
            class_id = np.argmax(scores)
            
            confidence = scores[class_id]
            
            if confidence > 0.45:
                
                # get the center and dimensions of the box
                
                center_x = int(detection[0] * width)
                
                center_y = int(detection[1] * height)
                
                w = int(detection[2] * width)
                
                h = int(detection[3] * height)
                
                # get the top left corner
                
                x = int(center_x - w / 2)
                
                y = int(center_y - h / 2)
                
                boxes.append([x, y, w, h])
                confidences.append(float(confidence))

    return boxes, confidences

# draw boxes after non-max suppression

def draw_fish(video, frame, boxes, confidences):
    
    # get number of fish so far
    
    fish_count = len(video.data)
    
    # apply non-max suppression
    
    indices = cv2.dnn.NMSBoxes(boxes, confidences, 0.4, 0.4)
    fish_id = fish_count
    
    for i in indices:   

        box = boxes[i]
        
        x, y, w, h = box
        
        # get the fish id
        
        fish_id = fish_id + 1
        
        # draw the box
        
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        label = f"Fish {fish_id}"
        cv2.putText(frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
    return frame