from math import radians, sin, cos, pi
import mathutils, bpy, argparse, random, time, os,logging

logger = logging.getLogger()
logger.setLevel(logging.ERROR)
random.seed(time.time())

def check_dir_exist(path):
	if not os.path.isdir(path):
		print(path + 'not exist, make it')
		os.mkdir(path)


model_path = '/home/willer/blender_python/wlg_with_texture/'
model = "wlg.obj"
model_scale_x, model_scale_y, model_scale_z = 0.01, 0.01, 0.01
model_scale = (model_scale_x, model_scale_y, model_scale_z)

# resolution 
resolution_x, resolution_y, resolution_percentage = 512, 512, 100

# train viewport setting
alpha_low, alpha_high, alpha_interval, alpha_rand = 1, 359, 5, 5
beta_low, beta_high, beta_interval, beta_rand = 1, 89, 5, 5
gamma_low, gamma_high, gamma_interval, gamma_rand = 0, 1, 1, 0
# at single view random set lights position for several times during generating training images
light_repetition_signle_view = 10
test_repetition_signle_view = 5

# result dir
base_dir = '/media/willer/BackUp/datasets/wlg_blender/20190420_03'
check_dir_exist(base_dir)

# training data path 
train_render_path = os.path.join(base_dir, "train")
check_dir_exist(train_render_path)
train_quat_file = os.path.join(train_render_path, "result.txt")
train_render_path = os.path.join(train_render_path, '%08d.png')

# testing data path 
test_render_path = os.path.join(base_dir, "test")
check_dir_exist(test_render_path)
test_quat_file = os.path.join(test_render_path, "result.txt")
test_render_path = os.path.join(test_render_path, '%08d.png')

# light setting
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
print('create %d light at:' % light_num)
for idx in range(light_num):
	light_data = bpy.data.lamps.new('light'+str(idx), type='POINT')
	light = bpy.data.objects.new('light'+str(idx), light_data)
	scene.objects.link(light)
	light_loc = (generate_rand(light_loc_low, light_loc_high), generate_rand(light_loc_low, light_loc_high), generate_rand(light_loc_low, light_loc_high, True))
	print(light_loc)
	light.location = mathutils.Vector(light_loc)

# set a light that never change during rendering
light_data = bpy.data.lamps.new('light', type='POINT')
light = bpy.data.objects.new('light', light_data)
scene.objects.link(light)
light.location = mathutils.Vector((0, 0, 8))
print(' ')

# do the same for lights etc
scene.update()

# simulation image resolution
scene.render.resolution_x = resolution_x
scene.render.resolution_y = resolution_y
scene.render.resolution_percentage = resolution_percentage

scene.camera = camera
path = os.path.join(model_path, model)
# make a new scene with cam and lights linked
context.screen.scene = scene
bpy.ops.scene.new(type='LINK_OBJECTS')
context.scene.name = model_path

# get cameras, only one camera in the scene
cams = [c for c in context.scene.objects if c.type == 'CAMERA']
c = cams[0]

# get lights which position may change during rendering
lights = [l for l in context.scene.objects if l.type == 'LAMP' and not(l.name == 'light')]

#import model
bpy.ops.import_scene.obj(filepath=path, axis_forward='-Z', axis_up='Y', filter_glob="*.obj;*.mtl") #-Z, Y

print('scene objects:')
for o in context.scene.objects:
	print(o)
for obj in context.scene.objects:
	if obj.name in ['Camera.001'] + ['light'+str(idx) for idx in range(light_num)]:
		continue
	else:
		obj.scale = mathutils.Vector(model_scale)
#		obj.location = mathutils.Vector((0, 0.4, 0))

bpy.context.scene.render.image_settings.file_format = 'PNG'

# train images
f_quat = open(train_quat_file, 'w')
image_idx = 0

for g in range(gamma_low, gamma_high, gamma_interval):
	g = radians(float(g))
	for b in range(beta_low, beta_high, beta_interval):
		b =  radians(float(b))
		for a in range(alpha_low, alpha_high, alpha_interval):	
			a = radians(float(a))
			for _ in range(light_repetition_signle_view):
				for l in lights:
					light_loc = (generate_rand(light_loc_low, light_loc_high), generate_rand(light_loc_low, light_loc_high), generate_rand(light_loc_low, light_loc_high, True))
					l.location = mathutils.Vector(light_loc)
				c.location = mathutils.Vector((distance*cos(b)*cos(a), distance*cos(b)*sin(a), distance*sin(b)))
				point_at(c, mathutils.Vector((0, -0.4, 0)), roll = g)
				quat = c.rotation_euler.to_quaternion()
				print('image_idx: %08d, camera: (%.3f,%.3f,%.3f)' % (image_idx, a * 180. /pi, b * 180. / pi, g * 180. / pi))
				context.scene.render.filepath = train_render_path % image_idx
				bpy.ops.render.render(use_viewport = True, write_still=True)
				f_quat.write('%08d,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f\n' % (image_idx,  a * 180 /pi, b * 180 / pi, g * 180 / pi, quat[0], quat[1], quat[2], quat[3]))
				image_idx = image_idx+ 1
			
f_quat.close()

# test images
f_quat = open(test_quat_file, 'w')
image_idx = 0
for g in range(gamma_low, gamma_high, gamma_interval):
	g = radians(float(g) + (random.random()-0.5)*gamma_interval)
	for b in range(beta_low, beta_high, beta_interval):
		b =  radians(float(b) + (random.random()-0.5)*beta_interval)
		for a in range(alpha_low, alpha_high, alpha_interval):		
			a = radians(float(a) + (random.random()-0.5)*alpha_interval)
			for _ in range(test_repetition_signle_view):
				for l in lights:
					light_loc = (generate_rand(light_loc_low, light_loc_high), generate_rand(light_loc_low, light_loc_high), generate_rand(light_loc_low, light_loc_high, True))
					l.location = mathutils.Vector(light_loc)

				c.location = mathutils.Vector((distance*cos(b)*cos(a), distance*cos(b)*sin(a), distance*sin(b)))
				point_at(c, mathutils.Vector((0, -0.4, 0)), roll = g)
				quat = c.rotation_euler.to_quaternion()
				print('image_idx: %08d, camera: (%.3f,%.3f,%.3f)' % (image_idx, a * 180. /pi, b * 180. / pi, g * 180. / pi))
				context.scene.render.filepath = test_render_path % image_idx
				bpy.ops.render.render(use_viewport = True, write_still=True)
				f_quat.write('%08d,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f\n' % (image_idx,  a * 180 /pi, b * 180 / pi, g * 180 / pi, quat[0], quat[1], quat[2], quat[3]))
				image_idx = image_idx+ 1
			
f_quat.close()
