import json
import sys
import os
from tkinter import N
import cv2
import pandas as pd
from PyQt5 import QtWidgets as widgets
from PyQt5.QtCore import Qt, QLibraryInfo, QTimer
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen
from assets.data import enter_data, time_out, predators, record_behaviour

os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = QLibraryInfo.location(
    QLibraryInfo.PluginsPath
)


# Define table class
class Datatable(widgets.QTableWidget):
    def __init__(self, data, columns=3, rows=3):
        super().__init__(rows, columns)
        self.setHorizontalHeaderLabels(data.columns)
        if not data.empty:
            self.populate_table(data, rows, columns)
        self.horizontalHeader().setSectionResizeMode(widgets.QHeaderView.Stretch)

    def populate_table(self, data, rows, columns):
        for i in range(rows):
            for j in range(columns):
                self.setItem(i, j, widgets.QTableWidgetItem(str(data.iloc[i, j])))


# Define video class
class VideoPane(widgets.QLabel):
    def __init__(self, video, project_info, status_bar):
        super().__init__()
        self.stream = video
        self.status_bar = status_bar

        # Create a widget for the status bar
        status_widget = widgets.QWidget()
        status_layout = widgets.QHBoxLayout(status_widget)
        status_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins

        # Add widgets to the status layout
        self.cursor_label = widgets.QLabel("X: 0, Y: 0")
        self.time_label = widgets.QLabel("00:00:00")
        self.status_label = widgets.QLabel("Ready")
        self.obs_label = widgets.QLabel("None")
        self.speed_label = widgets.QLabel("Speed: 1")

        status_layout.addWidget(self.cursor_label)
        status_layout.addWidget(self.time_label)
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.obs_label)
        status_layout.addWidget(self.speed_label)

        # Add the status widget to the status bar
        self.status_bar.addPermanentWidget(status_widget)

        self.speed = 1

        self.MouseX = 0
        self.MouseY = 0
        self.setMouseTracking(True)

        self.pt1 = None
        self.pt2 = None
        self.drawing = False

        self.loadBehaviour(project_info)
        self.loadsSize(project_info)

        self.setSizePolicy(widgets.QSizePolicy.Expanding, widgets.QSizePolicy.Expanding)
        self.adjustSize()
        self.setAlignment(Qt.AlignCenter)  # type: ignore

        # Placeholder image before video starts
        self.original_img = QImage(640, 480, QImage.Format_RGB888)

        # Timer for updating video frames

        if video is not None:
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.update_frame)
            self.timer.start(1000 // (60 * self.speed))  # 60 FPS refresh rate

            self.grabKeyboard()

    def update_frame(self):
        if not self.stream.Q.empty() and not self.stream.paused:
            frame, self.stream.frame_time = self.stream.Q.get()

            self.current_frame = frame

            # data entry
            if self.pt1 and self.pt2 and not self.drawing:
                # calculate position and size of rectangle based on curent Qlabel size

                pt1 = (  # Top left corner
                    int(self.pt1.x() / self.width() * frame.shape[1]),
                    int(self.pt1.y() / self.height() * frame.shape[0]),
                )

                pt2 = (  # Bottom right corner
                    int(self.pt2.x() / self.width() * frame.shape[1]),
                    int(self.pt2.y() / self.height() * frame.shape[0]),
                )

                # Draw rectangle on frame
                cv2.rectangle(
                    frame,
                    pt1,
                    pt2,
                    (0, 255, 0),
                    2,
                )

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

    def calculate_time(self):
        time = self.stream.frame_time

        # conver milliseconds into hours, minutes and seconds

        hours = int(time // (60 * 60 * 1000))
        minutes = int((time % (60 * 60 * 1000)) // (60 * 1000))
        seconds = int((time % (60 * 1000)) // 1000)
        milliseconds = round((time % 1000), 1)

        # display as HH:MM:SS

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
        """Record the position of the mouse when clicked"""

        self.grabKeyboard()

        self.pt1 = event.pos()
        self.pt2 = event.pos()
        self.drawing = True
        self.update()

    def mouseMoveEvent(self, event):
        """Track mouse movements when in video pane"""
        if self.drawing:
            self.pt2 = event.pos()
            self.update()
        self.MouseX = event.x()
        self.MouseY = event.y()
        self.cursor_label.setText(f"X: {self.MouseX}, Y: {self.MouseY}")

    def mouseReleaseEvent(self, event):
        """Record the position of the mouse when released"""
        self.pt2 = event.pos()

        self.drawing = False
        self.update()

    def paintEvent(self, event):
        """Draw a rectangle on the video pane"""

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
            # slow down video
            self.speed = max(0.5, self.speed - 0.5)
            self.timer.setInterval(1000 // int(60 * self.speed))
            self.speed_label.setText(f"Speed: {self.speed}")

        elif event.key() == Qt.Key_K:
            # speed up video
            self.speed = min(4, self.speed + 0.5)
            self.timer.setInterval(1000 // int(60 * self.speed))
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

        # record behaviour
        else:
            # convert key to string
            key = event.text()

            # check if key is in behaviours

            if key in self.behaviors.keys():
                record_behaviour(self.stream, key, self.obs_label, self.behaviors)

        self.update()


# Define menu class
class MenuBar(widgets.QMenuBar):
    def __init__(self):
        super().__init__()
        file_menu = self.addMenu("Exit")

        exit_action = widgets.QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(widgets.qApp.quit)
        file_menu.addAction(exit_action)

        self.addMenu("Edit")
        self.addMenu("View")


# Define main window class
class MainWindow(widgets.QMainWindow):  # Inherit from QMainWindow
    def __init__(self, project_info, data, video, tableColumns=3, tableRows=3):
        super().__init__()
        self.setWindowTitle("WhatFishDo")
        self.setGeometry(50, 50, 1280, 720)

        # Set central widget
        central_widget = widgets.QWidget()
        self.setCentralWidget(central_widget)

        # Layouts
        self.layout = widgets.QVBoxLayout(central_widget)
        self.setMenuBar(MenuBar())

        # Status Bar
        self.status_bar = self.statusBar()

        # Main Content Layout
        self.splitter = widgets.QSplitter(Qt.Horizontal)

        # Left Panel (Video)
        self.video = VideoPane(video, project_info, self.status_bar)
        self.splitter.addWidget(self.video)

        # Right Panel (Tables)
        self.data = self.datatoPD(data)
        table_container = widgets.QVBoxLayout()
        self.tab1 = Datatable(self.data, tableColumns, tableRows)
        self.tab2 = Datatable(self.data, tableColumns, tableRows)
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

    def datatoPD(self, data):
        return pd.DataFrame(data).T
