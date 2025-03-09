import json
import sys
import os
import cv2
import time
import pandas as pd
from PyQt5 import QtWidgets as widgets
from PyQt5.QtCore import Qt, QLibraryInfo, QTimer
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen, QFont
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
        self.setWindowTitle("Sample End")
        layout = widgets.QVBoxLayout()
        self.next = widgets.QPushButton("Next")
        self.cancel = widgets.QPushButton("Cancel")
        layout.addWidget(self.next)
        layout.addWidget(self.cancel)
        self.next.clicked.connect(self.accept)
        self.cancel.clicked.connect(self.reject)
        self.setLayout(layout)


class VideoPane(widgets.QLabel):
    def __init__(self, main_window):
        super().__init__()

        self.main_window = main_window
        self.project_info = main_window.project_info
        self.stream_properties = main_window.stream_properties
        self.status_bar = main_window.status_bar

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

        self.loadBehaviour()
        self.loadsSize()

        if self.project_info is not None:
            self.start_stream()
        else:
            self.stream = None
            self.quque = None

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

    def session(self):
        project_info = self.project_info

        sample_id = None
        plot = None
        file = None
        data = {}

        # load data file
        data_file = project_info["data_file"]

        if os.path.exists(data_file):
            with open(data_file, "r") as f:
                data = json.load(f)

        if project_info["type"] == "Individual":
            last_ind = list(data.keys())[-1]
            file = data[last_ind]["file"]
            sample_id = data[last_ind]["plot_id"]
        else:
            # find next pending sample
            if project_info["sample_n"] > 0:
                for plot in project_info["samples"].keys():
                    for sample in project_info["samples"][plot].keys():
                        if project_info["samples"][plot][sample]["status"] == "pending":
                            file = project_info["samples"][plot][sample]["video"]
                            plot = plot
                            sample_id = sample
                            break

        return file, data, plot, sample_id

    def start_stream(self, queue=None):
        stream_properties = self.stream_properties

        if queue is None:
            file, data, plot, sample_id = self.session()
            self.quque = (plot, sample_id)
        else:
            plot, sample_id = queue

            file = self.project_info["samples"][plot][sample_id]["video"]
            data = {}
            with open(self.project_info["data_file"], "r") as f:
                data = json.load(f)

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
            ).start()

            sys.stdout.write("\rInitialised.    ")
            sys.stdout.flush()

            # get sample start time

            if sample_id is not None:
                sys.stdout.write("\rSearching for last fish...")
                sys.stdout.flush()

                start_time = self.project_info["samples"][plot][sample_id]["start_time"]

                # clear queue and set stream to start time
                with self.stream.lock:
                    while not self.stream.Q.empty():
                        self.stream.Q.get()

                    self.stream.stream.set(cv2.CAP_PROP_POS_MSEC, start_time * 1000)

                sys.stdout.write("\rFound last fish!!!              ")
                sys.stdout.flush()
                time.sleep(0.5)
                sys.stdout.write("\r")
                sys.stdout.flush()

            # start timer

            if self.stream is not None:
                self.timer = QTimer(self)
                self.timer.timeout.connect(self.update_frame)
                self.timer.start(1000 // (FPS * self.speed))
                self.grabKeyboard()

            # show video

            self.update_frame()

            # pause video

            self.stream.paused = True

    def update_frame(self):
        if not self.stream.Q.empty() and not self.stream.paused:
            # check if sample has ended
            self.sample_queue()

            # set frames

            frame, self.stream.frame_time = self.stream.Q.get()

            self.current_frame = frame

            # check if rectangle is drawn

            if self.pt1 and self.pt2 and not self.drawing:
                # get points and draw
                pt1 = (
                    int(self.pt1.x() / self.width() * frame.shape[1]),
                    int(self.pt1.y() / self.height() * frame.shape[0]),
                )
                pt2 = (
                    int(self.pt2.x() / self.width() * frame.shape[1]),
                    int(self.pt2.y() / self.height() * frame.shape[0]),
                )

                # fix start and end points

                pt1 = (min(pt1[0], pt2[0]), min(pt1[1], pt2[1]))
                pt2 = (max(pt1[0], pt2[0]), max(pt1[1], pt2[1]))

                cv2.rectangle(frame, pt1, pt2, (0, 255, 0), 2)

                # pause the video
                self.stream.paused = True

                # enter data

                with self.stream.lock:
                    self.releaseKeyboard()

                    enter_data(
                        frame=frame,
                        data=self.stream.data,
                        sizes=self.sizes,
                        file=self.stream.path,
                        deployment_id=self.stream.sample_id,
                        video=self.stream,
                        coordinates=(pt1[0], pt1[1], pt2[0], pt2[1]),
                        status_bar=self.obs_label,
                    )

                    self.main_window.update_tables()

                # rest
                self.pt1 = None
                self.pt2 = None
                self.grabKeyboard()

            # scale and add frame to video pane

            qt_img = self.cv_to_qt(frame)
            self.original_img = qt_img
            scaled_img = qt_img.scaled(
                self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.setPixmap(QPixmap.fromImage(scaled_img))
            self.adjustSize()

            # update status bar
            formatted_time = self.calculate_time()
            self.time_label.setText(formatted_time)
            self.status_label.setText("Playing")
        elif self.stream.Q.empty() and not self.stream.paused:
            self.status_label.setText("Buffering")

    def sample_queue(self):
        # check if video is running

        if self.stream is not None:
            current_time = self.stream.frame_time / 1000
            plot = self.stream.plot_id
            sample_id = self.stream.sample_id
            end_time = (
                self.project_info["samples"][plot][sample_id]["start_time"]
                + self.project_info["sample_s"]
            )

            # check if sample has ended
            if current_time >= end_time:
                # prompt user to end sample
                sample_prompt = samplePrompt()
                sample_prompt.exec_()

                if sample_prompt.result() == 1:
                    # load next sample
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

    def loadBehaviour(self):
        project_info = self.project_info
        if project_info is not None:
            with open(project_info["behaviour_file"], "r") as f:
                self.behaviours = json.load(f)

    def loadsSize(self):
        project_info = self.project_info
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
            self.main_window.update_tables()
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
                self.main_window.update_tables()

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
            self.main_window.video = VideoPane(self.main_window)
            self.main_window.splitter.replaceWidget(0, self.main_window.video)

            self.main_window.update_tables()

    def load_project(self):
        dialog = projectDialog()
        dialog.exec_()
        if dialog.result() == 1:
            self.main_window.project_info = dialog.project_info
            self.main_window.video = VideoPane(self.main_window)
            self.main_window.splitter.replaceWidget(0, self.main_window.video)

            self.main_window.update_tables()

    def load_video(self):
        dialog = widgets.QFileDialog()
        dialog.setFileMode(widgets.QFileDialog.ExistingFile)
        dialog.exec_()
        file = dialog.selectedFiles()
        if file:
            self.main_window.video.stream.path = file
            self.main_window.video.start()
            self.main_window.update_frame()
            self.main_window.video.stream.paused = True

            self.main_window.update_tables()

    def save_project(self):
        dialog = widgets.QFileDialog()
        dialog.setFileMode(widgets.QFileDialog.AnyFile)
        dialog.exec_()
        file = dialog.selectedFiles()[0]
        if file:
            with open(file, "w") as f:
                json.dump(self.main_window.project_info, f)

    def sample_next(self):
        if self.main_window.project_info is None:
            dialog = widgets.QMessageBox()
            dialog.setText("No project loaded")
            dialog.exec_()

            return

        queue = self.main_window.video.quque

        self.main_window.video.stream.stop()

        self.main_window.video.start_stream(queue)

    def sample_previous(self):
        if self.main_window.project_info is None:
            dialog = widgets.QMessageBox()
            dialog.setText("No project loaded")
            dialog.exec_()

            return

        queue = self.main_window.video.quque

        if queue is not None:
            plot, sample_id = queue

            # find sample id

            sample_ids = list(self.main_window.project_info["samples"][plot].keys())
            sample_index = sample_ids.index(sample_id)

            if sample_index > 0:
                sample_id = sample_ids[sample_index - 1]

                self.main_window.video.stream.stop()
                self.main_window.video.start_stream((plot, sample_id))
        else:
            dialog = widgets.QMessageBox()
            dialog.setText("No sample loaded")
            dialog

    def load_sample(self):
        if self.main_window.project_info is None:
            dialog = widgets.QMessageBox()
            dialog.setText("No project loaded")
            dialog.exec_()

            return

        dialog = widgets.QDialog()
        dialog.setWindowTitle("Load Sample")
        dialog.setGeometry(400, 400, 800, 800)
        layout = widgets.QVBoxLayout()

        samples = []
        for plot in self.main_window.project_info["samples"].keys():
            for sample in self.main_window.project_info["samples"][plot].keys():
                samples.append((plot, sample))

        samples_df = pd.DataFrame(samples, columns=["Plot", "Sample ID"])

        table = behTable(samples_df)
        layout.addWidget(table)

        load_button = widgets.QPushButton("Load")
        layout.addWidget(load_button)

        def load_selected_sample():
            selected_items = table.selectedItems()
            if selected_items:
                plot = selected_items[0].text()
                sample_id = selected_items[1].text()
                self.main_window.video.stream.stop()
                self.main_window.video.start_stream((plot, sample_id))
                dialog.accept()

        load_button.clicked.connect(load_selected_sample)
        dialog.setLayout(layout)
        dialog.exec_()

    def view_data(self):
        if self.main_window.project_info is not None:
            data = self.main_window.ind_datatoPD()
            dialog = widgets.QDialog()
            dialog.setWindowTitle("Data")
            dialog.setGeometry(400, 400, 800, 800)
            layout = widgets.QVBoxLayout()
            rows = len(data)
            table = indTable(data, rows)
            layout.addWidget(table)
            dialog.setLayout(layout)
            dialog.exec_()
        else:
            dialog = widgets.QMessageBox()
            dialog.setText("No project loaded")
            dialog.exec_()

    def view_project(self):
        if self.main_window.project_info is not None:
            dialog = widgets.QDialog()
            dialog.setWindowTitle("Project Info")
            dialog.setGeometry(400, 400, 800, 800)
            layout = widgets.QVBoxLayout()

            text = ""

            for key, value in self.main_window.project_info.items():
                if key != "samples" and key != "plot_info":
                    text += f"{key}: {value}\n"

            label = widgets.QLabel(text)
            label.setWordWrap(True)
            label.setFont(QFont("Arial", 12))
            label.setAlignment(Qt.AlignLeft)
            layout.addWidget(label)

            dialog.setLayout(layout)
            dialog.exec_()
        else:
            dialog = widgets.QMessageBox()
            dialog.setText("No project loaded")
            dialog.exec_()

    def view_behaviour(self):
        if self.main_window.project_info is not None:
            dialog = widgets.QDialog()
            dialog.setWindowTitle("Behaviours")
            dialog.setGeometry(400, 400, 800, 800)
            layout = widgets.QVBoxLayout()

            behaviours = self.main_window.video.behaviours

            behaviours = pd.DataFrame(behaviours).T

            behaviours.columns = ["Behaviour", "Type", "Description"]

            # create a table

            table = behTable(behaviours)

            layout.addWidget(table)
            dialog.setLayout(layout)
            dialog.exec_()
        else:
            dialog = widgets.QMessageBox()
            dialog.setText("No project loaded")
            dialog.exec_()

    def view_size(self):
        if self.main_window.project_info is not None:
            dialog = widgets.QDialog()
            dialog.setWindowTitle("Sizes")
            dialog.setGeometry(400, 400, 50, 400)
            layout = widgets.QVBoxLayout()

            text = ""

            for size in self.main_window.video.sizes:
                text += f"{size}, "

            label = widgets.QLabel(text)
            label.setWordWrap(True)
            label.setFont(QFont("Arial", 12))
            label.setAlignment(Qt.AlignCenter)
            layout.addWidget(label)
            dialog.setLayout(layout)
            dialog.exec_()
        else:
            dialog = widgets.QMessageBox()
            dialog.setText("No project loaded")
            dialog.exec_()


# Define main window class
class MainWindow(widgets.QMainWindow):  # Inherit from QMainWindow
    def __init__(self, project_info, stream_properties):
        super().__init__()

        self.project_info = project_info
        self.stream_properties = stream_properties

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
        self.video = VideoPane(self)
        self.splitter.addWidget(self.video)

        # Right Panel (Tables)

        if project_info is not None:
            self.ind_data = self.ind_datatoPD()
            self.beh_data = self.beh_datatoPD()
        else:
            self.ind_data = pd.DataFrame()
            self.beh_data = pd.DataFrame()

        table_container = widgets.QVBoxLayout()
        self.tab1 = indTable(self.ind_data)
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
        else:
            return pd.DataFrame()

        if len(data) == 0:
            return pd.DataFrame()

        # remove subkeys coordinates, file, and behaviour

        for key in data.keys():
            for subkey in ["coordinates", "file", "behaviour"]:
                if subkey in data[key].keys():
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
        else:
            return pd.DataFrame()

        if len(data) == 0:
            return pd.DataFrame()

        if "behaviour" not in data[list(data.keys())[-1]].keys():
            return pd.DataFrame()

        # select last individual

        last_ind = list(data.keys())[-1]

        # get behaviour data

        data = data[last_ind]["behaviour"]

        # list to dataframe

        df = pd.DataFrame(data)

        return df

    def update_tables(self):
        self.ind_data = self.ind_datatoPD()
        self.beh_data = self.beh_datatoPD()
        self.tab1 = indTable(self.ind_data)
        self.tab2 = behTable(self.beh_data)

        table_container = widgets.QVBoxLayout()
        table_container.addWidget(self.tab1)
        table_container.addWidget(self.tab2)

        table_widget = widgets.QWidget()
        table_widget.setLayout(table_container)

        self.splitter.replaceWidget(1, table_widget)
