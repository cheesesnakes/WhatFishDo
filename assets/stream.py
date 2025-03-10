from threading import Thread, Lock
from queue import Queue
import cv2
import time
from assets.detect import load_model, detect_fish, draw_fish, track_fish
import sys


class VideoStream:
    def __init__(
        self,
        data,
        plot_id,
        sample_id,
        path,
        detection,
        tracking,
        useGPU,
        skip_seconds=10,
        queue_size=1024,
    ):
        self.stream = cv2.VideoCapture(path, cv2.CAP_FFMPEG)
        self.frame_time = 0
        self.data = data
        self.plot_id = plot_id
        self.sample_id = sample_id
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

                    frame_time = self.stream.get(cv2.CAP_PROP_POS_MSEC)

                    if not ret:
                        print(
                            f"Error: Unable to read frame from video file {self.path}"
                        )

                        self.stop()

                        break

                    if self.detection:
                        frame = self.detect(frame)

                    self.Q.put([frame, frame_time])

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

    def stop(self):
        # set stop state

        self.stopped = True

        # Release resources
        self.stream.release()

        # Clear queue
        with self.lock:
            while not self.Q.empty():
                self.Q.get()

        print("\rQueue cleared")

        return

    def skip(self, seconds):
        # skip seconds

        self.stream.set(
            cv2.CAP_PROP_POS_MSEC,
            self.frame_time + seconds * 1000,
        )

        return
