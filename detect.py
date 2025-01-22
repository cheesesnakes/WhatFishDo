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
    
    confidences = []
    class_ids = []
    
    # loop through the detections
    
    for out in outs:
        # Vectorize the detection processing
        scores = out[:, 5:]
        class_ids = np.argmax(scores, axis=1)
        confidences = scores[np.arange(len(scores)), class_ids]
        
        # Filter out weak detections
        mask = confidences > 0.5
        confidences = confidences[mask]
        class_ids = class_ids[mask]
        detections = out[mask]
        
        # create an array of boxes
        
        boxes = np.zeros((len(detections), 4))
        
        for i, detection in enumerate(detections):
            
            center_x = int(detection[0] * width)
            center_y = int(detection[1] * height)
            w = int(detection[2] * width)
            h = int(detection[3] * height)
            
            x = int(center_x - w / 2)
            y = int(center_y - h / 2)
            
            boxes[i] = [x, y, w, h]
    
    return boxes, confidences

# draw boxes after non-max suppression

def draw_fish(video, frame, boxes, confidences):
    
    # get number of fish so far
    
    fish_count = len(video.data)
    
    # apply non-max suppression
    
    indices = cv2.dnn.NMSBoxes(boxes, confidences, 0.4, 0.4)
    
    fish_id = fish_count
    
    boxes = [boxes[i] for i in indices]
    
    for i, box in enumerate(boxes):
        
        x, y, w, h = [int(i) for i in box]
        
        # get the fish id
        
        fish_id = fish_id + 1
        
        # draw the box
        
        #cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), int(2/video.scale))
        label = f"Fish {fish_id}"
        cv2.putText(frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5/video.scale, (0, 255, 0), int(2/video.scale))
        
    return frame

# function to determine intersection of boxes

def iou_vectorized(box, t_boxes):
    x1, y1, w1, h1 = box
    x2, y2, w2, h2 = t_boxes[:, 0], t_boxes[:, 1], t_boxes[:, 2], t_boxes[:, 3]

    xi1 = np.maximum(x1, x2)
    yi1 = np.maximum(y1, y2)
    xi2 = np.minimum(x1 + w1, x2 + w2)
    yi2 = np.minimum(y1 + h1, y2 + h2)
    inter_area = np.maximum(0, xi2 - xi1) * np.maximum(0, yi2 - yi1)

    box1_area = w1 * h1
    box2_area = w2 * h2
    union_area = box1_area + box2_area - inter_area

    return inter_area / union_area

# function to track fish and draw a bounding box

def track_fish(video, frame, boxes, confidences):
    
    # apply non-max suppression
    indices = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)

    # filter boxes
    boxes = [boxes[i] for i in indices]

    # update trackers
    t_boxes = []
    
    # get number of fish 
    
    fish_id = len(video.data)
    
    if len(video.trackers) > 0:
        
        for tracker in video.trackers:
            
            success, box = tracker.update(frame)
            
            if success:
                
                t_boxes.append(box)
                
                # draw
                
                x, y, w, h = [int(i) for i in box]
                
                fish_id += 1
                
                #cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), int(2/video.scale))
                
                label = f"Fish {fish_id}"
                
                cv2.putText(frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5/video.scale, (0, 255, 0), int(2/video.scale))
        
    # check if any are detected
    
    if len(boxes) == 0:
            
            return frame
    
    # Convert t_boxes to a NumPy array for vectorized operations
    if len(t_boxes) > 0:
        t_boxes_np = np.array(t_boxes)
        # Vectorized check for new fish
        ious = np.array([iou_vectorized(box, t_boxes_np) for box in boxes])
        is_tracked = np.max(ious, axis=1) > 0.5
    else:
        is_tracked = np.zeros(len(boxes), dtype=bool)

    # Process boxes that are not tracked
    new_boxes = np.array(boxes)[~is_tracked]

    # check for new fish
    for i, box in enumerate(new_boxes):

        x, y, w, h = [int(i) for i in box]
        
        # create a tracker
        
        tracker = cv2.TrackerKCF_create()

        # initialize the tracker
        
        tracker.init(frame, (x, y, w, h))

        # add the tracker to the list
        
        video.trackers.append(tracker)

        # fish id
        
        fish_id += 1
        
        # draw the box
        
        #cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), int(2/video.scale))
        
        label = f"Fish {fish_id}"
            
        cv2.putText(frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5/video.scale, (0, 255, 0), int(2/video.scale))

    return frame