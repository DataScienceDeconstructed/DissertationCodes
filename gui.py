import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QFileDialog, QSlider
)
from PyQt5.QtCore import Qt

class DensityExplorer(QWidget):
    def __init__(self):
        super().__init__()
        self.data = None
        self.types = 0
        self.selected_type = 0
        self.slice_axis = 'Z'
        self.slice_index = 0


        self.initUI()

    def initUI(self):
        self.setWindowTitle("4D Density Explorer")

        layout = QVBoxLayout()
        top_layout = QHBoxLayout()
        mid_layout = QHBoxLayout()
        bottom_layout = QHBoxLayout()

        # Load button
        load_button = QPushButton("Load .dat File")
        load_button.clicked.connect(self.load_file)
        top_layout.addWidget(load_button)

        # Type selector
        self.type_selector = QComboBox()
        self.type_selector.currentIndexChanged.connect(self.update_plots)
        top_layout.addWidget(QLabel("Type:"))
        top_layout.addWidget(self.type_selector)

        # Axis selector
        self.axis_selector = QComboBox()
        self.axis_selector.addItems(["X", "Y", "Z"])
        self.axis_selector.currentIndexChanged.connect(self.update_slice_axis)
        mid_layout.addWidget(QLabel("Slice Axis:"))
        mid_layout.addWidget(self.axis_selector)
        self.axis_selector.setCurrentIndex(2)

        # Slice slider
        self.slice_slider = QSlider(Qt.Horizontal)
        self.slice_slider.valueChanged.connect(self.update_slice_plot)
        mid_layout.addWidget(QLabel("Slice Index:"))
        mid_layout.addWidget(self.slice_slider)

        # Matplotlib figures
        self.fig, self.axes = plt.subplots(1, 4, figsize=(16, 4))
        self.canvas = FigureCanvas(self.fig)

        layout.addLayout(top_layout)
        layout.addLayout(mid_layout)
        layout.addWidget(self.canvas)

        self.setLayout(layout)

    def load_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open .dat File", "", "dat files (*.dat)")
        if file_path:
            self.data = np.load(file_path)
            if self.data.ndim != 4:
                print("Invalid data shape. Must be 4D.")
                return
            self.types = self.data.shape[3]
            self.type_selector.blockSignals(True)  # Prevent signal while resetting
            self.type_selector.clear()
            self.type_selector.addItems([str(i) for i in range(self.types)])
            self.type_selector.setCurrentIndex(0)
            self.type_selector.blockSignals(False)

            self.selected_type = 0
            self.slice_slider.setMaximum(self.data.shape[2] - 1)
            self.slice_slider.setValue(0)

            self.update_plots()

    import matplotlib.cm as cm

    def update_plots(self):
        if self.data is None:
            return

        num_types = self.data.shape[3]
        axis_titles = ['X (ΣY,Z)', 'Y (ΣX,Z)', 'Z (ΣX,Y)']

        # Clear existing plots
        for ax in self.axes[:3]:
            ax.clear()

        colors = cm.get_cmap('tab10', num_types)

        for t in range(num_types):
            data_t = self.data[:, :, :, t]
            x_vals = data_t.sum(axis=(1, 2))
            y_vals = data_t.sum(axis=(0, 2))
            z_vals = data_t.sum(axis=(0, 1))

            # Normalize
            x_vals /= x_vals.max() if x_vals.max() != 0 else 1
            y_vals /= y_vals.max() if y_vals.max() != 0 else 1
            z_vals /= z_vals.max() if z_vals.max() != 0 else 1

            summaries = [x_vals, y_vals, z_vals]
            for i, ax in enumerate(self.axes[:3]):
                ax.plot(
                    summaries[i],
                    label=f"Type {t}",
                    color=colors(t),
                    linewidth=2 if t == self.selected_type else 1,
                    alpha=1.0 if t == self.selected_type else 0.5
                )

        for i, ax in enumerate(self.axes[:3]):
            ax.set_title(f"Normalized Density along {axis_titles[i]}")
            ax.set_xlabel("Index")
            ax.set_ylabel("Normalized Density")
            ax.set_ylim(0, 1.05)
            ax.legend(
                loc='upper center',
                bbox_to_anchor=(0.5, -0.15),
                ncol=3,  # Adjust number of columns based on expected number of types
                fontsize='small',
                frameon=False
            )

        self.update_slice_plot(draw=False)
        self.fig.tight_layout()
        self.canvas.draw()

    def update_slice_axis(self):
        if self.data is None:
            return
        self.slice_axis = self.axis_selector.currentText()
        axis_index = {'X': 0, 'Y': 1, 'Z': 2}[self.slice_axis]
        max_index = self.data.shape[axis_index] - 1
        self.slice_slider.setMaximum(max_index)
        self.slice_slider.setValue(0)
        self.update_slice_plot()

    def update_slice_plot(self, value=None, draw=True):
        if self.data is None:
            return

        type_text = self.type_selector.currentText()
        if not type_text.isdigit():
            return  # Invalid or empty selection
        self.selected_type = int(type_text)

        data_t = self.data[:, :, :, self.selected_type]

        self.slice_index = self.slice_slider.value()

        if self.slice_axis == 'X':
            slice_2d = data_t[self.slice_index, :, :]
        elif self.slice_axis == 'Y':
            slice_2d = data_t[:, self.slice_index, :]
        else:  # Z
            slice_2d = data_t[:, :, self.slice_index]

        # Update vertical slice line on the appropriate density graph
        axis_idx = self.axis_to_index(self.slice_axis)
        for i, ax in enumerate(self.axes[:3]):
            # Remove previous slice lines
            for line in ax.get_lines():
                if line.get_label() == 'slice_line':
                    line.remove()
            if i == axis_idx:
                ax.axvline(self.slice_index, color='orange', linestyle='--', label='slice_line')

        # Update slice image
        ax = self.axes[3]
        ax.clear()
        im = ax.imshow(slice_2d.T, origin='lower', aspect='auto', cmap='viridis')
        ax.set_title(f"{self.slice_axis}-slice at {self.slice_index} (Type {self.selected_type})")
        ax.set_xlabel("Axis 1")
        ax.set_ylabel("Axis 2")

        if draw:
            self.canvas.draw()

    def axis_to_index(self, axis):
        return {'X': 0, 'Y': 1, 'Z': 2}[axis]


def main():
    app = QApplication(sys.argv)
    ex = DensityExplorer()
    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
