import bpy, bpy_extras
from math import *
import pprint
from mathutils import *
import random
import yaml
import json
import numpy as np
import os
from sklearn.neighbors import NearestNeighbors

class RopeRenderer:
    def __init__(self, rope_radius=0.1, rope_screw_offset=10, bezier_scale=7, bezier_subdivisions=10, save_depth=True, save_rgb=False):
        """
        Initializes the Blender rope renderer

        :param rope_radius: thickness of rope
        :type rope_radius: float
        :param rope_screw_offset: how tightly wound the "screw" texture is
        :type rope_radius: int
        :param bezier_scale: length of bezier curve
        :type bezier_scale: int
        :param bezier_subdivisions: # nodes in bezier curve - 2
        :type bezier_subdivisions: int
        :param save_rgb: if True, save_rgbs images, else just renders
        :type save_rgb: bool
        :return:
        :rtype:
        """
        self.save_rgb = save_rgb # whether to save_rgb images or not
        self.save_depth = save_depth
        self.rope_radius = rope_radius # thickness of rope
        self.rope_iterations = 1/self.rope_radius # how many "screws" are stacked lengthwise to create the rope
        self.rope_screw_offset = rope_screw_offset # how tightly wound the "screw" is
        self.bezier_scale = bezier_scale # length of bezier curve
        self.bezier_subdivisions = bezier_subdivisions # the number of splits in the bezier curve (ctrl points - 2)
        self.origin = (0, 0, 0)
        # Make objects
        self.rope = None
        self.rope_asymm = None
        self.bezier = None
        self.bezier_points = None # list of vertices in bezier curve
        self.camera = None
        # Name objects
        self.rope_name = "Rope"
        self.rope_asymm_name = "Rope-Asymmetric"
        self.bezier_name = "Bezier"
        self.camera_name = "Camera"
        # Dictionary to store pixel vals of knots (vertices)
        self.knots_info = {}
        self.i = 0

    def clear(self):
        """
        Deletes any objects or meshes in the scene
        :return:
        :rtype:
        """
        for block in bpy.data.meshes:
            if block.users == 0:
                bpy.data.meshes.remove(block)
        # for block in bpy.data.materials:
        #     if block.users == 0:
        #         bpy.data.materials.remove(block)
        # for block in bpy.data.textures:
        #     if block.users == 0:
        #         bpy.data.textures.remove(block)
        # for block in bpy.data.images:
        #     if block.users == 0:
        #         bpy.data.images.remove(block)
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()

    def add_camera(self):
        # Place a camera 'randomly' (not totally random, x and y rotation is only -pi/4 to pi/4 to avoid views of the side of the rope)
        bpy.ops.object.camera_add(location=[random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1)])
        self.camera = bpy.context.active_object
        self.camera.name = self.camera_name
        self.camera.rotation_euler = (random.uniform(-pi/4, pi/4), random.uniform(-pi/4, pi/4), random.uniform(-pi, pi))
        bpy.ops.object.light_add(type='SUN', radius=1, location=(0, 0, 0))


    def make_rigid_rope(self):
        # Join 4 circles and "twist" them to create realistic rope (See this 5 min. tutorial: https://youtu.be/xYhIoiOnPj4)
        bpy.ops.mesh.primitive_circle_add(location=self.origin)
        bpy.ops.transform.resize(value=(self.rope_radius, self.rope_radius, self.rope_radius))
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.transform.rotate(value= pi / 2, orient_axis='X')
        bpy.ops.transform.translate(value=(self.rope_radius, 0, 0))
        bpy.ops.object.mode_set(mode='OBJECT')
        for i in range(1, 4):
            bpy.ops.object.duplicate_move(OBJECT_OT_duplicate=None, TRANSFORM_OT_translate=None)
            ob = bpy.context.active_object
            ob.rotation_euler = (0, 0, i * (pi / 2))
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.join()
        self.rope = bpy.context.active_object
        self.rope.name = self.rope_name
        bpy.ops.object.modifier_add(type='SCREW')
        self.rope.modifiers["Screw"].screw_offset = self.rope_screw_offset
        self.rope.modifiers["Screw"].iterations = self.rope_iterations
        bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Screw")

    def add_rope_asymmetry(self):
        # Add a cone and icosphere at either end, to break symmetry of the rope
        bpy.ops.mesh.primitive_cone_add(location=(self.origin[0], self.origin[1] + 0.32, self.origin[2]))
        bpy.ops.transform.resize(value=(0.25, 0.25, 0.25))
        bpy.ops.transform.rotate(value= pi / 2, orient_axis='X')
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.join()
        self.rope_asymm = bpy.context.active_object
        self.rope_asymm.name= self.rope_asymm_name

    def make_bezier(self):
        # Create bezier curve
        bpy.ops.curve.primitive_bezier_curve_add(location=self.origin)
        bpy.ops.transform.resize(value=(self.bezier_scale, self.bezier_scale, self.bezier_scale))
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.curve.subdivide(number_cuts=self.bezier_subdivisions)
        bpy.ops.transform.resize(value=(1, 0, 1))
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.curve.select_all(action='SELECT')
        bpy.ops.curve.handle_type_set(type='AUTOMATIC')
        bpy.ops.object.mode_set(mode='OBJECT')
        self.bezier = bpy.context.active_object
        self.bezier_points = self.bezier.data.splines[0].bezier_points
        self.bezier.name = self.bezier_name
        self.bezier.select_set(False)
        self.rope_asymm.select_set(True)
        bpy.context.view_layer.objects.active = self.rope_asymm
        # Add bezier curve as deform modifier to the rope
        bpy.ops.object.modifier_add(type='CURVE')
        self.rope_asymm.modifiers["Curve"].deform_axis = 'POS_Z'
        self.rope_asymm.modifiers["Curve"].object = self.bezier
        bpy.ops.object.mode_set(mode='EDIT')
        # Adding a curve can mess up surface normals of rope, re-point them outwards
        bpy.ops.mesh.normals_make_consistent(inside=False)
        bpy.ops.object.mode_set(mode='OBJECT')

    def make_simple_loop(self, offset_min, offset_max):
        # Make simple cubic loop (4 control points)  + 2 more control points to pull slack through the loop
        p0 = np.random.choice(range(len(self.bezier_points) - 5))
        y_shift = random.uniform(offset_min, offset_max)
        self.bezier_points[p0 + 1].co.y += y_shift
        self.bezier_points[p0 + 2].co.y += y_shift
        self.bezier_points[p0 + 2].co.z += self.rope_radius
        self.bezier_points[p0 + 1].co.x, self.bezier_points[p0 + 2].co.x = self.bezier_points[p0 + 2].co.x, self.bezier_points[p0 + 1].co.x
        self.bezier_points[p0 + 4].co.x = (self.bezier_points[p0 + 1].co.x + self.bezier_points[p0 + 2].co.x)/2
        self.bezier_points[p0 + 4].co.y = self.bezier_points[p0 + 1].co.y
        self.bezier_points[p0 + 4].co.z -= self.rope_radius
        self.bezier_points[p0 + 5].co = Vector((self.bezier_points[p0 + 1].co.x, (self.bezier_points[p0].co.y + self.bezier_points[p0 + 1].co.y)/2, -2*self.bezier_points[p0 + 4].co.z))
        return set(range(p0, p0 + 5))

    def make_simple_overlap(self, offset_min, offset_max):
        # Just makes a simple cubic loop
        p0 = np.random.choice(range(len(self.bezier_points) - 5))
        y_shift = random.uniform(offset_min, offset_max)
        if random.uniform(0, 1) < 0.5:
            y_shift *= -1
        self.bezier_points[p0 + 1].co.y += y_shift
        self.bezier_points[p0 + 2].co.y += y_shift
        self.bezier_points[p0 + 2].co.z += self.rope_radius
        self.bezier_points[p0 + 1].co.x, self.bezier_points[p0 + 2].co.x = self.bezier_points[p0 + 2].co.x, self.bezier_points[p0 + 1].co.x


    def randomize_nodes(self, num, offset_min, offset_max, nonplanar=False, offlimit_indices=set()):
        # Random select num knots, pull them in a random direction (constrained by offset_min, offset_max)
        knots_idxs = np.random.choice(list(set(range(len(self.bezier_points))) ^ offlimit_indices), min(num, len(self.bezier_points)), replace=False)
        for idx in knots_idxs:
            knot = self.bezier_points[idx]
            offset_y = random.uniform(offset_min, offset_max)
            offset_x = random.uniform(offset_min/2, offset_max/2)
            if random.uniform(0, 1) < 0.5:
                offset_y *= -1
            if random.uniform(0, 1) < 0.5:
                offset_x *= -1
            if nonplanar:
                offset_z = random.uniform(offset_min, offset_max)
                if random.uniform(0, 1) < 0.5:
                    offset_z *= -1
                knot.co.z += offset_z
            knot.co.y += offset_y
            knot.co.x += offset_x


    def reposition_camera(self):
        # Orient camera towards the rope
        bpy.context.scene.camera = self.camera
        bpy.ops.view3d.camera_to_view_selected()

    def dist(self, p1, p2):
        return np.linalg.norm(np.array(p1) - np.array(p2))

    def closest_coord_from_list(self, p, coords):
        return min(range(len(coords)), key=lambda c: self.dist(c, p))

    def render_single_scene(self, M_pix=10, M_depth=0.2):
		# Produce a single image of the current scene, save_rgb the mesh vertex pixel coords
        scene = bpy.context.scene
        # Dependency graph used to get mesh vertex coords after deformation
        depsgraph = bpy.context.evaluated_depsgraph_get()
        rope_deformed = self.rope_asymm.evaluated_get(depsgraph)
        # Get vertices in world space
        coords = [rope_deformed.matrix_world @ v.co for v in list(rope_deformed.data.vertices)[::25]]
        print("%d Vertices" % len(coords))
        # Convert all vertices to pixel space
        pixels = {}
        scene.render.resolution_percentage = 100
        render_scale = scene.render.resolution_percentage / 100
        scene.render.resolution_x = 640
        scene.render.resolution_y = 480
        render_size = (
                int(scene.render.resolution_x * render_scale),
                int(scene.render.resolution_y * render_scale),
                )
        for i in range(len(coords)):
            coord = coords[i]
            camera_coord = bpy_extras.object_utils.world_to_camera_view(scene, self.camera, coord)
            render_scale = scene.render.resolution_percentage / 100
            scene.render.resolution_x = 640
            scene.render.resolution_y = 480
            render_size = (
                    int(scene.render.resolution_x * render_scale),
                    int(scene.render.resolution_y * render_scale),
                    )
            p = (round(camera_coord.x * render_size[0]), round(render_size[1] - camera_coord.y * render_size[1]))
            valid = True # Valid = True means 'this pixel is unoccluded'
            pixels[i] = [p, valid, camera_coord]
            # pixels[p] = [valid, camera_coord] # For each pixel, store whether it is valid + the camera coordinate (to get Z for depth comparison)
        # Run kNN on mesh vertex pixels
        neigh = NearestNeighbors(4, M_pix)
        # pixels_list = list(pixels.keys())
        pixels_list = [v[0] for v in pixels.values()]
        neigh.fit(pixels_list)
        # Prune out occluded pixels
        # for (p, q), [valid, camera_coord] in pixels.items():
        for j in pixels:
            (p, q), valid, camera_coord = pixels[j]
            if valid:
                match_idxs = neigh.kneighbors([(p, q)], 4, return_distance=False)
                for match_idx in match_idxs.squeeze().tolist()[1:]: # Get k neighbors, not including the original pixel (p, q)
                    # x, y = pixels_list[match_idx]
                    x, y = pixels[match_idx][0]
                    if pixels[match_idx][1]:
                        c1, c2 = camera_coord, pixels[match_idx][2]
                        # If one mesh vertex is below another, its pixel coord is invalid
                        if c1.z - c2.z > M_depth:
                            pixels[match_idx][1] = False
                        elif c1.z - c2.z < -M_depth:
                            pixels[j][1] = False
        final_pixs = [[v[0], v[1]] for v in pixels.values()]
        print(len(final_pixs))
        # final_pixs = [[k, v[0]] for k, v in pixels.items()]
        if self.save_rgb:
            scene.world.color = (1, 1, 1)
            scene.render.display_mode
            scene.render.engine = 'BLENDER_WORKBENCH'
            scene.display_settings.display_device = 'None'
            scene.sequencer_colorspace_settings.name = 'XYZ'
            color_filename = "{0:06d}_rgb.png".format(self.i)
            scene.render.image_settings.file_format='PNG'
            scene.render.filepath = "./images/{}".format(color_filename)
            bpy.ops.render.render(use_viewport = True, write_still=True)
        if self.save_depth:
            scene.render.engine = 'BLENDER_EEVEE'
            scene.eevee.taa_samples = 1
            scene.eevee.taa_render_samples = 1
            depth_filename = "{0:06d}_depth.png".format(self.i)
            scene.use_nodes = True
            tree = bpy.context.scene.node_tree
            links = tree.links
            render_node = tree.nodes["Render Layers"]
            norm_node = tree.nodes.new(type="CompositorNodeNormalize")
            inv_node = tree.nodes.new(type="CompositorNodeInvert")
            viewer_node = tree.nodes.new(type="CompositorNodeViewer")
            composite = tree.nodes.new(type = "CompositorNodeComposite")
            links.new(render_node.outputs["Depth"], inv_node.inputs["Color"])
            links.new(inv_node.outputs[0], norm_node.inputs[0])
            links.new(norm_node.outputs[0], composite.inputs["Image"])
            scene.render.use_multiview = False
            scene.render.filepath = "./depth_images/{}".format(depth_filename)
            bpy.ops.render.render(write_still=True)
        self.knots_info[self.i] = final_pixs
        self.i += 1


    def run(self, num_images):
        # Create new images folder to dump rendered images
        os.system('rm -rf ./images')
        os.makedirs('./images')
        for i in range(num_images):
            self.clear()
            self.add_camera()
            self.make_rigid_rope()
            self.add_rope_asymmetry()
            self.make_bezier()
            loop_indices = self.make_simple_loop(0.2, 0.3)
            self.randomize_nodes(2, 0.15, 0.35, offlimit_indices=loop_indices)
            self.reposition_camera()
            self.render_single_scene(M_pix=10)
        with open("./depth_images/knots_info.json", 'w') as outfile:
            json.dump(self.knots_info, outfile, sort_keys=True, indent=2)

if __name__ == '__main__':
    renderer = RopeRenderer(rope_radius=0.04, rope_screw_offset=10, bezier_scale=2.7, bezier_subdivisions=13, save_depth=True, save_rgb=False)
    renderer.run(1)
