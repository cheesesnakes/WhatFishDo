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

        if detection or tracking:
            self.detect_Q = Queue(maxsize=queue_size)

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
            detect_thread = Thread(target=self.detect, daemon=True)
            detect_thread.start()

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

                    if self.detection or self.tracking:
                        self.detect_Q.put([frame, frame_time])
                    else:
                        self.Q.put([frame, frame_time])

            else:
                time.sleep(10)

                sys.stdout.write("\rQueue full")
                sys.stdout.flush()

                continue

    def detect(self):
        # get frames from the queue
        while True:
            if self.stopped:
                sys.stdout.write("Stopped detection\n")
                sys.stdout.flush()

                break

            if not self.detect_Q.empty():
                with self.lock:
                    frame, frame_time = self.detect_Q.get()

                    boxes, confidences = detect_fish(self, frame)

                    if self.tracking:
                        self.Q.put(
                            [track_fish(self, frame, boxes, confidences), frame_time]
                        )

                    else:
                        self.Q.put(
                            [draw_fish(self, frame, boxes, confidences), frame_time]
                        )

            else:
                time.sleep(10)

                sys.stdout.write("\rDetect queue empty")
                sys.stdout.flush()

                continue

    def stop(self):
        # set stop state

        self.stopped = True

        # Release resources
        self.stream.release()

        if self.detection:
            self.detect_Q.queue.clear()

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
