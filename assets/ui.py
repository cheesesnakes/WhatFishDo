import json
import sys
import os
import cv2
import time
import pandas as pd
from PyQt5 import QtWidgets as widgets
from PyQt5.QtCore import Qt, QLibraryInfo, QTimer
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen
from assets.data import enter_data, time_out, predators, record_behaviour
from assets.stream import VideoStream
from assets.funcs import projectInit, projectDialog

os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = QLibraryInfo.location(
    QLibraryInfo.PluginsPath
)

# Constants
FPS = 60
DEFAULT_SPEED = 1
MAX_SPEED = 4
MIN_SPEED = 0.5
SPEED_STEP = 0.5


# Define table class
class indTable(widgets.QTableWidget):
    def __init__(self, data, rows=10):
        columns = len(data.columns)
        rows = min(rows, len(data))
        super().__init__(rows, columns)
        self.setHorizontalHeaderLabels(data.columns)
        if not data.empty:
            self.populate_table(data, rows, columns)
        self.horizontalHeader().setSectionResizeMode(widgets.QHeaderView.Stretch)

    def populate_table(self, data, rows, columns):
        for j in range(columns):
            for i in range(rows):
                self.setItem(i, j, widgets.QTableWidgetItem(str(data.iloc[i, j])))
        self.resizeColumnsToContents()


class behTable(widgets.QTableWidget):
    def __init__(self, data, rows=10):
        columns = len(data.columns)
        rows = min(rows, len(data))
        super().__init__(rows, columns)
        self.setHorizontalHeaderLabels(data.columns)
        if not data.empty:
            self.populate_table(data, rows, columns)
        self.horizontalHeader().setSectionResizeMode(widgets.QHeaderView.Stretch)

    def populate_table(self, data, rows, columns):
        for j in range(columns):
            for i in range(rows):
                self.setItem(i, j, widgets.QTableWidgetItem(str(data.iloc[i, j])))
        self.resizeColumnsToContents()


class samplePrompt(widgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sample Ennder")
        layout = widgets.QVBoxLayout()
        self.next = widgets.QPushButton("Next")
        self.cancel = widgets.QPushButton("Cancel")
        layout.addWidget(self.next)
        layout.addWidget(self.cancel)
        self.next.clicked.connect(self.accept)
        self.cancel.clicked.connect(self.reject)
        self.setLayout(layout)


class VideoPane(widgets.QLabel):
    def __init__(self, project_info, stream_properties, status_bar):
        super().__init__()
        self.project_info = project_info
        self.stream_properties = stream_properties
        self.status_bar = status_bar
        self.speed = DEFAULT_SPEED
        self.MouseX = 0
        self.MouseY = 0
        self.pt1 = None
        self.pt2 = None
        self.drawing = False
        self.setMouseTracking(True)
        self.setSizePolicy(widgets.QSizePolicy.Expanding, widgets.QSizePolicy.Expanding)
        self.adjustSize()
        self.setAlignment(Qt.AlignCenter)
        self.original_img = QImage(640, 480, QImage.Format_RGB888)
        self.init_status_bar()
        self.loadBehaviour(project_info)
        self.loadsSize(project_info)
        self.start_stream(stream_properties)
        if self.stream is not None:
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.update_frame)
            self.timer.start(1000 // (FPS * self.speed))
            self.grabKeyboard()

    def init_status_bar(self):
        status_widget = widgets.QWidget()
        status_layout = widgets.QHBoxLayout(status_widget)
        status_layout.setContentsMargins(0, 0, 0, 0)
        self.cursor_label = widgets.QLabel("X: 0, Y: 0")
        self.time_label = widgets.QLabel("00:00:00")
        self.status_label = widgets.QLabel("Ready")
        self.obs_label = widgets.QLabel("None")
        self.speed_label = widgets.QLabel(f"Speed: {self.speed}")
        status_layout.addWidget(self.cursor_label)
        status_layout.addWidget(self.time_label)
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.obs_label)
        status_layout.addWidget(self.speed_label)
        self.status_bar.addPermanentWidget(status_widget)

    def session(self, next=True):
        project_info = self.project_info
        sample_id = None
        plot = None
        file = None
        data = {}
        data_file = project_info["data_file"]
        if os.path.exists(data_file):
            with open(data_file, "r") as f:
                data = json.load(f)
        if project_info["type"] == "Individual":
            last_ind = list(data.keys())[-1]
            file = data[last_ind]["file"]
            sample_id = data[last_ind]["plot_id"]
        else:
            if project_info["sample_n"] > 0:
                for plot in project_info["samples"].keys():
                    for sample in project_info["samples"][plot].keys():
                        if project_info["samples"][plot][sample]["status"] == "pending":
                            file = project_info["samples"][plot][sample]["video"]
                            plot = plot
                            sample_id = sample
                            break
        return file, data, plot, sample_id

    def start_stream(self, stream_properties):
        file, data, plot, sample_id = self.session()
        self.stream = None
        if file is not None:
            print(f"Sample: {sample_id}", f"File: {file}", sep="\n")
            sys.stdout.write("\rInitialising...")
            sys.stdout.flush()
            self.stream = VideoStream(
                data=data,
                plot_id=plot,
                sample_id=sample_id,
                path=file,
                useGPU=stream_properties["useGPU"],
                detection=stream_properties["detection"],
                tracking=stream_properties["tracking"],
                scale=stream_properties["scale"],
            ).start()
            sys.stdout.write("\rInitialised.    ")
            sys.stdout.flush()
            if sample_id is not None:
                sys.stdout.write("\rSearching for last fish...")
                sys.stdout.flush()
                start_time = self.project_info["samples"][plot][sample_id]["start_time"]
                with self.stream.lock:
                    while not self.stream.Q.empty():
                        self.stream.Q.get()
                    self.stream.stream.set(cv2.CAP_PROP_POS_MSEC, start_time * 1000)
                    sys.stdout.write("\rFound last fish!!!              ")
                    sys.stdout.flush()
                    time.sleep(0.5)
                    sys.stdout.write("\r")
                    sys.stdout.flush()
            self.update_frame()
            self.stream.paused = True

    def update_frame(self):
        if not self.stream.Q.empty() and not self.stream.paused:
            self.sample_queue()
            frame, self.stream.frame_time = self.stream.Q.get()
            self.current_frame = frame
            if self.pt1 and self.pt2 and not self.drawing:
                pt1 = (
                    int(self.pt1.x() / self.width() * frame.shape[1]),
                    int(self.pt1.y() / self.height() * frame.shape[0]),
                )
                pt2 = (
                    int(self.pt2.x() / self.width() * frame.shape[1]),
                    int(self.pt2.y() / self.height() * frame.shape[0]),
                )
                cv2.rectangle(frame, pt1, pt2, (0, 255, 0), 2)
                self.stream.paused = True
                with self.stream.lock:
                    self.releaseKeyboard()
                    enter_data(
                        frame=frame,
                        data=self.stream.data,
                        sizes=self.sizes,
                        file=self.stream.path,
                        deployment_id=self.stream.deployment_id,
                        video=self.stream,
                        coordinates=(pt1[0], pt1[1], pt2[0], pt2[1]),
                        status_bar=self.obs_label,
                    )
                self.pt1 = None
                self.pt2 = None
                self.grabKeyboard()
            qt_img = self.cv_to_qt(frame)
            self.original_img = qt_img
            scaled_img = qt_img.scaled(
                self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.setPixmap(QPixmap.fromImage(scaled_img))
            self.adjustSize()
            formatted_time = self.calculate_time()
            self.time_label.setText(formatted_time)
            self.status_label.setText("Playing")

    def sample_queue(self):
        if self.stream is not None:
            current_time = self.stream.frame_time / 1000
            plot = self.stream.plot_id
            sample_id = self.stream.sample_id
            end_time = (
                self.project_info["samples"][plot][sample_id]["start_time"]
                + self.project_info["sample_s"]
            )
            if current_time >= end_time:
                sample_prompt = samplePrompt()
                sample_prompt.exec_()
                if sample_prompt.result() == 1:
                    self.project_info["samples"][plot][sample_id]["status"] = "complete"
                    self.stream.stop()
                    self.start_stream(self.stream_properties)
                else:
                    self.stream.paused = True

    def calculate_time(self):
        time = self.stream.frame_time
        hours = int(time // (60 * 60 * 1000))
        minutes = int((time % (60 * 60 * 1000)) // (60 * 1000))
        seconds = int((time % (60 * 1000)) // 1000)
        milliseconds = round((time % 1000), 1)
        return f"{hours:02}:{minutes:02}:{seconds:02}:{milliseconds:03}"

    def cv_to_qt(self, img):
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        return QImage(img.data, img.shape[1], img.shape[0], QImage.Format_RGB888)

    def resizeEvent(self, event):
        if not self.original_img.isNull():
            scaled_img = self.original_img.scaled(
                self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.setPixmap(QPixmap.fromImage(scaled_img))
            self.adjustSize()
        super().resizeEvent(event)

    def mousePressEvent(self, event):
        self.grabKeyboard()
        self.pt1 = event.pos()
        self.pt2 = event.pos()
        self.drawing = True
        self.update()

    def mouseMoveEvent(self, event):
        if self.drawing:
            self.pt2 = event.pos()
            self.update()
        self.MouseX = event.x()
        self.MouseY = event.y()
        self.cursor_label.setText(f"X: {self.MouseX}, Y: {self.MouseY}")

    def mouseReleaseEvent(self, event):
        self.pt2 = event.pos()
        self.drawing = False
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.drawing and self.pt1 and self.pt2:
            painter = QPainter(self)
            painter.setPen(QPen(Qt.red, 2, Qt.SolidLine))
            painter.drawRect(
                self.pt1.x(),
                self.pt1.y(),
                self.pt2.x() - self.pt1.x(),
                self.pt2.y() - self.pt1.y(),
            )

    def loadBehaviour(self, project_info):
        if project_info is not None:
            with open(project_info["behaviour_file"], "r") as f:
                self.behaviours = json.load(f)

    def loadsSize(self, project_info):
        if project_info is not None:
            with open(project_info["size_file"], "r") as f:
                sizes = json.load(f)
                self.sizes = sizes["sizes"]

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space:
            self.stream.paused = not self.stream.paused
            self.status_label.setText("Paused" if self.stream.paused else "Playing")
        elif event.key() == Qt.Key_J:
            self.speed = max(MIN_SPEED, self.speed - SPEED_STEP)
            self.timer.setInterval(1000 // int(FPS * self.speed))
            self.speed_label.setText(f"Speed: {self.speed}")
        elif event.key() == Qt.Key_K:
            self.speed = min(MAX_SPEED, self.speed + SPEED_STEP)
            self.timer.setInterval(1000 // int(FPS * self.speed))
            self.speed_label.setText(f"Speed: {self.speed}")
        elif event.key() == Qt.Key_Right:
            with self.stream.lock:
                self.stream.skip(1)
        elif event.key() == Qt.Key_Left:
            with self.stream.lock:
                while not self.stream.Q.empty():
                    self.stream.Q.get()
                self.stream.skip(-1)
        elif event.key() == Qt.Key_Up:
            with self.stream.lock:
                self.stream.skip(10)
        elif event.key() == Qt.Key_Down:
            with self.stream.lock:
                while not self.stream.Q.empty():
                    self.stream.Q.get()
                self.stream.skip(-10)
        elif event.key() == Qt.Key_Z:
            time_out(self.stream, self.obs_label)
        elif event.key() == Qt.Key_P:
            predators(self.stream, self.current_frame, self.sizes, self.obs_label)
        elif event.key() == Qt.Key_C:
            self.pt1 = None
            self.pt2 = None
            self.drawing = False
            self.update()
        elif event.key() == Qt.Key_Q:
            sys.exit(0)
        else:
            key = event.text()
            if key in self.behaviours.keys():
                record_behaviour(self.stream, key, self.obs_label, self.behaviours)
        self.update()


class MenuBar(widgets.QMenuBar):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        file_menu = self.addMenu("File")
        self.add_action(file_menu, "New Project", "Ctrl+N", self.new_project)
        self.add_action(file_menu, "Load Project", "Ctrl+L", self.load_project)
        self.add_action(file_menu, "Save Project", "Ctrl+S", self.save_project)
        self.add_action(file_menu, "Load Video", "Ctrl+V", self.load_video)
        self.add_action(file_menu, "Exit", "Ctrl+Q", widgets.qApp.quit)
        sample_menu = self.addMenu("Sample")
        self.add_action(sample_menu, "Next Sample", "Ctrl+Shift+N", self.sample_next)
        self.add_action(
            sample_menu, "Previous Sample", "Ctrl+Shift+P", self.sample_previous
        )
        self.add_action(sample_menu, "Load Sample", "Ctrl+Shift+L", self.load_sample)
        view_menu = self.addMenu("View")
        self.add_action(view_menu, "View Data", "Ctrl+D", self.view_data)
        self.add_action(view_menu, "View Project Info", "Ctrl+I", self.view_project)
        self.add_action(view_menu, "View Behaviours", "Ctrl+B", self.view_behaviour)
        self.add_action(view_menu, "View Size Classes", "Ctrl+S", self.view_size)

    def add_action(self, menu, name, shortcut, method):
        action = widgets.QAction(name, self)
        action.setShortcut(shortcut)
        action.triggered.connect(method)
        menu.addAction(action)

    def new_project(self):
        dialog = projectInit()
        dialog.exec_()
        if dialog.result() == 1:
            self.main_window.project_info = dialog.project_info
            self.main_window.video = VideoPane(
                self.main_window.project_info,
                self.main_window.stream_properties,
                self.main_window.status_bar,
            )
            self.main_window.splitter.replaceWidget(0, self.main_window.video)

    def load_project(self):
        dialog = projectDialog()
        dialog.exec_()
        if dialog.result() == 1:
            self.main_window.project_info = dialog.project_info
            self.main_window.video = VideoPane(
                self.main_window.project_info,
                self.main_window.stream_properties,
                self.main_window.status_bar,
            )
            self.main_window.splitter.replaceWidget(0, self.main_window.video)

    def load_video(self):
        dialog = widgets.QFileDialog()
        dialog.setFileMode(widgets.QFileDialog.ExistingFile)
        dialog.exec_()
        file = dialog.selectedFiles()
        if file:
            self.main_window.video.stream.path = file
            self.main_window.video.start()
            self.main_window.stream.paused = True
            self.main_window.update_frame()

    def save_project(self):
        dialog = widgets.QFileDialog()
        dialog.setFileMode(widgets.QFileDialog.AnyFile)
        dialog.exec_()
        file = dialog.selectedFiles()
        if file:
            with open(file, "w") as f:
                json.dump(self.main_window.project_info, f)

    def sample_next(self):
        self.main_window.video.stream.stop()
        self.main_window.video.start_stream(self.main_window.stream_properties)

    def sample_previous(self):
        pass

    def load_sample(self):
        pass

    def view_data(self):
        data = self.main_window.ind_datatoPD()
        dialog = widgets.QDialog()
        layout = widgets.QVBoxLayout()
        rows = len(data)
        table = indTable(data, rows)
        layout.addWidget(table)
        dialog.setLayout(layout)
        dialog.exec_()

    def view_project(self):
        dialog = widgets.QDialog()
        layout = widgets.QVBoxLayout()
        for key, value in self.main_window.project_info.items():
            if key != "samples" or key != "plot_info":
                layout.addWidget(widgets.QLabel(f"{key}: {value}"))
        dialog.setLayout(layout)
        dialog.exec_()

    def view_behaviour(self):
        dialog = widgets.QDialog()
        layout = widgets.QVBoxLayout()
        for key, value in self.main_window.behaviours.items():
            layout.addWidget(widgets.QLabel(f"{key}: {value}"))
        dialog.setLayout(layout)
        dialog.exec_()

    def view_size(self):
        dialog = widgets.QDialog()
        layout = widgets.QVBoxLayout()
        for key, value in self.main_window.sizes.items():
            layout.addWidget(widgets.QLabel(f"{key}: {value}"))
        dialog.setLayout(layout)


# Define main window class
class MainWindow(widgets.QMainWindow):  # Inherit from QMainWindow
    def __init__(self, project_info, stream_properties, tableColumns=3, tableRows=3):
        super().__init__()

        self.project_info = project_info

        self.setWindowTitle("WhatFishDo")
        self.setGeometry(50, 50, 1280, 720)

        # Set central widget
        central_widget = widgets.QWidget()
        self.setCentralWidget(central_widget)

        # Layouts
        self.layout = widgets.QVBoxLayout(central_widget)
        self.setMenuBar(MenuBar(self))

        # Status Bar
        self.status_bar = self.statusBar()

        # Main Content Layout
        self.splitter = widgets.QSplitter(Qt.Horizontal)

        # Left Panel (Video)
        self.video = VideoPane(project_info, stream_properties, self.status_bar)
        self.splitter.addWidget(self.video)

        # Right Panel (Tables)
        self.ind_data = self.ind_datatoPD()
        table_container = widgets.QVBoxLayout()
        self.tab1 = indTable(self.ind_data)
        self.beh_data = self.beh_datatoPD()
        self.tab2 = behTable(self.beh_data)
        table_container.addWidget(self.tab1)
        table_container.addWidget(self.tab2)

        table_widget = widgets.QWidget()
        table_widget.setLayout(table_container)
        self.splitter.addWidget(table_widget)

        # Ensure proper resizing
        self.splitter.setStretchFactor(0, 2)  # More space to video
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setSizes([800, 480])  # Initial sizes

        self.layout.addWidget(self.splitter)

    def closeEvent(self, event):
        sys.stdout.flush()
        sys.stdout.write("\rQuitting...")

        if self.video is not None:
            if self.video.stream is not None:
                self.video.stream.pause = False
                self.video.stream.stop()

        sys.stdout.flush()

        event.accept()

    def ind_datatoPD(self):
        data = {}

        data_file = self.project_info["data_file"]

        if os.path.exists(data_file):
            with open(data_file, "r") as f:
                data = json.load(f)

        # remove subkeys coordinates, file, and behaviour

        for key in data.keys():
            for subkey in ["coordinates", "file", "behaviour"]:
                data[key].pop(subkey)

        df = pd.DataFrame.from_dict(data, orient="index")

        # rename index to individual_id

        df.index.name = "individual_id"

        # make index a column

        df.reset_index(inplace=True)

        # reorder columns

        df = df[
            [
                "individual_id",
                "species",
                "size_class",
                "time_in",
                "time_out",
                "group",
                "remarks",
            ]
        ]

        # rename columns

        df.columns = [
            "Individual ID",
            "Species",
            "Size Class",
            "Time In",
            "Time Out",
            "Group",
            "Remarks",
        ]

        return df

    def beh_datatoPD(self):
        data = {}

        data_file = self.project_info["data_file"]

        if os.path.exists(data_file):
            with open(data_file, "r") as f:
                data = json.load(f)

        # select last individual

        last_ind = list(data.keys())[-1]

        # get behaviour data

        data = data[last_ind]["behaviour"]

        # list to dataframe

        df = pd.DataFrame(data)

        return df
