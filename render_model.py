from math import radians, sin, cos, pi
import mathutils, bpy, argparse, random, time, os,logging

logger = logging.getLogger()
logger.setLevel(logging.ERROR)
random.seed(time.time())

light_num_low, light_num_high = 1, 2
light_loc_low, light_loc_high = 3, 6

def generate_rand(a=0, b=1, only_positive=False):
	x = (random.random()-0.5) * 2*b
	if abs(x) < a or (only_positive and x<0):
		return generate_rand(a, b, only_positive)
	else:
		return x
    

def point_at(obj, target, roll=0):
	"""
	Rotate obj to look at target

	:arg obj: the object to be rotated. Usually the camera
	:arg target: the location (3-tuple or Vector) to be looked at
	:arg roll: The angle of rotation about the axis from obj to target in radians. 

	Based on: https://blender.stackexchange.com/a/5220/12947 (ideasman42)      
	"""
	if not isinstance(target, mathutils.Vector):
		target = mathutils.Vector(target)
	loc = obj.location
	# direction points from the object to the target
	direction = target - loc

	quat = direction.to_track_quat('-Z', 'Y')

	# /usr/share/blender/scripts/addons/add_advanced_objects_menu/arrange_on_curve.py
	quat = quat.to_matrix().to_4x4()
	rollMatrix = mathutils.Matrix.Rotation(roll, 4, 'Z')

	# remember the current location, since assigning to obj.matrix_world changes it
	loc = loc.to_tuple()
	obj.matrix_world = quat * rollMatrix
	obj.location = loc

context = bpy.context

model_path = '/home/willer/blender_python/wlg_with_texture/'
model = "wlg.obj"
render_path = "/home/willer/blender_python/test.png"


#create a scene
scene = bpy.data.scenes.new("Scene")
camera_data = bpy.data.cameras.new("Camera")
camera = bpy.data.objects.new("Camera", camera_data)

distance, alpha, beta, gamma = 4.0, 1.0, 89.0, 0.0
alpha, beta, gamma = radians(alpha), radians(beta), radians(gamma)

# camera.location = mathutils.Vector((0, 0, 4))
camera.location = mathutils.Vector((distance*cos(beta)*cos(alpha), distance*cos(beta)*sin(alpha), distance*sin(beta)))
#camera.rotation_euler = mathutils.Euler((radians(45), 0, 0.0),'XYZ')
point_at(camera, mathutils.Vector((0, -0.4, 0)), roll = gamma)
print('camera by looked_at', camera.location, camera.rotation_euler, camera.rotation_euler.to_quaternion())

scene.objects.link(camera)

# Create lights
light_num = random.randint(a=light_num_low, b=light_num_high)
print('create %d light at:', light_num)
for idx in range(light_num):
	light_data = bpy.data.lamps.new('light'+str(idx), type='POINT')
	light = bpy.data.objects.new('light'+str(idx), light_data)
	scene.objects.link(light)
	light_loc = (generate_rand(light_loc_low, light_loc_high), generate_rand(light_loc_low, light_loc_high), generate_rand(light_loc_low, light_loc_high, True))
	print(light_loc)
	light.location = mathutils.Vector(light_loc)

light_data = bpy.data.lamps.new('light', type='POINT')
light = bpy.data.objects.new('light', light_data)
scene.objects.link(light)
light.location = mathutils.Vector((0, 0, 8))

print(' ')

# do the same for lights etc
scene.update()

scene.render.resolution_x = 512
scene.render.resolution_y = 512
scene.render.resolution_percentage = 100

scene.camera = camera
path = os.path.join(model_path, model)
# make a new scene with cam and lights linked
context.screen.scene = scene
bpy.ops.scene.new(type='LINK_OBJECTS')
context.scene.name = model_path
cams = [c for c in context.scene.objects if c.type == 'CAMERA']
print(cams)
#import model
bpy.ops.import_scene.obj(filepath=path, axis_forward='-Z', axis_up='Y', filter_glob="*.obj;*.mtl") #-Z, Y

print('scene objects:')
for o in context.scene.objects:
	print(o)
for obj in context.scene.objects:
	if obj.name in ['Camera.001'] + ['light'+str(idx) for idx in range(light_num)]:
		continue
	else:
		obj.scale = mathutils.Vector((0.01, 0.01, 0.01))
#		obj.location = mathutils.Vector((0, 0.4, 0))

c = cams[0]

bpy.context.scene.render.image_settings.file_format = 'PNG'
render_path = "/home/willer/blender_python/render_images/%08d.png"
quat_file = "/home/willer/blender_python/render_images/result.txt"
f_quat = open(quat_file, 'w')
image_idx = 0
for g in range(1, 89, 10):
	g = radians(float(g))
	for b in range(1, 89, 10):
		b =  radians(float(b))
		for a in range(1, 179, 20):		
			a = radians(float(a))
			c.location = mathutils.Vector((distance*cos(b)*cos(a), distance*cos(b)*sin(a), distance*sin(b)))
			point_at(c, mathutils.Vector((0, -0.4, 0)), roll = g)
			quat = c.rotation_euler.to_quaternion()
			print('image_idx: %08d, camera: (%.3f,%.3f,%.3f)' % (image_idx, a * 180. /pi, b * 180. / pi, g * 180. / pi))
			context.scene.render.filepath = render_path % image_idx
			bpy.ops.render.render(use_viewport = True, write_still=True)
			f_quat.write('%08d,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f\n' % (image_idx, quat[0], quat[1], quat[2], quat[3], a * 180 /pi, b * 180 / pi, g * 180 / pi))
			image_idx = image_idx+ 1
			
f_quat.close()
