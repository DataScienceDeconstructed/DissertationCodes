import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go

#base_dir = "/scratch/chdavis/exp_3_c/NP_BRUSH/Umin_-0.175/rad_2/den_0.03/den_128/den_32/NP_1024"
#base_dir = "/scratch/chdavis/exp_3_d/NP_BRUSH/Umin_-0.175/rad_2/den_0.3/gap_128/len_64/NP_4"
base_dir = "/scratch/chdavis/exp_3_d/NP_BRUSH/Umin_-0.175/rad_2/den_0.3/gap_0/len_64/NP_32"
# Example 3D numpy array

np.random.seed(0)  # Seed for reproducibility
data = np.load(base_dir+"/voxel_data.dat")
Polymer_array = data[...,0]  # grab polymers
NP_array = data[...,1]  # grab NPs

print("max values P, NPs \t", np.max(Polymer_array), " , ", np.max(NP_array))
Polymer_array = Polymer_array / np.max(Polymer_array) # normalize
NP_array = NP_array / np.max(NP_array) # normalize

# Set threshold value
threshold = 0.8

# Get indices of points above threshold
x, y, z = np.where(Polymer_array > threshold)

# Get corresponding density values
values = Polymer_array[x, y, z]

# # Create 3D scatter plot
# fig = plt.figure(figsize=(10, 7))
# ax = fig.add_subplot(111, projection='3d')
# scatter = ax.scatter(x, y, z, c=values, cmap='viridis', marker='o')
#
# # Add a color bar
# color_bar = fig.colorbar(scatter, ax=ax, label="Density")
# ax.set_xlabel('X-axis')
# ax.set_ylabel('Y-axis')
# ax.set_zlabel('Z-axis')
# ax.view_init(azim=0, elev=0)
# plt.title(f"3D Volume Visualization (Threshold > {threshold})")
# plt.show()
#axis x,y,z => 0,1,2
# look along x = sum over axis 1,2
# look along y = sum over axis 0,2
# look along z = sum over axis 0,1
x_Polymer_summed_array = Polymer_array.sum(axis=(1,2))
x_NP_summed_array = NP_array.sum(axis=(1,2))
y_Polymer_summed_array = Polymer_array.sum(axis=(0,2))
y_NP_summed_array = NP_array.sum(axis=(0,2))
z_Polymer_summed_array = Polymer_array.sum(axis=(1,0))
z_NP_summed_array = NP_array.sum(axis=(1,0))


#plt.plot(Polymer_summed_array / np.max(Polymer_summed_array))

#plt.plot(NP_summed_array / np.max(NP_summed_array))

#plt.show()

fig, axs = plt.subplots(3, sharex=True, sharey=True)
fig.suptitle('Vertically stacked subplots')
axs[0].set_ylabel('X')
axs[0].plot(x_Polymer_summed_array / np.max(x_Polymer_summed_array))
axs[0].plot(x_NP_summed_array / np.max(x_NP_summed_array))

axs[1].set_ylabel('Y')
axs[1].plot(y_Polymer_summed_array / np.max(y_Polymer_summed_array))
axs[1].plot(y_NP_summed_array / np.max(y_NP_summed_array))

axs[2].set_ylabel('Z')
axs[2].plot(z_Polymer_summed_array / np.max(z_Polymer_summed_array))
axs[2].plot(z_NP_summed_array / np.max(z_NP_summed_array))
fig.subplots_adjust(wspace=1, hspace=0.1)

plt.show()

