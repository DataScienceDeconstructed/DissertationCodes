import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QFileDialog, QSlider, QCheckBox
)
from PyQt5.QtCore import Qt


class DensityExplorer(QWidget):
    def __init__(self):
        super().__init__()
        # Two datasets
        self.data1 = None
        self.data2 = None

        # Track UI state for each dataset
        self.types1 = self.types2 = 0
        self.selected_type1 = self.selected_type2 = 0
        self.slice_axis1 = self.slice_axis2 = 'Z'
        self.slice_index1 = self.slice_index2 = 0

        # Sync flag
        self.sync_enabled = False

        self.initUI()

    def initUI(self):
        self.setWindowTitle("Dual 4D Density Explorer")

        layout = QVBoxLayout()

        # ---- File 1 Controls ----
        top_layout1 = QHBoxLayout()
        load_button1 = QPushButton("Load 1st .npy File")
        load_button1.clicked.connect(lambda: self.load_file(1))
        top_layout1.addWidget(load_button1)

        self.type_selector1 = QComboBox()
        self.type_selector1.currentIndexChanged.connect(lambda: self.update_plots(1))
        top_layout1.addWidget(QLabel("Type:"))
        top_layout1.addWidget(self.type_selector1)

        self.axis_selector1 = QComboBox()
        self.axis_selector1.addItems(["X", "Y", "Z"])
        self.axis_selector1.currentIndexChanged.connect(lambda: self.update_slice_axis(1))
        top_layout1.addWidget(QLabel("Slice Axis:"))
        top_layout1.addWidget(self.axis_selector1)
        self.axis_selector1.setCurrentIndex(2)

        self.slice_slider1 = QSlider(Qt.Horizontal)
        self.slice_slider1.valueChanged.connect(lambda: self.update_slice_plot(1))
        top_layout1.addWidget(QLabel("Slice Index:"))
        top_layout1.addWidget(self.slice_slider1)

        # ---- Sync Checkbox ----
        sync_layout = QHBoxLayout()
        self.sync_checkbox = QCheckBox("Sync Controls")
        self.sync_checkbox.stateChanged.connect(self.toggle_sync)
        sync_layout.addWidget(self.sync_checkbox)

        # ---- File 2 Controls ----
        top_layout2 = QHBoxLayout()
        load_button2 = QPushButton("Load 2nd .npy File")
        load_button2.clicked.connect(lambda: self.load_file(2))
        top_layout2.addWidget(load_button2)

        self.type_selector2 = QComboBox()
        self.type_selector2.currentIndexChanged.connect(lambda: self.update_plots(2))
        top_layout2.addWidget(QLabel("Type:"))
        top_layout2.addWidget(self.type_selector2)

        self.axis_selector2 = QComboBox()
        self.axis_selector2.addItems(["X", "Y", "Z"])
        self.axis_selector2.currentIndexChanged.connect(lambda: self.update_slice_axis(2))
        top_layout2.addWidget(QLabel("Slice Axis:"))
        top_layout2.addWidget(self.axis_selector2)
        self.axis_selector2.setCurrentIndex(2)

        self.slice_slider2 = QSlider(Qt.Horizontal)
        self.slice_slider2.valueChanged.connect(lambda: self.update_slice_plot(2))
        top_layout2.addWidget(QLabel("Slice Index:"))
        top_layout2.addWidget(self.slice_slider2)

        # ---- Matplotlib Figure with 2 rows ----
        self.fig, axes = plt.subplots(2, 4, figsize=(16, 8))
        self.axes = axes.flatten()  # Flatten into list of 8
        self.canvas = FigureCanvas(self.fig)

        # Layout assembly
        layout.addLayout(top_layout1)
        layout.addLayout(sync_layout)
        layout.addLayout(top_layout2)
        layout.addWidget(self.canvas)

        self.setLayout(layout)

    def toggle_sync(self, state):
        self.sync_enabled = state == Qt.Checked

        # Enable/disable File 2 controls
        self.axis_selector2.setEnabled(not self.sync_enabled)
        self.slice_slider2.setEnabled(not self.sync_enabled)

        # If enabling sync, immediately sync values
        if self.sync_enabled:
            self.axis_selector2.setCurrentIndex(self.axis_selector1.currentIndex())
            self.slice_slider2.setValue(self.slice_slider1.value())
            self.update_slice_axis(2)
            self.update_slice_plot(2)

    def load_file(self, which):
        file_path, _ = QFileDialog.getOpenFileName(self, f"Open {which} .npy File", "", "NumPy files (*.npy)")
        if not file_path:
            return

        data = np.load(file_path)
        if data.ndim != 4:
            print("Invalid data shape. Must be 4D.")
            return

        if which == 1:
            self.data1 = data
            self.types1 = data.shape[3]
            self.type_selector1.blockSignals(True)
            self.type_selector1.clear()
            self.type_selector1.addItems([str(i) for i in range(self.types1)])
            self.type_selector1.setCurrentIndex(0)
            self.type_selector1.blockSignals(False)
            self.selected_type1 = 0
            self.slice_slider1.setMaximum(data.shape[2] - 1)
            self.slice_slider1.setValue(0)
            self.update_plots(1)

        else:
            self.data2 = data
            self.types2 = data.shape[3]
            self.type_selector2.blockSignals(True)
            self.type_selector2.clear()
            self.type_selector2.addItems([str(i) for i in range(self.types2)])
            self.type_selector2.setCurrentIndex(0)
            self.type_selector2.blockSignals(False)
            self.selected_type2 = 0
            self.slice_slider2.setMaximum(data.shape[2] - 1)
            self.slice_slider2.setValue(0)
            self.update_plots(2)

    def update_plots(self, which):
        data = self.data1 if which == 1 else self.data2
        if data is None:
            return

        num_types = data.shape[3]
        axis_titles = ['X (ΣY,Z)', 'Y (ΣX,Z)', 'Z (ΣX,Y)']

        row_offset = 0 if which == 1 else 4

        for ax in self.axes[row_offset:row_offset+3]:
            ax.clear()

        colors = cm.get_cmap('tab10', num_types)
        selected_type = self.selected_type1 if which == 1 else self.selected_type2

        for t in range(num_types):
            data_t = data[:, :, :, t]
            x_vals = data_t.sum(axis=(1, 2))
            y_vals = data_t.sum(axis=(0, 2))
            z_vals = data_t.sum(axis=(0, 1))

            x_vals /= x_vals.max() if x_vals.max() != 0 else 1
            y_vals /= y_vals.max() if y_vals.max() != 0 else 1
            z_vals /= z_vals.max() if z_vals.max() != 0 else 1

            summaries = [x_vals, y_vals, z_vals]
            for i, ax in enumerate(self.axes[row_offset:row_offset+3]):
                ax.plot(
                    summaries[i],
                    label=f"Type {t}",
                    color=colors(t),
                    linewidth=2 if t == selected_type else 1,
                    alpha=1.0 if t == selected_type else 0.5
                )

        for i, ax in enumerate(self.axes[row_offset:row_offset+3]):
            ax.set_title(f"Normalized Density along {axis_titles[i]}")
            ax.set_xlabel("Index")
            ax.set_ylabel("Normalized Density")
            ax.set_ylim(0, 1.05)
            ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3, fontsize='small', frameon=False)

        self.update_slice_plot(which, draw=False)
        self.fig.tight_layout()
        self.canvas.draw()

    def update_slice_axis(self, which):
        data = self.data1 if which == 1 else self.data2
        if data is None:
            return

        axis_selector = self.axis_selector1 if which == 1 else self.axis_selector2
        slider = self.slice_slider1 if which == 1 else self.slice_slider2

        axis = axis_selector.currentText()
        axis_index = {'X': 0, 'Y': 1, 'Z': 2}[axis]
        max_index = data.shape[axis_index] - 1
        slider.setMaximum(max_index)
        slider.setValue(0)

        if which == 1:
            self.slice_axis1 = axis
            if self.sync_enabled:
                self.axis_selector2.setCurrentIndex(axis_selector.currentIndex())
                self.update_slice_axis(2)
        else:
            self.slice_axis2 = axis

        self.update_slice_plot(which)

    def update_slice_plot(self, which, value=None, draw=True):
        data = self.data1 if which == 1 else self.data2
        if data is None:
            return

        type_selector = self.type_selector1 if which == 1 else self.type_selector2
        slider = self.slice_slider1 if which == 1 else self.slice_slider2
        selected_type = int(type_selector.currentText()) if type_selector.currentText().isdigit() else 0

        if which == 1:
            self.selected_type1 = selected_type
            slice_axis = self.slice_axis1
            self.slice_index1 = slider.value()
            row_offset = 0
            if self.sync_enabled:
                self.slice_slider2.setValue(slider.value())
                self.update_slice_plot(2, draw=False)
        else:
            self.selected_type2 = selected_type
            slice_axis = self.slice_axis2
            self.slice_index2 = slider.value()
            row_offset = 4

        data_t = data[:, :, :, selected_type]
        slice_index = slider.value()

        if slice_axis == 'X':
            slice_2d = data_t[slice_index, :, :]
        elif slice_axis == 'Y':
            slice_2d = data_t[:, slice_index, :]
        else:
            slice_2d = data_t[:, :, slice_index]

        axis_idx = {'X': 0, 'Y': 1, 'Z': 2}[slice_axis]
        for i, ax in enumerate(self.axes[row_offset:row_offset+3]):
            for line in ax.get_lines():
                if line.get_label() == 'slice_line':
                    line.remove()
            if i == axis_idx:
                ax.axvline(slice_index, color='orange', linestyle='--', label='slice_line')

        ax = self.axes[row_offset+3]
        ax.clear()
        ax.imshow(slice_2d.T, origin='lower', aspect='auto', cmap='viridis')
        ax.set_title(f"{slice_axis}-slice at {slice_index} (Type {selected_type})")
        ax.set_xlabel("Axis 1")
        ax.set_ylabel("Axis 2")

        if draw:
            self.canvas.draw()


def main():
    app = QApplication(sys.argv)
    ex = DensityExplorer()
    ex.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
