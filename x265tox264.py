"""----------------------------------------------------------------------------------
Imports (do not change)
----------------------------------------------------------------------------------"""
import datetime
import os
import os.path
import subprocess
import sys
import requests

"""=====================================================================================================================
conv2mp4

This Python script will recursively search through */NiehausConvert/Convert file path and convert all videos types specified 
in file_types to MP4 with H264 video using ffmpeg if it is not in H264. 
========================================================================================================================

---------------------------------------------------------------------------------------------------------------------"""

#Set static variables
Base_Path = os.path.dirname(os.path.abspath(__file__))
media_path = Base_Path + '/Convert/'
file_types = '.mkv', '.avi', '.flv', '.mpeg', '.ts', '.mp4'
log_path = Base_Path +'/Log/'
log_name = "NiehausConvert.log"
ffmeg_bin_dir = Base_Path + '/ffmpeg/bin'
ffmpeg_exe = "ffmpeg.exe"
ffprobe_exe = "ffprobe.exe"
garbage = '.sub', '.sfv', '.smi', '.srt', '.nfo', '.ini','.png','.PNG', '.idx', '.txt', '.jpg', '.png', '.bmp', '.JPG'

# Print initial wait notice to console
print "\n Larry Johnson's 'Swiggity Swiles, Converting The Files"
print "-----------------------------------------------------------------\n"
print "Building file list, please wait. This may take a while, especially for large libraries.\n"

# Get current time to store as start time for script
script_dur_start = datetime.datetime.now().strftime('%H:%M:%S')

# Build file paths to executables
ffmpeg = os.path.join(ffmeg_bin_dir, ffmpeg_exe)
ffprobe = os.path.join(ffmeg_bin_dir, ffprobe_exe)
log = os.path.join(log_path, log_name)

# Initialize minimum and maximum compression variables
min = 27
max = 30
"""---------------------------------------------------------------------------------------------------------------------
Classes
---------------------------------------------------------------------------------------------------------------------"""


# Logging and console output
class Tee(object):
	def __init__(self, *targets):
		self.targets = targets

	def write(self, obj):
		for ftarg in self.targets:
			ftarg.write(obj)
			ftarg.flush()  # If you want the output to be visible immediately


ftarg = open(log, 'w')
original = sys.stdout
sys.stdout = Tee(sys.stdout, ftarg)

"""---------------------------------------------------------------------------------------------------------------------
General functions (do not change)
---------------------------------------------------------------------------------------------------------------------"""


# List files in the queue in the log
def list_targets():
	global queue_Count, queue_list
	queue_Count = 0
	queue_list = ''
	check_path = os.path.exists(media_path)
	if not check_path:
		print "Path not found: " + media_path
		print "Ensure your media_path exists and is accessible."
		print "Aborting script."
		exit()
	else:
		for root, dirs, targets in os.walk(media_path):
			for target_name in targets:
				if target_name.endswith(file_types):
					queue_Count += 1
					fullpath = os.path.normpath(os.path.join(str(root), str(target_name)))
					queue_list = queue_list + "\n" + (str(queue_Count) + ': ' + fullpath)
		if queue_Count == 1:
			print ("There is " + str(queue_Count) + " file in the queue:")
		elif queue_Count > 1:
			print ("There are " + str(queue_Count) + " files in the queue:")
		else:
			print ("There are no files to be converted in " + media_path + ". Congrats!")
		print queue_list


# Make time human-readable
def humanize_time(secs):
	if secs != "N/A":
		mins, secs = divmod(int(secs), 60)
		hours, mins = divmod(mins, 60)
		return '%02d:%02d:%02d' % (hours, mins, secs)
	else:
		mins, secs = divmod(30, 60)
		hours, mins = divmod(mins, 60)
		return '%02d:%02d:%02d' % (hours, mins, secs)




# Find out what video codec a file is using
def codec_discovery():
	global get_vid_codec

	# Check video codec with ffprobe
	cmnd = [ffprobe, '-show_streams', '-select_streams', 'v:0', '-pretty', '-loglevel', 'quiet', old_file]
	p = subprocess.Popen(cmnd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	out, err = p.communicate()
	for line in out.split('\n'):
		if 'codec_name' in line:
			line = line.split('=')
			get_vid_codec = line[1].strip() 


# Delete garbage files
def garbage_collection():
	global garbage_count, garbage_list
	garbage_count = 0
	garbage_list = ''
	for root, dirs, targets in os.walk(media_path):
		for target_name in targets:
			if target_name.endswith(garbage):
				garbage_count += 1
				fullpath = os.path.normpath(os.path.join(str(root), str(target_name)))
				garbage_list = garbage_list + "\n" + (str(garbage_count) + ': ' + fullpath)
				os.remove(fullpath)
	if garbage_count == 0:
		print ("\nGarbage Collection: There was no garbage found!")
	elif garbage_count == 1:
		print ("\nGarbage Collection: The following file was deleted:")
	else:
		print ("\nGarbage Collection: The following " + str(garbage_count) + " files were deleted:")
	print garbage_list



"""---------------------------------------------------------------------------------------------------------------------
File conversion functions
---------------------------------------------------------------------------------------------------------------------"""


# If a file video codec is already H264, and container is not .mp4 or .mkv, use these arguments
def simple_convert():
	print (datetime.datetime.now().strftime(
		'%m/%d/%Y %H:%M:%S') + " Video: " + get_vid_codec.upper()
		   + " . Performing simple container conversion to MP4.")

	ff_args = (" -i " + '"'+ old_file.replace(r'\\', r'\\\\')+'"' + " -c:v copy -c:a copy  " + '"' + new_file + '"')
	subprocess.Popen(ffmpeg + ff_args, stdout=subprocess.PIPE).stdout.read()


# If a file video codec is not already H264, use these arguments
def encode_video(min, max):
	print (datetime.datetime.now().strftime('%m/%d/%Y %H:%M:%S') + " Video: " + get_vid_codec.upper()
		   +  ". Encoding video to H264 using minimum value " + str(min) + " and maximum value " + str(max) + ":" )
	ff_args = (" -i " + '"'+ old_file.replace(r'\\', r'\\\\')+'"' + " -c:v h264_nvenc -profile:v 0 -preset 0 -rc-lookahead:v 5 -2pass true -qmin:v "+ str(min) +" -qmax:v "+ str(max) + " -c:a copy "
			   + '"' + new_file + '"')
	subprocess.Popen(ffmpeg + ff_args, stdout=subprocess.PIPE).stdout.read()


"""---------------------------------------------------------------------------------------------------------------------
Preparation 
---------------------------------------------------------------------------------------------------------------------"""
# Clear log contents
open(log, 'w').close()

"""---------------------------------------------------------------------------------------------------------------------
Begin search loop 
---------------------------------------------------------------------------------------------------------------------"""

print "\nconvert Niehaus By Larry Johnson"
print "-----------------------------------------------------------------\n"
# List files that are in queue, in the log
list_targets()

# Begin performing operations on files
i = 0
for root, dirs, targets in os.walk(media_path):
	print(root)
	for target_name in targets:
		print(target_name)
		if target_name.endswith(file_types):
			i = (i + 1)
			old_file = os.path.normpath(os.path.join(str(root), str(target_name)))
			if '.mp4' in old_file:
				new_file = os.path.splitext(old_file)[0] + ".H.264" + ".mp4"
			else:
				new_file = os.path.splitext(old_file)[0] + ".mp4"
			progress = float(i) / float(queue_Count) * 100
			progress = str(round(progress, 2))
			print "------------------------------------------------------------------------------------"
			print (datetime.datetime.now().strftime('%m/%d/%Y %H:%M:%S') + " Processing - " + old_file)
			print (datetime.datetime.now().strftime('%m/%d/%Y %H:%M:%S') + " File " + str(i) + " of " + str(queue_Count)
				   + " - Total queue " + str(progress) + "%")

			"""---------------------------------------------------------------------------------------------------------
			Codec discovery to determine whether video needs to be encoded
			---------------------------------------------------------------------------------------------------------"""
			codec_discovery()

			"""---------------------------------------------------------------------------------------------------------
			Begin ffmpeg conversion based on codec discovery 
			---------------------------------------------------------------------------------------------------------"""
			# Video is already H264 and container is not .mp4 or .mkv
			print(get_vid_codec)
			if target_name is not '' and target_name is not None:
				# Video is not H265
				if get_vid_codec != 'h264':
					encode_video(min, max)
					os.remove(old_file)
				elif get_vid_codec == 'h264' and not target_name.endswith('.mp4') and not target_name.endswith('.mkv') :
					simple_convert()
					os.remove(old_file)



"""---------------------------------------------------------------------------------------------------------------------
Wrap-up
---------------------------------------------------------------------------------------------------------------------"""

#Clear junk files
garbage_collection()

print ("\nFinished")
exit()


