import sys
import os
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QComboBox, QSlider, QCheckBox,
    QMessageBox, QSizePolicy
)
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class SliceViewer(QWidget):
    def __init__(self, title):
        super().__init__()
        self.title = title
        self.data = None
        self.sync_checkbox = None
        self.linked_viewer = None

        # Layouts
        self.layout = QVBoxLayout(self)
        self.label = QLabel(title)
        self.layout.addWidget(self.label)

        control_layout = QHBoxLayout()

        # File load button
        self.load_button = QPushButton("Load File")
        self.load_button.clicked.connect(self.load_file)
        control_layout.addWidget(self.load_button)

        # Variable labels
        self.var_labels = {}
        for var in ["Umin", "rad", "den", "gap", "len", "NP"]:
            lbl = QLabel(f"{var}: missing")
            self.var_labels[var] = lbl
            control_layout.addWidget(lbl)

        # Axis selector
        self.axis_selector = QComboBox()
        self.axis_selector.addItems(["X", "Y", "Z"])
        self.axis_selector.currentIndexChanged.connect(self.update_view)
        control_layout.addWidget(self.axis_selector)

        # Sync checkbox (added later externally)

        self.layout.addLayout(control_layout)

        # Plot area
        plot_layout = QHBoxLayout()

        self.fig = Figure(figsize=(6, 4))
        self.canvas = FigureCanvas(self.fig)
        self.ax_sum = self.fig.add_subplot(1, 2, 1)
        self.ax_slice = self.fig.add_subplot(1, 2, 2)
        self.fig.tight_layout()
        plot_layout.addWidget(self.canvas)

        # Slider at far right (stretch)
        self.slider = QSlider(Qt.Horizontal)
        self.slider.valueChanged.connect(self.update_view)
        self.slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        plot_layout.addWidget(self.slider)

        self.layout.addLayout(plot_layout)

        # Orange bar lines for sum plots
        self.slice_line = None

    def load_file(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Open NumPy File", "", "NumPy files (*.npy *.dat)", options=options
        )
        if file_name:
            try:
                self.data = np.load(file_name)
                if self.data.ndim != 4:
                    raise ValueError("Data must be 4D (X, Y, Z, T)")

                # Parse directory variables
                path_parts = file_name.split(os.sep)
                for var in self.var_labels:
                    found = "missing"
                    for part in path_parts:
                        if part.startswith(var + "_"):
                            found = part.split("_", 1)[1]
                    self.var_labels[var].setText(f"{var}: {found}")

                self.slider.setMaximum(self.data.shape[0] - 1)
                self.slider.setValue(self.data.shape[0] // 2)
                self.update_view()

                if self.linked_viewer:
                    self.linked_viewer.try_make_diff()

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load file: {e}")

    def update_view(self):
        if self.data is None:
            return

        axis = self.axis_selector.currentIndex()
        idx = self.slider.value()

        # Clear axes
        self.ax_sum.clear()
        self.ax_slice.clear()

        # Summations for all T
        labels = ["X", "Y", "Z"]
        for t in range(self.data.shape[3]):
            s = self.data.sum(axis=axis)[:, :, t] if axis < 2 else self.data.sum(axis=axis)[:, t]
            if s.ndim > 1:
                s = s.sum(axis=0)
            s_norm = s / np.max(s) if np.max(s) > 0 else s
            self.ax_sum.plot(np.arange(len(s)), s_norm, label=f"T{t}")

        self.ax_sum.legend()
        self.ax_sum.set_title("Summation")

        # Slice view for current type (T=0)
        slicer = [slice(None)] * 4
        slicer[axis] = idx
        slice2d = self.data[tuple(slicer)]

        im = self.ax_slice.imshow(slice2d, cmap="viridis", origin="lower")
        self.ax_slice.set_title(f"Slice {labels[axis]}={idx}")
        self.fig.colorbar(im, ax=self.ax_slice)

        # Orange bar showing current index
        if self.slice_line:
            self.slice_line.remove()
        self.slice_line = self.ax_sum.axvline(idx, color="orange", linestyle="--")

        self.canvas.draw_idle()

        # Sync if checkbox is checked
        if self.sync_checkbox and self.sync_checkbox.isChecked():
            if self.linked_viewer and self.linked_viewer.data is not None:
                self.linked_viewer.axis_selector.setCurrentIndex(axis)
                max_val = self.linked_viewer.slider.maximum()
                self.linked_viewer.slider.setValue(min(idx, max_val))

    def try_make_diff(self):
        if self.linked_viewer is None:
            return
        f1, f2, fdiff = self, self.linked_viewer, self.linked_viewer.diff_viewer
        if f1.data is not None and f2.data is not None:
            if f1.data.shape == f2.data.shape:
                fdiff.data = f2.data - f1.data
                fdiff.slider.setMaximum(fdiff.data.shape[0] - 1)
                fdiff.slider.setValue(fdiff.data.shape[0] // 2)
                fdiff.update_view()
            else:
                QMessageBox.critical(self, "Error", "Arrays have different shapes, cannot subtract.")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("3D Data Viewer with Difference")
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # File1 viewer
        self.viewer1 = SliceViewer("File 1")
        layout.addWidget(self.viewer1)

        # File2 viewer
        self.viewer2 = SliceViewer("File 2")
        self.viewer2.sync_checkbox = QCheckBox("Sync with File 1")
        self.viewer2.layout.addWidget(self.viewer2.sync_checkbox)
        layout.addWidget(self.viewer2)

        # Diff viewer
        self.diff_viewer = SliceViewer("Difference (File2 - File1)")
        self.diff_viewer.sync_checkbox = QCheckBox("Sync with File 1")
        self.diff_viewer.layout.addWidget(self.diff_viewer.sync_checkbox)
        layout.addWidget(self.diff_viewer)

        # Cross-links
        self.viewer1.linked_viewer = self.viewer2
        self.viewer2.linked_viewer = self.viewer1
        self.viewer2.diff_viewer = self.diff_viewer

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
