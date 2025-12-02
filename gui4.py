import sys
import os
import numpy as np
from pathlib import Path
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from PyQt5.QtGui import QCursor

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QComboBox, QSlider, QLabel, QCheckBox,
    QMessageBox, QSizePolicy, QStatusBar, QToolTip
)
from PyQt5.QtCore import Qt

import gap_brush_analysis

# ---------------- Constants ----------------
VARS = ["Umin", "rad", "den", "gap", "len", "NP", "system x", "system y", "system z", "concentration at z"]
AXIS_MAP = {"X": 0, "Y": 1, "Z": 2}


class DensityExplorer(QMainWindow):
    """4D (X,Y,Z,T) density explorer for File 1 + File 2.
    Row 1: File 1 data
    Row 2: File 2 row is overwritten with RDP / concentration / FFT derived from File 1.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("4D Density Explorer — Two Files Only")
        self.resize(1600, 1050)
        self.system_dims = [0,0,0]
        # status bar
        self.setStatusBar(QStatusBar(self))

        # Data storage
        self.data = {1: None, 2: None}
        self.paths = {1: None, 2: None}
        self.last_frame_path = {1: None, 2: None}
        self.file_xyz_path = {1: None, 2: None}
        # Per-file UI state
        self.selected_type = {1: 0, 2: 0}
        self.slice_axis = {1: 'Z', 2: 'Z'}
        self.slice_index = {1: 0, 2: 0}
        self.sync_to_file1 = {2: False}

        # Persistent artists for slice panels
        self.slice_images = {1: None, 2: None}
        self.colorbars    = {1: None, 2: None}
        self.RDPs = {1: {'brush': None, 'gap': None}, 2: {'brush': None, 'gap': None}}
        self.concentrations = {1: {'brush': None, 'gap': None}, 2: {'brush': None, 'gap': None}}

        self._build_ui()

    # ----------------------------- UI -----------------------------
    def _build_ui(self):
        central = QWidget(self)
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        # ====== Controls (Top) ======
        # ---- Controls row for File 1 ----
        root.addWidget(self._make_dataset_header("File 1 Controls"))
        self.ctrl1 = self._make_controls_row(file_id=1)
        root.addLayout(self.ctrl1['layout'])

        # ---- Controls row for File 2 (with sync) ----
        root.addWidget(self._make_dataset_header("File 2 Controls"))
        self.ctrl2 = self._make_controls_row(file_id=2, with_sync=True)
        root.addLayout(self.ctrl2['layout'])

        # ====== Plots (Bottom): 2 rows × 4 columns ======
        #self.fig, grid = plt.subplots(2, 4, figsize=(16, 12))
        self.fig, grid = plt.subplots(
            2, 4,
            figsize=(16, 12)
        )

        self.axes = {
            1: grid[0, :],      # row 0: File 1
            2: grid[1, :],      # row 1: File 2 (overwritten with FFT/RDP/conc)
        }
        self.canvas = FigureCanvas(self.fig)
        self.canvas.mpl_connect("motion_notify_event", self._on_mouse_move)
        self.fig.subplots_adjust(
            left=0.06,
            right=0.97,
            top=0.95,
            bottom=0.07,
            wspace=0.35,
            hspace=0.45
        )

        root.addWidget(self.canvas)

        # safe tight layout (once)
        #self.fig.tight_layout()
        # Remove tight_layout() because it breaks constrained_layout


        self._init_empty_plots()

    def _make_dataset_header(self, title: str) -> QLabel:
        return QLabel(f"<b>{title}</b>")

    # ---------------- mouse tracking ----------------
    def _old__on_mouse_move(self, event):
        if event.inaxes is None:
            return
        ax = event.inaxes
        try:
            msg = ax.format_coord(event.xdata, event.ydata)
        except Exception:
            msg = ""
        self.statusBar().showMessage(msg)

    from PyQt5.QtWidgets import QToolTip
    from PyQt5.QtGui import QCursor

    def _on_mouse_move(self, event):
        """Displays tooltips and keeps status bar coordinates."""

        if event.inaxes is None:
            QToolTip.hideText()
            self.statusBar().clearMessage()
            return

        ax = event.inaxes

        # ---- SLICE IMAGES ----
        img = None
        for key in (1, 2):
            if self.slice_images[key] is not None and self.slice_images[key].axes is ax:
                img = self.slice_images[key]
                break

        if img is not None:
            data = img.get_array()
            x = event.xdata
            y = event.ydata

            ix = int(round(x))
            iy = int(round(y))

            if 0 <= ix < data.shape[0] and 0 <= iy < data.shape[1]:
                val = data[ix, iy]
                QToolTip.showText(
                    QCursor.pos(),
                    f"x={ix}, y={iy}\nvalue={val:.5g}",
                    self
                )
            else:
                QToolTip.hideText()

            # Keep status bar updated
            try:
                msg = ax.format_coord(event.xdata-self.system_dims[0]//2, event.ydata-self.system_dims[1]//2)
                self.statusBar().showMessage(msg)
            except:
                pass
            return

        # ---- LINE PLOTS ----
        x = event.xdata
        if x is None:
            QToolTip.hideText()
            self.statusBar().clearMessage()
            return

        best_info = None
        min_dist = float("inf")

        if len(ax.lines) > 3:
            xd = ax.lines[self.selected_type[1]].get_xdata()
            yd = ax.lines[self.selected_type[1]].get_ydata()
        else:
            xd = ax.lines[0].get_xdata()
            yd = ax.lines[0].get_ydata()

        idx = int(round(x))
        if 0 <= idx < len(xd):
            dist = abs(x - idx)
            if dist < min_dist:
                min_dist = dist
                best_info = (xd[idx], yd[idx])

        if best_info:
            xv, yv = best_info
            QToolTip.showText(
                QCursor.pos(),
                f"x={int(round(xv))}, y={yv:.5g}",
                self
            )
        else:
            QToolTip.hideText()

        # Update the status bar text as before
        try:
            msg = ax.format_coord(event.xdata, event.ydata)
            self.statusBar().showMessage(msg)
        except:
            pass

    # ---------------- controls ----------------
    def _make_controls_row(self, file_id, with_sync: bool = False):
        row = {}
        layout = QVBoxLayout()

        # --- Variables from path (for File 1 and File 2) ---
        var_row = QHBoxLayout()
        var_labels = {}
        for v in VARS:
            lab = QLabel(f"{v} = missing")
            var_labels[v] = lab
            var_row.addWidget(lab)
        var_row.addStretch(1)
        layout.addLayout(var_row)

        # --- Controls line ---
        top = QHBoxLayout()

        # Load button
        load_btn = QPushButton(f"Load File {file_id} (.npy / .dat)")
        load_btn.clicked.connect(lambda: self._load_file(file_id))
        top.addWidget(load_btn)

        # Type selector
        type_combo = QComboBox()
        type_combo.currentIndexChanged.connect(lambda _, fid=file_id: self._on_type_changed(fid))
        type_combo.setEnabled(False)
        top.addWidget(QLabel("Type:"))
        top.addWidget(type_combo)

        # Axis selector
        axis_combo = QComboBox()
        axis_combo.addItems(["X", "Y", "Z"])
        axis_combo.setCurrentText('Z')
        axis_combo.currentIndexChanged.connect(lambda _, fid=file_id: self._on_axis_changed(fid))
        top.addWidget(QLabel("Slice Axis:"))
        top.addWidget(axis_combo)

        # Slider
        slider = QSlider(Qt.Horizontal)
        slider.setRange(0, 0)
        slider.setValue(0)
        slider.valueChanged.connect(lambda _, fid=file_id: self._on_slider_changed(fid))
        slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        top.addWidget(QLabel("Slice Index:"))
        top.addWidget(slider, stretch=1)

        # Sync
        sync_cb = None
        if with_sync:
            sync_cb = QCheckBox("Sync to File 1")
            sync_cb.stateChanged.connect(lambda state, fid=file_id: self._toggle_sync(fid, state))
            top.addWidget(sync_cb)

        layout.addLayout(top)

        row['layout'] = layout
        row['type_combo'] = type_combo
        row['axis_combo'] = axis_combo
        row['slider'] = slider
        row['sync_cb'] = sync_cb
        row['var_labels'] = var_labels
        return row

    # ---------------- blank plots ----------------
    def _init_empty_plots(self):
        titles = ["X (ΣY,Z)", "Y (ΣX,Z)", "Z (ΣX,Y)"]
        for key in (1, 2):
            self.slice_images[key] = None
            if self.colorbars[key] is not None:
                try:
                    self.colorbars[key].remove()
                except:
                    pass
                self.colorbars[key] = None

            for i in range(3):
                ax = self.axes[key][i]
                ax.clear()
                ax.set_title(titles[i])
                ax.set_xlabel("Index")
                ax.set_ylabel("Normalized Density")
                ax.set_ylim(-1.05, 1.05)
                ax.axhline(0.0, color='black', linestyle=':')
            ax = self.axes[key][3]
            ax.clear()
            ax.set_title("Slice (load a file)")
        self.canvas.draw_idle()

    # ---------------- load file ----------------
    def _load_file(self, file_id: int):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open NumPy Array", "", "NumPy Arrays (*.npy *.dat);;All Files (*)"
        )
        if not path:
            return
        try:
            arr = np.load(path, allow_pickle=False)
        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Could not load file:\n{e}")
            return
        if arr.ndim != 4:
            QMessageBox.critical(self, "Shape Error",
                                 f"Loaded array has shape {arr.shape}. Expected 4D (X, Y, Z, T).")
            return

        self.data[file_id] = arr
        self.paths[file_id] = path

        last_frame_path = Path(path)
        parent_path = str(last_frame_path.parent)
        last_frame_str = parent_path + "/last_frame.xyz"
        self.last_frame_path[file_id] = last_frame_str

        file_xyz_path = Path(path)
        file_xyz_path_parent = Path(file_xyz_path.parent)
        files = list(file_xyz_path_parent.glob("frames_exp*.xyz"))
        self.file_xyz_path[file_id] = str(files[0])

        # parse variables
        vals = {v: 'missing' for v in VARS}
        for part in os.path.normpath(self.last_frame_path[file_id]).split(os.sep):
            if '_' in part:
                name, value = part.split('_', 1)
                if name in vals:
                    vals[name] = value

        vals["system x"] = arr.shape[0]
        vals["system y"] = arr.shape[1]
        vals["system z"] = arr.shape[2]
        self.system_dims[0] = arr.shape[0]
        self.system_dims[1] = arr.shape[1]
        self.system_dims[2] = arr.shape[2]

        # compute RDP + concentration
        self.RDPs[file_id]['brush'], self.RDPs[file_id]['gap'], \
        self.concentrations[file_id]['brush'] = gap_brush_analysis.calc_2D_avg_RDP(
            self.file_xyz_path[file_id],
            arr.shape[:3],
            int(vals['gap']),
            int(vals['NP']),
            int(vals['len'])
        )

        vals["concentration at z"] = self.concentrations[file_id]['brush'][0]

        self._reset_slice_artists(file_id)

        # type selector
        T = arr.shape[3]
        ctrl = self._ctrl_for(file_id)
        combo = ctrl['type_combo']
        combo.blockSignals(True)
        combo.clear()
        combo.addItems([str(i) for i in range(T)])
        combo.setEnabled(True)
        combo.setCurrentIndex(0)
        combo.blockSignals(False)
        self.selected_type[file_id] = 0

        self._reset_slider_bounds(file_id)
        self._update_var_labels(file_id, vals)

        self._update_all_plots(file_id)

        # sync
        if file_id == 1 and self.sync_to_file1[2] and self.data[2] is not None:
            self._apply_sync_to_dataset(2)
            self._update_all_plots(2)

    # ---------------- var labels ----------------
    def _update_var_labels(self, file_id, vals):
        labels = self._ctrl_for(file_id)['var_labels']
        for k, lab in labels.items():
            lab.setText(f"{k} = {vals[k]}")

    # ---------------- reset artists ----------------
    def _reset_slice_artists(self, key):
        if self.colorbars[key] is not None:
            try:
                self.colorbars[key].remove()
            except:
                pass
            self.colorbars[key] = None
        self.slice_images[key] = None

    # ---------------- events ----------------
    def _on_type_changed(self, key):
        if self.data.get(key) is None:
            return
        ctrl = self._ctrl_for(key)
        txt = ctrl['type_combo'].currentText()
        if txt.isdigit():
            self.selected_type[key] = int(txt)
        self._update_all_plots(key)

    def _on_axis_changed(self, key):
        ctrl = self._ctrl_for(key)
        self.slice_axis[key] = ctrl['axis_combo'].currentText()
        self._reset_slider_bounds(key)
        self._update_all_plots(key)
        if key == 1 and self.sync_to_file1[2] and self.data[2] is not None:
            self._apply_sync_to_dataset(2)
            self._update_all_plots(2)

    def _on_slider_changed(self, key):
        ctrl = self._ctrl_for(key)
        self.slice_index[key] = ctrl['slider'].value()
        self._update_all_plots(key)

        if key == 1 and self.sync_to_file1[2] and self.data[2] is not None:
            self._apply_sync_to_dataset(2)
            self._update_all_plots(2)

        # update concentration label
        if key == 1:
            labels = self._ctrl_for(key)['var_labels']
            labels["concentration at z"].setText(
                f"concentration at z = {self.concentrations[1]['brush'][self.slice_index[1]]}"
            )

    def _toggle_sync(self, key, state):
        self.sync_to_file1[key] = (state == Qt.Checked)
        ctrl = self._ctrl_for(key)
        ctrl['axis_combo'].setEnabled(not self.sync_to_file1[key])
        ctrl['slider'].setEnabled(not self.sync_to_file1[key])
        if self.sync_to_file1[key] and self.data[1] is not None:
            self._apply_sync_to_dataset(key)
            self._update_all_plots(key)

    # ---------------- helpers ----------------
    def _ctrl_for(self, key):
        return self.ctrl1 if key == 1 else self.ctrl2

    def _reset_slider_bounds(self, key):
        data = self.data.get(key)
        if data is None: return
        axis = AXIS_MAP[self.slice_axis[key]]
        max_index = max(0, data.shape[axis] - 1)
        ctrl = self._ctrl_for(key)
        sld = ctrl['slider']
        sld.blockSignals(True)
        sld.setRange(0, max_index)
        if self.slice_index[key] > max_index:
            self.slice_index[key] = max_index
        sld.setValue(self.slice_index[key])
        sld.blockSignals(False)

    def _apply_sync_to_dataset(self, dst_key):
        if self.data.get(dst_key) is None or self.data.get(1) is None:
            return
        axis_txt = self.slice_axis[1]
        idx = self.slice_index[1]
        self.slice_axis[dst_key] = axis_txt

        dst_ctrl = self._ctrl_for(dst_key)
        dst_ctrl['axis_combo'].blockSignals(True)
        dst_ctrl['axis_combo'].setCurrentText(axis_txt)
        dst_ctrl['axis_combo'].blockSignals(False)

        self._reset_slider_bounds(dst_key)
        dst_sld = dst_ctrl['slider']
        clamped = int(np.clip(idx, dst_sld.minimum(), dst_sld.maximum()))
        dst_ctrl['slider'].blockSignals(True)
        dst_ctrl['slider'].setValue(clamped)
        dst_ctrl['slider'].blockSignals(False)
        self.slice_index[dst_key] = clamped

    # ---------------- plotting ----------------
    def _update_all_plots(self, key):
        if self.data.get(key) is None:
            return
        self._update_summaries(key)
        self._update_slice_plot(key)
        self.canvas.draw_idle()

    def _update_summaries(self, key):
        data = self.data[key]
        axes_row = self.axes[key]

        for i in range(3):
            axes_row[i].clear()

        num_types = data.shape[3]
        colors = cm.get_cmap('tab20', max(10, num_types))

        sel_t = self.selected_type[key]
        for t in range(num_types):
            vol = data[:, :, :, t]
            x_vals = vol.sum(axis=(1, 2))
            y_vals = vol.sum(axis=(0, 2))
            z_vals = vol.sum(axis=(0, 1))

            def norm(v):
                vmax = float(np.max(np.abs(v))) if v.size else 0.0
                return (v / vmax) if vmax > 0 else v

            series = [norm(x_vals), norm(y_vals), norm(z_vals)]
            for i in range(3):
                axes_row[i].plot(
                    series[i],
                    color=colors(t),
                    linewidth=2 if t == sel_t else 1,
                    alpha=1.0 if t == sel_t else 0.6
                )

        titles = ["X (ΣY,Z)", "Y (ΣX,Z)", "Z (ΣX,Y)"]
        for i in range(3):
            axes_row[i].set_title(titles[i])
            axes_row[i].set_xlabel("Index")
            axes_row[i].set_ylabel("Normalized Density")
            axes_row[i].set_ylim(-1.05, 1.05)
            axes_row[i].axhline(0.0, color='black', linestyle=':')

        axis_idx = AXIS_MAP[self.slice_axis[key]]
        axes_row[axis_idx].axvline(self.slice_index[key], color='orange', linestyle='--')

    def _update_slice_plot(self, key):
        data = self.data[key]
        ax = self.axes[key][3]

        # compute slice
        t = self.selected_type[key]
        vol = data[:, :, :, t]
        axis_txt = self.slice_axis[key]
        idx = self.slice_index[key]

        if axis_txt == 'X':
            slice_2d = vol[idx, :, :]
            xlab, ylab = 'Y', 'Z'
        elif axis_txt == 'Y':
            slice_2d = vol[:, idx, :]
            xlab, ylab = 'X', 'Z'
        else:
            slice_2d = vol[:, :, idx]
            xlab, ylab = 'X', 'Y'

        slice_2d = np.squeeze(slice_2d)

        # build formatter
        def mk_formatter(slice_2d_local):
            def _fmt(x, y):
                ix = int(round(x))
                iy = int(round(y))
                if 0 <= ix < slice_2d_local.shape[0] and 0 <= iy < slice_2d_local.shape[1]:
                    val = slice_2d_local[ix, iy]
                    return f"{xlab}={ix}, {ylab}={iy}, value={val:.4g}"
                return f"{xlab}={x:.1f}, {ylab}={y:.1f}"
            return _fmt

        # create/update image
        if self.slice_images[key] is None:
            ax.cla()
            im = ax.imshow(slice_2d.T, origin='lower', aspect='auto', cmap='viridis')
            ax.set_title(f"{axis_txt}-slice at {idx} (Type {t})")
            ax.set_xlabel(xlab)
            ax.set_ylabel(ylab)

            ax.format_coord = mk_formatter(slice_2d)

            cbar = ax.figure.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
            self.slice_images[key] = im
            self.colorbars[key] = cbar
        else:
            im = self.slice_images[key]
            im.set_data(slice_2d.T)
            vmin = float(np.min(slice_2d))
            vmax = float(np.max(slice_2d))
            if vmin == vmax:
                eps = 1e-12
                vmin -= eps
                vmax += eps
            im.set_clim(vmin=vmin, vmax=vmax)

            ax.set_title(f"{axis_txt}-slice at {idx} (Type {t})")
            ax.set_xlabel(xlab)
            ax.set_ylabel(ylab)

            ax.format_coord = mk_formatter(slice_2d)

            if self.colorbars[key] is not None:
                self.colorbars[key].update_normal(im)

        # ------------ custom logic (Option A): overwrite row 2 -------------
        if key == 1:
            key2 = 2  # overwrite File-2 row
            axes_row = self.axes[key2]

            # clear summaries for row 2
            for i in range(3):
                axes_row[i].clear()

            # RDP
            axes_row[2].set_title("Z Plane RDP")
            axes_row[2].plot(
                self.RDPs[1]['brush'][self.slice_index[1]],
                linewidth=1,
                alpha=1.0,
            )

            # NP concentration
            axes_row[1].set_title("Z Plane NP Concentration")
            axes_row[1].plot(
                self.concentrations[1]['brush'],
                linewidth=1,
                alpha=1.0,
            )
            axes_row[1].axvline(self.slice_index[1], color='orange', linestyle='--')

            # FFT
            ax2 = axes_row[3]
            slice_xy = slice_2d - np.mean(slice_2d)
            fft2d = np.fft.fftshift(np.fft.fft2(slice_xy))
            fft_abs = np.abs(fft2d)

            # FFT display
            if self.slice_images[key2] is None:
                ax2.cla()
                im2 = ax2.imshow(fft_abs.T, origin='lower', aspect='auto', cmap='viridis')
                ax2.set_title(f"Z Plane FFT at {idx} (Type {t})")
                ax2.set_xlabel(xlab)
                ax2.set_ylabel(ylab)
                cbar2 = ax2.figure.colorbar(im2, ax=ax2, fraction=0.046, pad=0.04)
                self.slice_images[key2] = im2
                self.colorbars[key2] = cbar2
            else:
                im2 = self.slice_images[key2]
                im2.set_data(fft_abs.T)
                vmin = float(np.min(fft_abs))
                vmax = float(np.max(fft_abs))
                if vmin == vmax:
                    eps = 1e-12
                    vmin -= eps
                    vmax += eps
                im2.set_clim(vmin=vmin, vmax=vmax)
                ax2.set_title(f"Z Plane FFT at {idx} (Type {t})")
                ax2.set_xlabel(xlab)
                ax2.set_ylabel(ylab)
                if self.colorbars[key2] is not None:
                    self.colorbars[key2].update_normal(im2)


def main():
    app = QApplication(sys.argv)
    win = DensityExplorer()
    win.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
