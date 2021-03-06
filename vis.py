import cv2
import numpy as np
import argparse
import os
import math
import json

def show_knots(idx, knots_info, save=True):
	image_filename = "{0:06d}_rgb.png".format(idx)
	print(image_filename)
	img = cv2.imread('images/{}'.format(image_filename))
	pixels = knots_info[str(idx)]
	for i in range(len(pixels)):
		for (u, v) in pixels[i]:
			val = 255 * i/len(pixels)
			color = (val, 255 - val, 255)
			cv2.circle(img,(int(u), int(v)), 1, color, -1)

	if save:
		annotated_filename = "{0:06d}_annotated.png".format(idx)
		cv2.imwrite('./annotated/{}'.format(annotated_filename), img)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--num', type=int, default=len(os.listdir('./images')) - 1)
    args = parser.parse_args()
    if not os.path.exists("./annotated"):
        os.makedirs('./annotated')
    else:
        os.system("rm -rf ./annotated")
        os.makedirs("./annotated")
    print("parsed")
    with open("images/knots_info.json", "r") as stream:
    	knots_info = json.load(stream)
    print(len(knots_info['0']))
    print("loaded knots info")
    for i in range(args.num):
	    show_knots(i, knots_info)
