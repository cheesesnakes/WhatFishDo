from threading import Thread, Lock
from queue import Queue
import cv2
import time
from funcs import draw_rectangle, get_points
from data import enter_data

class VideoStream:
    
    def __init__(self, data, deployment_id, path, skip_seconds = 2, queue_size=512):
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

        if not self.stream.isOpened():
            print(f"Error: Unable to open video file {path}")

    def start(self):
        
        # Create and track threads
        read_thread = Thread(target=self.read, daemon=True)
        process_thread = Thread(target=self.process, daemon=True)
        
        self.threads.extend([read_thread, process_thread])
        
        # Start threads
        read_thread.start()
        process_thread.start()
        
        return self
        
    def read(self):
        
        while True:
            
            if self.stopped:
                
                print("Stopped reads")
                
                return
            
            if not self.Q.full():
                
                with self.lock:
                        
                    ret, frame = self.stream.read()
            
                    
                    if not ret:

                        print(f"Error: Unable to read frame from video file {self.path}")
                        
                        self.stop()
                        
                        return
                    
                    self.Q.put(frame)
                
            else:
                
                time.sleep(10)
                
                print("Queue is full")
                
                continue

    def process(self, window_name="fish-behavior-video"):

        while not self.stopped:
        
            if not self.Q.empty() and not self.paused:
                
                # get frame from the queue
                
                frame = self.Q.get()
                
                # create window
                
                cv2.namedWindow("fish-behavior-video", cv2.WINDOW_NORMAL)
        
                # Area selection (bbox)
                
                cv2.setMouseCallback(window_name, draw_rectangle)
                
                pt1, pt2 = get_points()
                
                if pt1 and pt2:
                    
                    frame_copy = frame.copy()
                    
                    cv2.rectangle(frame_copy, pt1, pt2, (0, 255, 0), 2)
                    
                    cv2.putText(frame_copy, f"Playback Speed = {self.speed}x", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    
                    cv2.imshow(window_name, frame_copy)
                    
                    enter_data(frame=frame, data=self.data, file=self.path, deployment_id=self.deployment_id, video=self.stream)

                else:
                    
                    cv2.putText(frame, f"Playback Speed = {self.speed}x", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    
                    cv2.imshow(window_name, frame)                 
            
                self.key_event()
    
            else:
                
                if self.paused:
                    
                    while self.paused:
                        
                        time.sleep(0.1)
                        
                        self.key_event()
                        
                    continue
                
                print("Buffering...")
                
                time.sleep(0.2)
                
                continue
        
        if self.stopped:
    
            print("Stopped processing")
            
            return
            
        else:
            
            print("Something went wrong")
            
            exit(1)
    
    def key_event(self):
        
        # handle key presses
        
        key = cv2.waitKey(int(1000/(self.fps*self.speed))) & 0xFF
        
        # key press logic
    
        if key == ord("q"): #quit
            
            print("Quitting...")
            
            self.stop()
            
        elif key == ord(" "): #pause
            
            self.paused = not self.paused
            
            if self.paused:
                
                print("Paused")
            
            else:
                
                print("Resumed")
        
        elif key == ord(","):  # Skip backward 

            self.seek(-self.skip_seconds)
        
        elif key == ord("."):  # Skip backward

            self.seek(self.skip_seconds)
            
        elif key == ord("["): # decrease speed
            
            self.speed = max(0.5, self.speed - 0.5)
        
        elif key == ord("]"): # increase speed
            
            self.speed = min(10, self.speed + 0.5)
        
        elif key == ord("t"): # seek
            
            seek_time = input("Enter time in seconds: ")
            
            seek_time = int(seek_time)
            
            self.seek(seek_time)
    
    def seek(self, seconds):
            
        with self.lock:
        
            # Clear queue
            while not self.Q.empty():
            
                self.Q.get()
        
            current_frame = self.stream.get(cv2.CAP_PROP_POS_FRAMES)
            
            fps = self.stream.get(cv2.CAP_PROP_FPS)
            
            frames_to_skip = int(fps * seconds)
            
            target_frame = current_frame + frames_to_skip
            
            self.stream.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
                            
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