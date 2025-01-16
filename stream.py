from threading import Thread, Lock
from queue import Queue
import cv2
import time
from funcs import resize_frame, draw_rectangle, get_points, enter_data, seek

class VideoStream:
    
    def __init__(self, data, deployment_id, path, skip_seconds = 2, queue_size=128):
        self.stream = cv2.VideoCapture(path)
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
        
        while not self.stopped:
        
            with self.lock:
        
                if not self.paused:
        
                    ret, frame = self.stream.read()
                    
                    if not ret:
        
                        print("Stopped reads")
                        
                        break
        
                    self.Q.put(frame)

    def process(self, window_name="fish-behavior-video"):

        while not self.stopped:
        
            if not self.Q.empty():
                
                # get frame from the queue
                
                frame = self.Q.get()
                
                # resize the frame
                
                frame = resize_frame(frame = frame, window_name=window_name)

                # Area selection (bbox)
                
                cv2.setMouseCallback(window_name, draw_rectangle)
                
                pt1, pt2 = get_points()
                
                if pt1 and pt2:
                    
                    frame_copy = frame.copy()
                    
                    cv2.rectangle(frame_copy, pt1, pt2, (0, 255, 0), 2)
                    
                    cv2.putText(frame_copy, f"Playback Speed = {self.speed}x", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    
                    cv2.imshow(window_name, frame_copy)
                    
                    enter_data(frame=frame, data=self.data, file=self.path, deployment_id=self.deployment_id)

                else:
                    
                    cv2.putText(frame, f"Playback Speed = {self.speed}x", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    
                    cv2.imshow(window_name, frame)                 
            
                self.key_event()

            else:
                
                time.sleep(0.1)
                
                print("Queue is empty")
                
                continue
        
        if self.stopped:
    
            print("Stopped processing")
            
            return
        
        elif self.Q.full():
            
            print("Queue is full")
            
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
        
        elif key == ord(","):  # Skip backward 

            current_frame = self.stream.get(cv2.CAP_PROP_POS_FRAMES)
            
            fps = self.stream.get(cv2.CAP_PROP_FPS)
            
            frames_to_skip = int(fps * self.skip_seconds)
            
            target_frame = max(0, current_frame - frames_to_skip)
            
            self.stream.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
        
        elif key == ord("."):  # Skip backward

            current_frame = self.stream.get(cv2.CAP_PROP_POS_FRAMES)
            
            fps = self.stream.get(cv2.CAP_PROP_FPS)
            
            frames_to_skip = int(fps * self.skip_seconds)
            
            target_frame = max(0, current_frame + frames_to_skip)
            
            self.stream.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
            
        elif key == ord("["): # decrease speed
            
            self.speed = max(0.5, self.speed - 0.5)
        
        elif key == ord("]"): # increase speed
            
            self.speed = min(10, self.speed + 0.5)
        
        elif key == ord("t"): # seek
            
            seek(self.stream)
                        
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
            
        # join threads
        
        for thread in self.threads:
            
            thread.join()
            
        return 