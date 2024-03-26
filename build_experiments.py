
import uuid

file_id=str(uuid.uuid4())
strength_U = [-0.175*i for i in range(1,3)]
length_radius = [i for i in range(2, 5, 2)]
grafting_density = [0.03*i for i in range(1,21)]
num_nanoparticles = [64, 128, 256, 320, 384, 512, 768, 1024]

with open("./brushs"+file_id+".sim", 'w') as fp:
    fp.writelines("# stationary brushes + NP simulations")
    for line in [f"1 {U} {r} {d} {np}\n" for U in strength_U for r in length_radius for d in grafting_density for np in num_nanoparticles]:
        fp.write(line)

pass
