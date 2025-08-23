import os
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QSlider, QComboBox, QCheckBox,
    QMessageBox
)
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


def parse_variables_from_path(filepath):
    variables = {"Umin": "missing", "rad": "missing", "den": "missing",
                 "gap": "missing", "len": "missing", "NP": "missing"}
    path_parts = os.path.normpath(filepath).split(os.sep)
    for part in path_parts:
        if "_" in part:
            name, value = part.split("_", 1)
            if name in variables:
                variables[name] = value
    return variables


class SliceViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("3D Data Slice Viewer")

        # data storage
        self.file1_data = None
        self.file2_data = None
        self.diff_data = None

        # sync flags
        self.sync_file2 = False
        self.sync_diff = False

        # ------------------ Main Layout ------------------
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        self.layout = QVBoxLayout(main_widget)

        # file 1
        self.file1_button = QPushButton("Load File 1")
        self.file1_button.clicked.connect(lambda: self.load_file(1))
        self.layout.addWidget(self.file1_button)

        self.file1_var_labels = {v: QLabel(f"{v} = missing") for v in ["Umin","rad","den","gap","len","NP"]}
        file1_label_row = QHBoxLayout()
        for lab in self.file1_var_labels.values():
            file1_label_row.addWidget(lab)
        self.layout.addLayout(file1_label_row)

        self.file1_axis_selector, self.file1_slider, self.file1_canvas, self.file1_lines, self.file1_slice_line = self.build_view_section("File 1 Controls")
        self.layout.addWidget(self.file1_axis_selector)
        self.layout.addWidget(self.file1_slider)
        self.layout.addWidget(self.file1_canvas)

        # file 2
        self.file2_button = QPushButton("Load File 2")
        self.file2_button.clicked.connect(lambda: self.load_file(2))
        self.layout.addWidget(self.file2_button)

        self.file2_var_labels = {v: QLabel(f"{v} = missing") for v in ["Umin","rad","den","gap","len","NP"]}
        file2_label_row = QHBoxLayout()
        for lab in self.file2_var_labels.values():
            file2_label_row.addWidget(lab)
        self.layout.addLayout(file2_label_row)

        sync_row = QHBoxLayout()
        self.file2_axis_selector, self.file2_slider, self.file2_canvas, self.file2_lines, self.file2_slice_line = self.build_view_section("File 2 Controls")
        self.file2_sync_checkbox = QCheckBox("Sync with File 1")
        self.file2_sync_checkbox.stateChanged.connect(self.toggle_sync_file2)
        sync_row.addWidget(self.file2_sync_checkbox)
        self.layout.addLayout(sync_row)

        self.layout.addWidget(self.file2_axis_selector)
        self.layout.addWidget(self.file2_slider)
        self.layout.addWidget(self.file2_canvas)

        # diff dataset
        self.diff_label = QLabel("Difference Dataset (File2 - File1)")
        self.layout.addWidget(self.diff_label)

        self.diff_var_labels = {v: QLabel(f"{v} = missing") for v in ["Umin","rad","den","gap","len","NP"]}
        diff_label_row = QHBoxLayout()
        for lab in self.diff_var_labels.values():
            diff_label_row.addWidget(lab)
        self.layout.addLayout(diff_label_row)

        diff_sync_row = QHBoxLayout()
        self.diff_axis_selector, self.diff_slider, self.diff_canvas, self.diff_lines, self.diff_slice_line = self.build_view_section("Diff Controls")
        self.diff_sync_checkbox = QCheckBox("Sync with File 1")
        self.diff_sync_checkbox.stateChanged.connect(self.toggle_sync_diff)
        diff_sync_row.addWidget(self.diff_sync_checkbox)
        self.layout.addLayout(diff_sync_row)

        self.layout.addWidget(self.diff_axis_selector)
        self.layout.addWidget(self.diff_slider)
        self.layout.addWidget(self.diff_canvas)

    # ------------------------------------------------------

    def build_view_section(self, title):
        axis_selector = QComboBox()
        axis_selector.addItems(["X", "Y", "Z"])
        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(0)
        slider.setMaximum(0)
        slider.setValue(0)

        fig = Figure(figsize=(5, 3))
        canvas = FigureCanvas(fig)

        # summation lines
        ax_sum = fig.add_subplot(121)
        ax_sum.set_title(f"{title} Summations")
        lines = {ax: ax_sum.plot([], [], label=f"Sum {ax}")[0] for ax in ["X", "Y", "Z"]}
        slice_line = ax_sum.axvline(0, color="orange", linestyle="--")

        ax_sum.legend()

        # slice viewer
        ax_slice = fig.add_subplot(122)
        ax_slice.set_title("Slice")
        ax_slice.axis("off")

        return axis_selector, slider, canvas, lines, slice_line

    # ------------------------------------------------------

    def load_file(self, which):
        fname, _ = QFileDialog.getOpenFileName(self, "Open File", "", "NumPy/Dat Files (*.npy *.dat)")
        if not fname:
            return
        try:
            data = np.load(fname)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load file:\n{e}")
            return

        variables = parse_variables_from_path(fname)

        if which == 1:
            self.file1_data = data
            for v, lab in self.file1_var_labels.items():
                lab.setText(f"{v} = {variables[v]}")
            self.update_display(1)
        elif which == 2:
            self.file2_data = data
            for v, lab in self.file2_var_labels.items():
                lab.setText(f"{v} = {variables[v]}")
            self.update_display(2)

        # try to build diff
        self.build_diff_dataset()

    def build_diff_dataset(self):
        if self.file1_data is None or self.file2_data is None:
            return
        if self.file1_data.shape != self.file2_data.shape:
            QMessageBox.critical(self, "Error", "File1 and File2 shapes do not match. Cannot compute difference.")
            self.diff_data = None
            return
        self.diff_data = self.file2_data - self.file1_data
        # Use file1's variables for diff
        for v, lab in self.diff_var_labels.items():
            if self.file1_var_labels[v].text() != f"{v} = missing" and self.file2_var_labels[v].text() != f"{v} = missing":
                lab.setText(f"{v} = {self.file2_var_labels[v].text().split('=')[1].strip()} - {self.file1_var_labels[v].text().split('=')[1].strip()}")
            else:
                lab.setText(f"{v} = missing")
        self.update_display("diff")

    # ------------------------------------------------------

    def toggle_sync_file2(self, state):
        self.sync_file2 = (state == Qt.Checked)
        self.file2_axis_selector.setEnabled(not self.sync_file2)
        self.file2_slider.setEnabled(not self.sync_file2)
        self.update_display(2)

    def toggle_sync_diff(self, state):
        self.sync_diff = (state == Qt.Checked)
        self.diff_axis_selector.setEnabled(not self.sync_diff)
        self.diff_slider.setEnabled(not self.sync_diff)
        self.update_display("diff")

    # ------------------------------------------------------

    def update_display(self, which):
        if which == 1 and self.file1_data is not None:
            self.update_view(self.file1_data, self.file1_axis_selector, self.file1_slider, self.file1_canvas, self.file1_lines, self.file1_slice_line)

            if self.sync_file2 and self.file2_data is not None:
                self.file2_axis_selector.setCurrentIndex(self.file1_axis_selector.currentIndex())
                self.file2_slider.setValue(self.file1_slider.value())
                self.update_view(self.file2_data, self.file2_axis_selector, self.file2_slider, self.file2_canvas, self.file2_lines, self.file2_slice_line)

            if self.sync_diff and self.diff_data is not None:
                self.diff_axis_selector.setCurrentIndex(self.file1_axis_selector.currentIndex())
                self.diff_slider.setValue(self.file1_slider.value())
                self.update_view(self.diff_data, self.diff_axis_selector, self.diff_slider, self.diff_canvas, self.diff_lines, self.diff_slice_line)

        elif which == 2 and self.file2_data is not None:
            self.update_view(self.file2_data, self.file2_axis_selector, self.file2_slider, self.file2_canvas, self.file2_lines, self.file2_slice_line)

        elif which == "diff" and self.diff_data is not None:
            self.update_view(self.diff_data, self.diff_axis_selector, self.diff_slider, self.diff_canvas, self.diff_lines, self.diff_slice_line)

    def update_view(self, data, axis_selector, slider, canvas, lines, slice_line):
        ax_sum, ax_slice = canvas.figure.axes
        ax_sum.clear()
        ax_slice.clear()

        axis = axis_selector.currentIndex()
        index = slider.value()

        # summations
        sums = [
            data.sum(axis=(1, 2)),  # X
            data.sum(axis=(0, 2)),  # Y
            data.sum(axis=(0, 1)),  # Z
        ]
        labels = ["X", "Y", "Z"]

        for i, (s, lab) in enumerate(zip(sums, labels)):
            s_norm = s / np.max(s) if np.max(s) > 0 else s
            lines[lab], = ax_sum.plot(np.arange(len(s)), s_norm, label=f"Sum {lab}")

        # orange slice bar
        slice_line = ax_sum.axvline(index, color="orange", linestyle="--")

        ax_sum.legend()

        # update slider range
        slider.setMaximum(data.shape[axis] - 1)

        # slice view
        if axis == 0:
            slice_img = data[index, :, :]
        elif axis == 1:
            slice_img = data[:, index, :]
        else:
            slice_img = data[:, :, index]

        ax_slice.imshow(slice_img, cmap="viridis")
        ax_slice.set_title(f"Axis {labels[axis]}, Slice {index}")

        canvas.draw()


if __name__ == "__main__":
    app = QApplication([])
    viewer = SliceViewer()
    viewer.show()
    app.exec_()
