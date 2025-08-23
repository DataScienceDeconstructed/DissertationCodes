import sys
import os
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QPushButton, QVBoxLayout,
                             QHBoxLayout, QFileDialog, QLabel, QComboBox, QSlider, QCheckBox)
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt

class DensityExplorer(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("4D Density Explorer (Two Files)")

        self.data1 = None
        self.data2 = None

        self.fig, self.axes = plt.subplots(2, 4, figsize=(16, 8))
        self.canvas = FigureCanvas(self.fig)

        # File 1 Controls
        load_btn1 = QPushButton("Load File 1")
        load_btn1.clicked.connect(lambda: self.load_file(1))
        self.type_combo1 = QComboBox()
        self.type_combo1.addItems(["linear", "log"])
        self.axis_combo1 = QComboBox()
        self.axis_combo1.addItems(["X", "Y", "Z", "T"])
        self.slider1 = QSlider(Qt.Horizontal)
        self.slider1.valueChanged.connect(lambda: self.update_slice(1))

        # File 1 Variable Labels
        self.file1_labels = {var: QLabel(f"{var} = missing") for var in ["Umin", "rad", "den", "gap", "len", "NP"]}

        # File 2 Controls
        load_btn2 = QPushButton("Load File 2")
        load_btn2.clicked.connect(lambda: self.load_file(2))
        self.type_combo2 = QComboBox()
        self.type_combo2.addItems(["linear", "log"])
        self.axis_combo2 = QComboBox()
        self.axis_combo2.addItems(["X", "Y", "Z", "T"])
        self.slider2 = QSlider(Qt.Horizontal)
        self.slider2.valueChanged.connect(lambda: self.update_slice(2))

        # File 2 Variable Labels
        self.file2_labels = {var: QLabel(f"{var} = missing") for var in ["Umin", "rad", "den", "gap", "len", "NP"]}

        # Sync Checkbox
        self.sync_checkbox = QCheckBox("Sync Controls")
        self.sync_checkbox.stateChanged.connect(self.toggle_sync)

        # Layouts
        layout = QVBoxLayout()

        # File 1 Layout
        f1_controls = QVBoxLayout()
        f1_controls.addWidget(load_btn1)
        f1_controls.addWidget(QLabel("Scale:"))
        f1_controls.addWidget(self.type_combo1)
        f1_controls.addWidget(QLabel("Slice Axis:"))
        f1_controls.addWidget(self.axis_combo1)
        for lbl in self.file1_labels.values():
            f1_controls.addWidget(lbl)
        f1_controls.addWidget(self.slider1)

        # File 2 Layout
        f2_controls = QVBoxLayout()
        f2_controls.addWidget(load_btn2)
        f2_controls.addWidget(QLabel("Scale:"))
        f2_controls.addWidget(self.type_combo2)
        f2_controls.addWidget(QLabel("Slice Axis:"))
        f2_controls.addWidget(self.axis_combo2)
        for lbl in self.file2_labels.values():
            f2_controls.addWidget(lbl)
        f2_controls.addWidget(self.slider2)

        controls_layout = QHBoxLayout()
        controls_layout.addLayout(f1_controls)
        controls_layout.addWidget(self.sync_checkbox)
        controls_layout.addLayout(f2_controls)

        layout.addLayout(controls_layout)
        layout.addWidget(self.canvas)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def parse_variables_from_path(self, filepath):
        variables = {"Umin": "missing", "rad": "missing", "den": "missing",
                     "gap": "missing", "len": "missing", "NP": "missing"}

        path_parts = os.path.normpath(filepath).split(os.sep)
        for part in path_parts:
            if "_" in part:
                name, value = part.split("_", 1)
                if name in variables:
                    variables[name] = value
        return variables

    def update_variable_labels(self, variables, label_widgets):
        for name, label in label_widgets.items():
            label.setText(f"{name} = {variables[name]}")

    def load_file(self, file_number):
        filepath, _ = QFileDialog.getOpenFileName(self, "Open File", "", "NumPy/Dat Files (*.npy *.dat)")
        if not filepath:
            return

        try:
            data = np.load(filepath)
        except Exception as e:
            print(f"Error loading file: {e}")
            return

        variables = self.parse_variables_from_path(filepath)

        if file_number == 1:
            self.data1 = data
            self.slider1.setMaximum(data.shape[0] - 1)
            self.update_variable_labels(variables, self.file1_labels)
            self.update_plots(1)
        else:
            self.data2 = data
            self.slider2.setMaximum(data.shape[0] - 1)
            self.update_variable_labels(variables, self.file2_labels)
            self.update_plots(2)

    def toggle_sync(self, state):
        if state == Qt.Checked:
            # Sync axis and slider values
            self.axis_combo2.setCurrentIndex(self.axis_combo1.currentIndex())
            self.slider2.setValue(self.slider1.value())

            # Disable second controls
            self.axis_combo2.setEnabled(False)
            self.slider2.setEnabled(False)

            # Connect File 1 controls to update File 2
            self.axis_combo1.currentIndexChanged.connect(self.sync_axis)
            self.slider1.valueChanged.connect(self.sync_slider)

        else:
            # Enable second controls again
            self.axis_combo2.setEnabled(True)
            self.slider2.setEnabled(True)

            try:
                self.axis_combo1.currentIndexChanged.disconnect(self.sync_axis)
                self.slider1.valueChanged.disconnect(self.sync_slider)
            except TypeError:
                pass

    def sync_axis(self):
        self.axis_combo2.setCurrentIndex(self.axis_combo1.currentIndex())
        self.update_slice(2)

    def sync_slider(self):
        self.slider2.setValue(self.slider1.value())
        self.update_slice(2)

    def update_plots(self, file_number):
        if file_number == 1 and self.data1 is None:
            return
        if file_number == 2 and self.data2 is None:
            return

        data = self.data1 if file_number == 1 else self.data2
        row = 0 if file_number == 1 else 1

        for ax in self.axes[row]:
            ax.clear()

        # Summation plots
        for i, axis in enumerate(range(3)):
            summed = np.sum(data, axis=axis)
            self.axes[row][i].imshow(summed, aspect='auto')
            self.axes[row][i].set_title(f"Sum over axis {axis}")

        # Slice plot
        self.update_slice(file_number)

        self.canvas.draw()

    def update_slice(self, file_number):
        if file_number == 1 and self.data1 is None:
            return
        if file_number == 2 and self.data2 is None:
            return

        data = self.data1 if file_number == 1 else self.data2
        axis_combo = self.axis_combo1 if file_number == 1 else self.axis_combo2
        slider = self.slider1 if file_number == 1 else self.slider2
        row = 0 if file_number == 1 else 1

        axis = axis_combo.currentIndex()
        idx = slider.value()

        slicer = [slice(None)] * data.ndim
        slicer[axis] = idx
        slice_data = data[tuple(slicer)]

        self.axes[row][3].imshow(slice_data, aspect='auto')
        self.axes[row][3].set_title(f"Slice {axis}={idx}")

        self.canvas.draw()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    explorer = DensityExplorer()
    explorer.show()
    sys.exit(app.exec_())
