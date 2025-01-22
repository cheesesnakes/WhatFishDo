from threading import Thread, Lock
from queue import Queue
import cv2
import time
from funcs import draw_rectangle, get_points, seek
from data import enter_data, time_out, predators
from detect import load_model, detect_fish, draw_fish, track_fish
import sys
import itertools

class VideoStream:
    
    def __init__(self, data, deployment_id, path, detection, tracking, useGPU, skip_seconds = 2, queue_size=1024, scale = 2):
        self.stream = cv2.VideoCapture(path, cv2.CAP_FFMPEG)
        self.data = data
        self.deployment_id = deployment_id
        self.path = path
        self.skip_seconds = skip_seconds
        self.threads = []
        self.stopped = False
        self.paused = False
        self.speed = 1
        self.lock = Lock()
        self.fps = self.stream.get(cv2.CAP_PROP_FPS)
        self.Q = Queue(maxsize=queue_size)
        self.width = int(self.stream.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.stream.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.trackers = []
        self.scale = scale
        
        # switches
        
        self.detection = detection
        self.tracking = tracking
        self.useGPU = useGPU
        
        if not self.stream.isOpened():
            print(f"Error: Unable to open video file {path}")
    

    def start(self):
        
        if self.detection:
            
            # load model
        
            load_model(self)
        
        
        # Create and track threads
        read_thread = Thread(target=self.read, daemon=True)
        read_thread.start()
        
        
        return self
        
    def read(self):
        
        
        while True:
            
            if self.stopped:
                
                sys.stdout.write("Stopped reads\n")
                sys.stdout.flush()
                
                break
            
            if not self.Q.full():
                
                with self.lock:
                        
                    ret, frame = self.stream.read()
            
                    # resize the frame
                    if self.scale != 1:
                        
                        if self.useGPU:
                            
                            gpu_frame = cv2.cuda_GpuMat()
                            gpu_frame.upload(frame)
                            gpu_frame = cv2.cuda.resize(gpu_frame, (int(self.width/self.scale), int(self.height/self.scale)))
                            frame = gpu_frame.download()
                        
                        else:
    
                            frame = cv2.resize(frame, (int(self.width/self.scale), int(self.height/self.scale)))
                        
                    if not ret:

                        print(f"Error: Unable to read frame from video file {self.path}")
                        
                        self.stop()
                        
                        break
                    
                    if self.detection:
                        
                        frame = self.detect(frame)
                    
                    self.Q.put(frame)
                
            else:
                
                time.sleep(10)
                
                sys.stdout.write("\rQueue full")
                sys.stdout.flush()
                
                continue
    
    def detect(self, frame):
            
        # detect fish
        
        boxes, confidences = detect_fish(self, frame)
        
        # draw fish
        
        if self.tracking:
                    
            frame = track_fish(self, frame, boxes, confidences)
        
        else:
            
            frame = draw_fish(self, frame, boxes, confidences)
            
        return frame
        
    def process(self, window_name="fish-behavior-video"):

        spinner = itertools.cycle(['|', '/', '-', '\\'])
        pause_indicator = itertools.cycle(['|', '||'])
        
        while not self.stopped:
            
            if not self.Q.empty() and self.Q.qsize() > 10 and not self.paused:
                
                sys.stdout.write('\rPlaying   ' + next(spinner))
                
                # get frame from the queue
                
                frame = self.Q.get()
                                
                # create window
                
                cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
                
                # Area selection (bbox)
                
                cv2.setMouseCallback(window_name, draw_rectangle)
                
                pt1, pt2 = get_points()
                
                if pt1 and pt2:
                    
                    frame_copy = frame.copy()
                    
                    cv2.rectangle(frame_copy, pt1, pt2, (255, 0, 0), 2)
                    
                    cv2.putText(frame_copy, f"Playback Speed = {self.speed}x", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1/self.scale, (20, 10, 10), int(4/self.scale))
                    
                    cv2.imshow(window_name, frame_copy)
                    
                    enter_data(frame=frame, data=self.data, file=self.path, deployment_id=self.deployment_id, video=self.stream)

                else:
                    
                    cv2.putText(frame, f"Playback Speed = {self.speed}x", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1/self.scale, (20,10,10), int(4/self.scale))
                    
                    # get the last fish id
                    
                    fish_id = list(self.data.keys())[-1]
                    
                     # fish alert
    
                    if self.data[fish_id]['time_out'] == 0:
                        
                        cv2.putText(frame, 
                            f"Observing Fish {fish_id} - Species: {self.data[fish_id]['species']}, Size: {self.data[fish_id]['size_class']}cm", 
                            (self.width - 2000, 30), cv2.FONT_HERSHEY_SIMPLEX, 1/self.scale, (50, 10, 10), int(4/self.scale))
                    else:                
                        
                        cv2.putText(frame, 
                        f"{self.data[fish_id]['species']} has been recorded from {round(self.data[fish_id]['time_in'], 2)} to {round(self.data[fish_id]["time_out"], 2)}", 
                        (self.width - 2000, 30), cv2.FONT_HERSHEY_SIMPLEX, 1/self.scale, (50, 10, 10), int(4/self.scale))
                    
                    
                    cv2.imshow(window_name, frame)                 
            
                self.key_event()
                 
            else:
                
                if self.paused:
                    
                    while self.paused:
                        
                        sys.stdout.write('Paused ' + next(pause_indicator) + ' ' * 10)
                        
                        sys.stdout.flush()
                        
                        time.sleep(0.2)
                        
                        sys.stdout.write('\r')
                        
                        self.key_event()
                        
                    continue
                
                # spinner
                
                sys.stdout.write('\rBuffering ' + next(spinner))
                
                sys.stdout.flush()
                
                time.sleep(0.1)
                
                sys.stdout.write('\r')
                
                continue
        
        if self.stopped:
    
            sys.stdout.write("Stopped processing")
            
            sys.stdout.flush()
            
            return
            
        else:
            
            sys.stdout.write("Something went wrong")
            
            sys.stdout.flush()
            
            exit(1)
    
    def key_event(self):
        
        # handle key presses
        
        key = cv2.waitKey(int(1000/(self.fps*self.speed))) & 0xFF
        
        # key press logic
    
        if key == ord("q"): #quit
            
            sys.stdout.write("\rQuitting...\n")
            sys.stdout.flush()
            
            self.stop()
            
        elif key == ord(" "): #pause
            
            self.paused = not self.paused
        
        elif key == ord(","):  # Skip backward 

            self.seek(-self.skip_seconds)
        
        elif key == ord("."):  # Skip backward

            self.seek(self.skip_seconds)
            
        elif key == ord("["): # decrease speed
            
            self.speed = max(0.5, self.speed - 0.5)
        
        elif key == ord("]"): # increase speed
            
            self.speed = min(10, self.speed + 0.5)
        
        elif key == ord("t"): # seek
            
            with self.lock:

                # Clear queue
                while not self.Q.empty():
            
                    self.Q.get()
                
                seek(self)
                
        elif key == ord("z"): #time out
            
            time_out(self)
            
        elif key == ord("p"): # predators
            
            predators(self)
                                    
    def stop(self):
        
        # set stop state
        
        self.stopped = True
        
        # Release resources
        self.stream.release()
        
        # destroy windows
        
        cv2.destroyAllWindows()
        
        # Clear queue
        while not self.Q.empty():
            
            self.Q.get()
                
        print("Queue cleared")
                
        return 