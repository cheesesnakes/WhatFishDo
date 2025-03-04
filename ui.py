import sys
import os
import cv2
import pandas as pd
from PyQt5 import QtWidgets as widgets
from PyQt5.QtCore import Qt, QLibraryInfo, QTimer
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen

os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = QLibraryInfo.location(
    QLibraryInfo.PluginsPath
)


# Define table class
class Datatable(widgets.QTableWidget):
    def __init__(self, data, columns=3, rows=3):
        super().__init__(rows, columns)
        self.setHorizontalHeaderLabels(data.columns)
        self.populate_table(data, rows, columns)
        self.horizontalHeader().setSectionResizeMode(widgets.QHeaderView.Stretch)

    def populate_table(self, data, rows, columns):
        for i in range(rows):
            for j in range(columns):
                self.setItem(i, j, widgets.QTableWidgetItem(str(data.iloc[i, j])))


# Define video class
class VideoPane(widgets.QLabel):
    def __init__(self, video, status_bar):
        super().__init__()
        self.stream = video
        self.status_bar = status_bar

        self.MouseX = 0
        self.MouseY = 0
        self.setMouseTracking(True)

        self.pt1 = None
        self.pt2 = None
        self.drawing = False

        self.setSizePolicy(widgets.QSizePolicy.Expanding, widgets.QSizePolicy.Expanding)
        self.adjustSize()
        self.setAlignment(Qt.AlignCenter)

        # Placeholder image before video starts
        self.original_img = QImage(640, 480, QImage.Format_RGB888)

        # Timer for updating video frames
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(1000 // 60)  # 60 FPS refresh rate

    def update_frame(self):
        if not self.stream.Q.empty():
            frame, frame_time = self.stream.Q.get()
            qt_img = self.cv_to_qt(frame)
            self.original_img = qt_img
            scaled_img = qt_img.scaled(
                self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.setPixmap(QPixmap.fromImage(scaled_img))
            self.adjustSize()

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
        self.status_bar.showMessage(f"X: {self.MouseX}, Y: {self.MouseY}")

    def mouseReleaseEvent(self, event):
        """Record the position of the mouse when released"""

        self.pt2 = event.pos()
        self.drawing = False
        self.update()

    def paintEvent(self, event):
        """Draw a rectangle on the video pane"""

        super().paintEvent(event)
        if self.drawing:
            painter = QPainter(self)
            painter.setPen(QPen(Qt.red, 2, Qt.SolidLine))
            painter.drawRect(
                self.pt1.x(),
                self.pt1.y(),
                self.pt2.x() - self.pt1.x(),
                self.pt2.y() - self.pt1.y(),
            )


# Define menu class
class MenuBar(widgets.QMenuBar):
    def __init__(self):
        super().__init__()
        file_menu = self.addMenu("File")
        for action_text in ["New", "Open", "Save", "Save As", "Exit"]:
            action = file_menu.addAction(action_text)
            action.triggered.connect(lambda: print(f"{action_text} clicked"))
        self.addMenu("Edit")
        self.addMenu("View")


# Define main window class
class MainWindow(widgets.QMainWindow):  # Inherit from QMainWindow
    def __init__(self, data, video, tableColumns=3, tableRows=3):
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
        self.status_bar.showMessage("Ready")

        # Main Content Layout
        self.splitter = widgets.QSplitter(Qt.Horizontal)

        # Left Panel (Video)
        self.video = VideoPane(video, self.status_bar)
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

        self.video.stream.pause = False
        self.video.stream.stop()

        sys.stdout.flush()

        event.accept()

    def datatoPD(self, data):
        return pd.DataFrame(data).T
