import os
import uuid

#np_options =  [0, 4, 8, 16, 32, 64, 128, 256, 320, 384, 512, 768, 1024] # nps
np_options = [320, 384, 512, 768, 1024] # nps
file_id=str(uuid.uuid4())
strength_U = [-0.175]
length_radius = [2]
grafting_density = [0.06] #[0.1, 0.2, 0.3, 0.4, 0.5]
num_nanoparticles = np_options[:]
gap = [0] # [0, 4, 8, 16, 32, 64, 128, 256]
length = [32, 64, 128] # length from stacking 4 NPs and then doubling to remove any edge effects that could occur.

process = "dual"

#for NPs
if "NPs" in process:
    with open("./brushs_Umin_small_exp_r2"+file_id+".sim", 'w') as fp:
        fp.writelines("# stationary brushes + NP simulations \n")
        for line in [f"1 {U} {r} {d} {np} {g} {l}\n"
                     for U in strength_U
                     for r in length_radius
                     for d in grafting_density
                     for np in num_nanoparticles
                     for g in gap
                     for l in length]:
            fp.write(line)
if "brush" in process:
    with open("./brushs_gaps"+file_id+".sim", 'w') as fp:
        fp.writelines("# stationary brushes \n")
        for line in [f"2 {U} {r} {d} {np} {g} {l}\n"
                     for U in strength_U
                     for r in length_radius
                     for d in grafting_density
                     for np in num_nanoparticles
                     for g in gap
                     for l in length]:
            fp.write(line)
if "dual" in process:
    with open("./brushs_nps_gaps"+file_id+".sim", 'w') as fp:
        fp.writelines("# stationary brushes, NPs, Gaps\n")
        for line in [f"3 {U} {r} {d} {np} {g} {l}\n"
                     for U in strength_U
                     for r in length_radius
                     for d in grafting_density
                     for np in num_nanoparticles
                     for g in gap
                     for l in length]:
            fp.write(line)
print(file_id)
pass
