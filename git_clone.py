import os
import stat
import shutil
import subprocess

class GitClone:
	def __init__(self, url, clone_dir, working_dir):
		self.url = url
		self.clone_dir = clone_dir
		self.working_dir = working_dir

	def change_permissions(self, path):
		for root, dirs, files in os.walk(path):
			for d in dirs:
				os.chmod(os.path.join(root, d), stat.S_IRWXU)
			for f in files:
				os.chmod(os.path.join(root, f), stat.S_IRWXU)
	
	def clone(self):
		# first check the path and delete previous clone
		self.change_permissions(self.clone_dir)
		if os.path.exists(self.working_dir):
			shutil.rmtree(self.working_dir)

		os.makedirs(self.working_dir, exist_ok=True)
		# clone the repository
		try:
			subprocess.run(['git', 'clone', self.url, self.working_dir])
			print(f'[INFO] Repository cloned to {self.working_dir}')
			return True
		except Exception as e:
			print(f'[ERROR] while cloning repository: {e}')

# test it

# url = 'http://192.168.1.127/assemblyline/gw100_gw10_assemblyline.git'
# clone_dir = 'C:\\Users\\Jesse\\Desktop\\clone\\'
# working_dir = 'C:\\Users\\Jesse\\Desktop\\clone\\working\\'

# git = GitClone(url, clone_dir, working_dir)
# git.clone()
