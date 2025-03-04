import sys
import os
import cv2
import pandas as pd
from PyQt5 import QtWidgets as widgets
from PyQt5.QtCore import Qt, QLibraryInfo, QTimer
from PyQt5.QtGui import QImage, QPixmap

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
    def __init__(self, video):
        super().__init__()
        self.video = video
        self.setSizePolicy(widgets.QSizePolicy.Expanding, widgets.QSizePolicy.Expanding)
        self.adjustSize()  # Ensures QLabel resizes properly
        self.setAlignment(Qt.AlignCenter)  # Center image in QLabel

        # make a grey image to show when no video is available
        self.original_img = QImage(640, 480, QImage.Format_RGB888)
        # timer for updating
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(1000 // 60)  # 60 FPS

    def update_frame(self):
        if not self.video.Q.empty():
            frame, frame_time = self.video.Q.get()
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
            self.adjustSize()  # Ensures QLabel resizes properly
        super().resizeEvent(event)


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
class MainWindow(widgets.QWidget):
    def __init__(self, data, video, tableColumns=3, tableRows=3):
        super().__init__()
        self.setWindowTitle("WhatFishDo")
        self.setGeometry(50, 50, 1280, 720)  # Start with a reasonable size

        # Layouts
        self.layout = widgets.QVBoxLayout(self)
        self.layout.setMenuBar(MenuBar())

        # Main Content Layout
        self.splitter = widgets.QSplitter(Qt.Horizontal)

        # Left Panel (Video)
        self.video = VideoPane(video)
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
        self.setLayout(self.layout)

    def datatoPD(self, data):
        return pd.DataFrame(data).T


# Test the UI
if __name__ == "__main__":
    data = pd.DataFrame(
        {col: [f"{col}{i}" for i in range(3)] for col in ["A", "B", "C"]}
    )
    img = cv2.imread("image.png")

    app = widgets.QApplication([])
    window = MainWindow(data, img)
    window.show()
    sys.exit(app.exec_())
