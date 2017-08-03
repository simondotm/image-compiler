#!/usr/bin/env python
#
# Uses the Pillow fork of Python Imaging Library (PIL) - http://python-pillow.org/ 
#
# On Windows - 
#		Install Python 2.7
# 		Download ez_setup.py from https://bootstrap.pypa.io/ez_setup.py to C:\Python27
# 		run ez_setup.py
# 		From the \Python27\Scripts folder, run easy_install.exe pillow
# 
# On Mac -
#       pip install Pillow
#
# Author: simondotm
#         https://github.com/simondotm


import gzip
import struct
import sys
import binascii
import math
import json
import os
import PIL

from PIL import Image
import PIL.ImageOps  
  
from os import listdir
from os.path import isfile, join

# http://pillow.readthedocs.io/en/3.0.x/handbook/image-file-formats.html
OUTPUT_FORMAT = "png"
FORCE_UPDATE = True

class AssetManager:

	_database = { "source" : "", "target" : "", "root" : {} }
	_database_filename = None

	_meta = {}
	_meta_filename = None
	
	_db_folderlist = []
	_db_source_dir = None
	_db_target_dir = None
	_db_root = None

	# constructor - pass in the filename of the VGM
	def __init__(self, database_filename):
		self._database_filename = database_filename
		if not os.path.isfile(database_filename):
			print "No database exists - creating one"
			self.saveDatabase()
		
		# load the database
		self.loadDatabase()
		self.loadMeta()

		

	
	def saveDatabase(self):
		with open(self._database_filename, 'w') as outfile:
			json.dump(self._database, outfile, sort_keys = True, indent = 4, separators = (',', ': ') )	
	
	def saveMeta(self):
		with open(self._meta_filename, 'w') as outfile:
			json.dump(self._meta, outfile, sort_keys = True, indent = 4, separators = (',', ': ') )		
	
	def loadMeta(self):
		self._meta_filename = self._db_target_dir + "/meta.json"
		if not os.path.isfile(self._meta_filename):
			print "No meta file exists - creating one"
			self.saveMeta()	
		else:
			fh = open(self._meta_filename)
			self._meta = json.loads(fh.read())			
		
	def loadDatabase(self):

		fh = open(self._database_filename)
		self._database = json.loads(fh.read())
		#print self._database

		self._db_root = self._database['root']
		self._db_source_dir = self._database['source']
		self._db_target_dir = self._database['target']

		# load folder list
		for folderkey in self._db_root:
			if not folderkey in self._db_folderlist:
				self._db_folderlist.append(folderkey)

		#print "folder list"
		#print self._db_folderlist
		
		# sync database	
		print "scanning folders"
		update_db = False
		new_folders = []
		for folder, subs, files in os.walk(self._db_source_dir):
			path = folder.replace('\\', '/')
			if path.startswith(self._db_source_dir):
				sz = len(self._db_source_dir)
				path = path[sz:]
				if len(path) > 0:
					if not path in self._db_folderlist:
						self._db_folderlist.append(path)
						new_folders.append(path)
						self._db_root[path] = {}
						update_db = True

		#print "done"

		if update_db:
			self.saveDatabase()
			print str(len(new_folders)) + " new folders detected and added to database."
			print "Apply settings if desired, then re-run script to compile."
			exit()
		
	# scan source folder looking for files that are not in the database and add them
	def scanDir(self, dir):
		print ""
	
	
	def syncDatabase(self):
		files = [f for f in listdir(sourcepath) if isfile(join(sourcepath, f))]	
	
	
	
	def compile(self):
		print "Compiling assets..."
		update_count = 0
		for assetkey in self._db_root:

			asset = self._db_root[assetkey]	

			#print "'" + folder + "'"
			source_path = self._db_source_dir + assetkey + "/"
			target_path = self._db_target_dir + assetkey + "/"

			asset_is_dir = False
			if os.path.isdir(source_path):
				files = [f for f in listdir(source_path) if isfile(join(source_path, f))]
				asset_is_dir = True
				output_dir = target_path
			else:
				files = [ assetkey ]
				source_path = self._db_source_dir
				target_path = self._db_target_dir				
				output_dir = os.path.dirname(target_path + assetkey)
				#print output_dir
				#print files
			
			# make the target directory if it doesn't exist
			if not os.path.exists(output_dir):
				os.makedirs(output_dir)

			
							
			for file in files:
			

				#print "'" + file + "'"
				
				# if we're processing a directory, skip any files we come across that have been added individually to the database
				asset_file = assetkey + "/" + file
				if asset_is_dir and asset_file in self._db_root:
					#print "Skipping overridden asset"
					continue				
				
				source_file = source_path + file
				target_file = target_path + file



				# determine if we need to synchronise the asset based on :
				#     target is missing
				#     target is older than source
				#     asset meta data is absent
				#     asset settings have changed since last compile
				#
				
				update_asset = FORCE_UPDATE
				update_meta = FORCE_UPDATE
				
				# TODO: missing source file should trigger some cleanup of meta data & output files
				if isfile(source_file):
				
					#print source_file + ", " + target_file				
					if not isfile(target_file):
						update_asset = True
					else:
						if os.path.getctime(target_file) < os.path.getctime(source_file):
							update_asset = True
					
					# Trigger update of output AND metadata file if this asset isn't yet in our meta data
					if not target_file in self._meta:
						print "Adding meta file '" + target_file + "'"
						self._meta[target_file] = {}
						update_meta = True
						update_asset = True
					
					# get compile options for this asset
					#   scale - % resample
					#   width - fixed pixel width, will scale up or down
					#   height - fixed pixel height, will scale up or down
					#   retina - output N upsampled versions of the asset, 1 = @2x, 2 = @4x, 3 = @8x etc.
					#   square - force output image to be square (adds padding on smallest dimension)
					#   pad - ensure a % sized border exists (if square is selected, this border will be incorporated)
					#	palette - reduce image to N colour palette (indexed) image
					#	invert - invert image
					#	alpha - export image using just alpha channel info
					#
					#  If only width or height is specified, aspect is maintained
					#  If width AND height is specified, aspect is not maintained
					#  Width or Height overrides scale
					# 
					asset_options = { 'scale' : 0, 'width' : 0, 'height' : 0, 'retina' : 0, 'square' : 0, 'pad' : 0, 'palette' : 0, 'invert' : 0, 'alpha' : 0 }
					#option_scale = 0
					#option_width = 0
					#option_height = 0
					
					#if 'scale' in asset:	option_scale = asset['scale']
					#if 'width' in asset:	option_width = asset['width']
					#if 'height' in asset:	option_height = asset['height']			
				
					for option in asset:
						if option in asset_options:
							asset_options[option] = asset[option]
					

						
					# Also trigger update if compile options have changed for this asset since last compilation
					meta_asset = self._meta[target_file]
					#print "file '" + target_file + "' meta '" + str(meta_asset) + "'"
					def checkObjectForUpdate(obj, key, value):
						#print "checking " + key
						if not key in obj:
							#print "failed key match"
							return True
						else:
							if obj[key] != value:
								#print "failed value match '" + str(obj[key]) + "' != '" + str(value) + "'"
								return True
						return False
						
					#if checkObjectForUpdate(meta_asset, 'scale', option_scale): update_asset = update_meta = True
					#if checkObjectForUpdate(meta_asset, 'width', option_width): update_asset = update_meta = True
					#if checkObjectForUpdate(meta_asset, 'height', option_height): update_asset = update_meta = True
					
					# scan the asset's options, compare with meta data options, and detect any differences
					for option in asset_options:
						if checkObjectForUpdate(meta_asset, option, asset_options[option]):
							update_asset = True
							update_meta = True					

					

					# process asset if it needs to be updated
					if update_asset:
					
						print "Updating '" + target_file + "'"



						option_scale = asset_options['scale']
						option_width = asset_options['width']
						option_height = asset_options['height']
						option_retina = asset_options['retina']
						option_square = asset_options['square']
						option_pad = asset_options['pad']
						option_palette = asset_options['palette']
						option_invert = asset_options['invert']
						option_alpha = asset_options['alpha']
						
						# compile the image
						img = Image.open(source_file)					
						iw = img.size[0]
						ih = img.size[1]		

						
						# invert image if required
						if option_invert != 0:
							if img.mode == 'RGBA':
								r,g,b,a = img.split()
								rgb_image = Image.merge('RGB', (r,g,b))

								inverted_image = PIL.ImageOps.invert(rgb_image)

								r2,g2,b2 = inverted_image.split()

								final_transparent_image = Image.merge('RGBA', (r2,g2,b2,a))
								img = final_transparent_image

							else:
								inverted_image = PIL.ImageOps.invert(img)
								img = inverted_image
				
						# create a white mask image using the source image alpha channel
						if option_alpha != 0:
							if img.mode == 'RGBA':
								r,g,b,a = img.split()
								white_image = Image.new('RGB', (img.width, img.height), (255,255,255))
								wr, wg, wb = white_image.split()							
									
								#rgba_image = Image.merge('RGBA', (r,g,b,a))	
								rgba_image = Image.merge('RGBA', (wr,wg,wb,a))
								img = rgba_image
						
						
						# force image to be square and/or padded
						if option_square != 0 or option_pad != 0:

							rw = iw
							rh = ih

							pad_x = 0
							pad_y = 0
							if option_pad != 0:
								#print "n"

								pad_x = (option_pad * rw / 100) * 2
								pad_y = (option_pad * rh / 100) * 2
								#print "image w=" + str(rw) + " h=" + str(rh) + " padx=" + str(pad_x) + " pady=" + str(pad_y)
								rw += pad_x
								rh += pad_y
								#print "new image w=" + str(rw) + " h=" + str(rh) + " padx=" + str(pad_x) + " pady=" + str(pad_y)
								#xoffset += pad_x / 2
								#yoffset += pad_y / 2
							
							if option_square != 0 and rw != rh:
								#print "do squaring"
								if rw > rh:
									pad_y += (rw - rh)
									rh = rw
									#print "square image w=" + str(rw) + " h=" + str(rh) + " padx=" + str(pad_x) + " pady=" + str(pad_y)
									#print "a"
								else:	
									pad_x += (rh - rw)
									rw = rh
									#print "square image w=" + str(rw) + " h=" + str(rh) + " padx=" + str(pad_x) + " pady=" + str(pad_y)
									#print "b"
							
							xoffset = pad_x / 2
							yoffset = pad_y / 2


								
					
							imode = img.mode
							if imode != 'RGBA':
								imode = 'RGB'

							print "arse " + imode
							#print "square to " + str(rw) + " x " + str(rh) + " xoff=" + str(xoffset) + " yoff=" + str(yoffset)
							
							# create a new blank canvas at the target size and copy the original image to its centre
							#c = img.getpixel((0,0))	# use the top left colour of the image as the bg color
							c = (0,0,0,0) # use transparent colour as the pad bg color
							newimg = Image.new(imode, (rw, rh), c) 
							newimg.paste(img, (xoffset, yoffset, xoffset+iw, yoffset+ih) )
							img = newimg
							
							iw = img.size[0]
							ih = img.size[1]		

						# apply image scaling - scale, width or height
						scale_ratio_x = 1.0
						scale_ratio_y = 1.0

						if option_scale != 0:
							scale_ratio_x = scale_ratio_y = float(option_scale) / 100.0
						else:	
							if option_width != 0 and option_height == 0:
								scale_ratio_x = scale_ratio_y = float(option_width) / float(iw)
							else:	
								if option_width == 0 and option_height != 0:
									scale_ratio_x = scale_ratio_y = float(option_height) / float(ih)
								else:
									if option_width !=0 and option_height != 0:
										scale_ratio_x = float(option_width) / float(iw)
										scale_ratio_y = float(option_height) / float(ih)
										
						# apply image scaling - scale, width or height
						ow = iw
						oh = ih
						if scale_ratio_x != 1.0 or scale_ratio_y != 1.0:
							ow = int( round( float(iw) * scale_ratio_x ) )
							oh = int( round( float(ih) * scale_ratio_y ) )
							
						
						# we only handle retina for images that are being resized
						if ow != iw or oh != ih:
						
							# if retina option is selected we create variant of the image at multiples of 2x target resolution
							if option_retina != 0:
							
								levels = option_retina
								while levels > 0:
									retina_scale = pow(2, levels)
									retina_w = ow * retina_scale
									retina_h = oh * retina_scale
									
									if retina_w > iw or retina_h > ih:
										print "WARNING: Output retina image at " + str(retina_scale) + "x exceeds source image size - quality will be compromised"
										
									img_retina = img.resize((retina_w, retina_h), PIL.Image.ANTIALIAS)
									
									# convert to indexed palette format if required									
									if option_palette != 0:
										img_retina = img_retina.quantize(option_palette)
									
									
									
									ext_offset = target_file.rfind('.')
									output_filename = target_file[:ext_offset] + "@" + str(retina_scale) + "x" + "." + OUTPUT_FORMAT #target_file[ext_offset:]
									img_retina.save(output_filename, OUTPUT_FORMAT)
									
									# for each retina level required
									levels -= 1
								
							# resample the image to target size
							img = img.resize((ow, oh), PIL.Image.ANTIALIAS)						
						
						# convert to indexed palette format if required
						# TODO: should use convert - http://pillow.readthedocs.io/en/3.0.x/reference/Image.html?highlight=quantize#PIL.Image.Image.convert
						if option_palette != 0:
							img = img.quantize(option_palette)	
							#img = img.convert("P", colors=2, dither=1)#, colors=option_palette, dither=Image.FLOYDSTEINBERG)				

						# save the processed image
						ext_offset = target_file.rfind('.')
						output_filename = target_file[:ext_offset] + "." + OUTPUT_FORMAT
						img.save(output_filename, OUTPUT_FORMAT)
						
						# update meta data
						meta_asset['scale'] = option_scale
						meta_asset['width'] = option_width
						meta_asset['height'] = option_height
						meta_asset['retina'] = option_retina
						meta_asset['square'] = option_square
						meta_asset['pad'] = option_pad
						meta_asset['palette'] = option_palette
						meta_asset['invert'] = option_invert
						meta_asset['alpha'] = option_alpha
						
						# output some metrics of processed file
						meta_asset['output_width'] = ow
						meta_asset['output_height'] = oh
						
						# save meta file each update in case script is interrupted
						if update_meta:
							#print "saving meta data"
							self.saveMeta()
					
						update_count += 1
						
		print "Complete - updated " + str(update_count) + " files"

					

		
		

	
	
	
	

	def processLetters(self, sourcepath, targetpath = None):

		files = [f for f in listdir(sourcepath) if isfile(join(sourcepath, f))]
		print files
		
		image_library = []
		max_w = 0
		max_h = 0
		max_s = 0
		largest_size_id = None
		largest_width_id = None
		largest_height_id = None
		for file in files:
			filename = sourcepath + file

			im = Image.open(filename)
			w = im.size[0]
			h = im.size[1]
			s = w*h
			
			image_object = {}
			image_object['path'] = sourcepath
			image_object['filename'] = file
			image_object['width'] = w
			image_object['height'] = h
			image_object['pixels'] = s
			image_object['image'] = im
			
			image_library.append(image_object)

			if w > max_w: 
				max_w = w
				largest_width_id = len(image_library)

			if h > max_h: 
				max_h = h
				largest_height_id = len(image_library)		
			
			if s > max_s:
				max_s = s
				largest_size_id = len(image_library)

			
			print "'" + file + "', w=" + str(w) + " h=" + str(h)
			data = im.getdata()
			
		print "Loaded " + str(len(image_library)) + " images"
		
		io = image_library[largest_size_id]
		print "Largest size image is '" + io['filename'] + "', w=" + str(io['width']) + ", h=" + str(io['height'])
		
		io = image_library[largest_width_id]
		print "Largest width image is '" + io['filename'] + "', w=" + str(io['width']) + ", h=" + str(io['height'])	

		io = image_library[largest_height_id]
		print "Largest height image is '" + io['filename'] + "', w=" + str(io['width']) + ", h=" + str(io['height'])	
	

		
	
#----------------------------------------------------------------------------------------------------------------------------
# main
#----------------------------------------------------------------------------------------------------------------------------
	
	

#print "hello world"

asset_manager = AssetManager("assets.json")
asset_manager.compile()



#asset_manager.processLetters("assets/_PLAIN_LETTERS_PNG/_PLAIN_LETTERS_PNG/")