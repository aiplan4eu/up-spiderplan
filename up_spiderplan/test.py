from unified_planning.test.examples import get_example_problems

import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import matplotlib.patches as patches
from PIL import Image

import math

from solver import EngineImpl

problems = get_example_problems()

basic = problems["basic"].problem
basic_nc = problems["basic_nested_conjunctions"].problem
robot = problems["robot"].problem
basic_wc = problems["basic_with_costs"].problem
counter_2_50 = problems["counter_to_50"].problem
match_cellar = problems["matchcellar"].problem
robot_no_neg = problems["robot_no_negative_preconditions"].problem

tamp = problems["tamp_feasible"].problem

selected = tamp

print(selected)

solver = EngineImpl()
result = solver.solve(selected)


for a in result.plan.actions:
    print(a)
    if a.motion_paths is not None:
        for key in a.motion_paths:
            print(f"  {key} -> {a.motion_paths[key]}")
            print(f"  Map: {key.starting.type.occupancy_map}")
            map_file = key.starting.type.occupancy_map.filename
            map_path = map_file.replace(map_file.split("/")[-1], "")
            path = a.motion_paths[key]
            image_file = None
            resolution = 1.0
            f = open(map_file)
            for l in f.readlines():
                if "image: " in l:
                    image_file = map_path + "/" + l.replace("image: ", "").strip()
                if "resolution: " in l:
                    resolution = float(l.replace("resolution: ", "").strip())
            if image_file is not None:
                im = Image.open(image_file)
                fig, ax = plt.subplots()
                ax.imshow(im)


                for step in path:
                    x = step[0][0]/resolution
                    y = step[0][1]/resolution
                    w = step[0][2]
                    x_d = math.sin(w)
                    y_d = math.cos(w)
                    plt.arrow(x, im.height - y, x_d, y_d)
                plt.show()
                plt.waitforbuttonpress()





# for mc in cdb.get_or_default(Sym("motion"), []):
#     if mc[0] == Sym("path") and not isinstance(mc[1], Var):
#         map_name = mc[5]
#         map_file = self.conv.map_files[map_name]
#         map_path = map_file.replace(map_file.split("/")[-1], "")
#
#         image_file = None
#         resolution = 1.0
#         f = open(map_file)
#         for l in f.readlines():
#             if "image: " in l:
#                 image_file = map_path + "/" + l.replace("image: ", "").strip()
#             if "resolution: " in l:
#                 resolution = float(l.replace("resolution: ", "").strip())
#         if image_file is not None:
#             print(mc)
#             img = np.asarray(Image.open(image_file))
#             imgplot = plt.imshow(img)
#             path = mc[6]
#             print(mc[6])
#             for step in path.unpack():
#                 x = step[0][0]/resolution
#                 y = step[0][1]/resolution
#                 w = step[0][2]
#
#                 x_d = math.sin(w)
#                 y_d = math.cos(w)
#
#                 plt.arrow(x, y, x_d, y_d)
#             plt.waitforbuttonpress()
#
#         print("Found path in map", map_name)
#         print("Fname:", map_file)
#
#         print(path)