# rope-rendering

### Dependencies
All in Python3:
* Blender (beta version 2.8) (Download here: https://www.blender.org/download/Blender2.80/blender-2.80-macOS.dmg/)
* cv2
* argparse
* scipy
* sklearn
* numpy

### Description
* This repo hosts rendering scripts for the dense descriptors for deformable objects project. 
  * `rope-blender.py`: renders images of deformable rope into directory `rope-rendering/images` and dumps a JSON file with vertex pixel info into the same folder. The rope model is based directly off https://www.youtube.com/watch?v=xYhIoiOnPj4
  * `vis.py`: loads a set of images and a JSON file from `rope-rending/images` and highlights all the vertex pixels in the JSON file on each image. Dumps annotated images into `rope-rendering/annotated`
  * `mask.py`: renders a visible mask (255's and 0's) and non-visible mask (1's and 0's) of each image and dumps them to `rope-rendering/image_masks.` This is used to generate non-matches both on and off the rope during training.
  * `process-sim.py`: hacks the sim images to make them look like `real_images`

### Setup
* After downloading Blender version 2.8, do the following steps:
* Add the following line to your .bashrc: 
  * `alias blender="/Users/priyasundaresan/Downloads/blender-2.80.0-git20190620.d30f72dfd8ac-x86_64/blender.app/Contents/MacOS/blender"` replacing the path to blender.app with your downloaded version
* `cd` into the following directory: `/Users/priyasundaresan/Downloads/blender-2.80.0-git20190620.d30f72dfd8ac-x86_64/blender.app/Contents/Resources/2.80/python/bin`
* To install dependencies, optionally make a python3 virtualenv, navigate into `rope-rendering` and run pip3 install -r requirements.txt

### Rendering Usage
* Off-screen rendering: run `blender -b -P rope-blender.py` (-b signals --background, -P signals --python)
* On-screen rendering: run `blender -P rope-blender.py`
* For debugging purposes, you can also open a scripting window in Blender (on the top nav-bar menu, look for `Scripting`), click `+New`, copy the contents of `rope-blender.py` and hit `Run Script`
  * To manually deform the rope, select the spline in `'EDIT'` mode (by pressing `Tab`), press `'G'`, and grab any of the spline nodes with a mouse to move the rope. You can select groups of nodes at a time by pressing `'Ctrl'` while grabbing nodes.

### Example Workflow
* Run `blender -b -P rope-blender.py`
* Run `python3 vis.py` to visualize the vertex correspondences
* Run `python3 mask.py` to produce masks of images
* Run `python3 process_sim.py` to add noise to the sim images (can compare to images in `real_images` to see the result)
