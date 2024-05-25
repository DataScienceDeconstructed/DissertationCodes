
import uuid

file_id=str(uuid.uuid4())
strength_U = [-0.175*i for i in range(1,3)]
length_radius = [i for i in range(2, 5, 2)]
grafting_density = [0.03*i for i in range(1,21)]
num_nanoparticles = [64, 128, 256, 320, 384, 512, 768, 1024]

#brushs_Umin35_r2_extended
# strength_U = [-0.175*2]
# length_radius = [2]
# grafting_density = [0.03*i for i in range(1,13)]
# num_nanoparticles = [1024+64, 1024+128, 1024+256, 1024+320, 1024+384, 1024+512]

#brushs_Umin175_r4_extended
strength_U = [-0.175]
length_radius = [4]
grafting_density = [0.03*i for i in range(8,21)]
num_nanoparticles = [32,16,8,4,2]

with open("./brushs_Umin175_r4_extended"+file_id+".sim", 'w') as fp:
    fp.writelines("# stationary brushes + NP simulations")
    for line in [f"1 {U} {r} {d} {np}\n" for U in strength_U for r in length_radius for d in grafting_density for np in num_nanoparticles]:
        fp.write(line)

pass
