import os
import math
import matplotlib.pyplot as plt
from PIL import Image


def plot_path(result):
    plotted = []
    ax = None
    fix = None

    for a in result.plan.actions:
        if a.motion_paths is not None:
            for key in a.motion_paths:
                # print(f"  {key} -> {a.motion_paths[key]}")
                # print(f"  Map: {key.starting.type.occupancy_map}")
                map_file = key.starting.type.occupancy_map.filename
                map_path = map_file.replace(map_file.split(os.sep)[-1], "")
                path = a.motion_paths[key]
                image_file = None
                resolution = 1.0
                f = open(map_file)
                for l in f.readlines():
                    if "image: " in l:
                        image_file = map_path + os.sep + l.replace("image: ", "").strip()
                    if "resolution: " in l:
                        resolution = float(l.replace("resolution: ", "").strip())
                if image_file is not None:
                    if image_file not in plotted:
                        im = Image.open(image_file)
                        fig, ax = plt.subplots()
                        ax.imshow(im)
                        plotted.append(image_file)

                    for step in path:
                        x = step[0][0]/resolution
                        y = step[0][1]/resolution
                        w = step[0][2]
                        x_d = math.cos(w)
                        y_d = math.sin(w)
                        plt.arrow(x, im.height - y, x_d, y_d)
    plt.show()
