from unified_planning.test.examples import get_example_problems
from combined_task_motion_planning.office.test_01 import TampOffice01


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

office_tamp = TampOffice01(1).get_problem()

selected = office_tamp

# print(selected)

solver = EngineImpl()
result = solver.solve(selected)


for a in result.plan.actions:
    print(a)
    if a.motion_paths is not None:
        for key in a.motion_paths:
            # print(f"  {key} -> {a.motion_paths[key]}")
            # print(f"  Map: {key.starting.type.occupancy_map}")
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


