import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Qt5Agg")

base_dir = "/scratch/chdavis/exp_4/NP_BRUSH/Umin_-0.175/rad_2/den_0.1/gap_0/len_32/NP_320"

voxels = np.load(base_dir + "/voxel_data.dat", allow_pickle=False)
# Check shape
print("Array shape:", voxels.shape)  # should be (Nx, Ny, Nz, 2)

# Globals to track current selection
z_index = 0
particle_type = 0

# FFT function
def compute_fft(z, t):
    """Compute abs FFT over x,y for fixed z and type"""
    slice_xy = voxels[:, :, z, t]
    slice_xy = slice_xy - np.mean(slice_xy)
    fft2d = np.fft.fftshift(np.fft.fft2(slice_xy))
    return np.abs(fft2d)

# Initial data
fft_abs = compute_fft(z_index, particle_type)

fig, ax = plt.subplots()
im = ax.imshow(fft_abs, cmap="inferno", origin="lower")
title = ax.set_title(f"z = {z_index}, type = {particle_type}")
plt.colorbar(im, ax=ax)

def update_display():
    fft_abs = compute_fft(z_index, particle_type)
    im.set_data(fft_abs)
    im.set_clim(vmin=fft_abs.min(), vmax=fft_abs.max())
    title.set_text(f"z = {z_index}, type = {particle_type}")
    fig.canvas.draw_idle()

def on_key(event):
    global z_index, particle_type
    if event.key == "right":  # increase z
        if z_index < voxels.shape[2] - 1:
            z_index += 1
            update_display()
    elif event.key == "left":  # decrease z
        if z_index > 0:
            z_index -= 1
            update_display()
    elif event.key == "t":  # toggle type
        particle_type = 1 - particle_type
        update_display()

fig.canvas.mpl_connect("key_press_event", on_key)
plt.show(block=True)