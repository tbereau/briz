'''ssh computer cluster and run job'''

import ConfigParser
import paramiko
import os

class RunCommandRemotely:
	'''Run remote command on server'''
	def __init__(self, server, subdir=''):
		self.config   = ConfigParser.RawConfigParser()
		hostsFile = __file__[:__file__.rfind("/")] + "/hosts.ini"
		self.config.read(hostsFile)	

		self.locdir    = os.getcwd()
		self.server    = server
		self.hostname  = self.config.get(server, 'hostname')
		self.username  = self.config.get(server, 'user')
		self.workdir   = self.config.get(server, 'workdir')
		self.subdir    = subdir
		self.remdir    = ''
		self.pkeyfile  = os.path.expanduser('~/.ssh/id_rsa')
		self.mykey     = paramiko.RSAKey.from_private_key_file(
			self.pkeyfile)
		self.trnsprt   = paramiko.Transport((self.hostname, 22))
		self.trnsprt.connect(username=self.username, pkey=self.mykey)
		self.sftp      = paramiko.SFTPClient.from_transport(self.trnsprt)
		self.ssh       = paramiko.SSHClient()
		self.stdin     = ''
		self.stdout    = ''
		self.stderr    = ''
		self.maxtrials = 20

		self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

		# Connect to remote server, choose directory, and create working directory
		self.chooseDir()


	def connectSSH(self):
		if hasattr(self.ssh,"is_active") is False:
			self.ssh.connect(self.hostname, username=self.username)
			print "SSH connection to",self.hostname,"established" 

	def disconnectSSH(self):
		if hasattr(self.ssh,"is_active"):
			self.ssh.close()

	def chooseDir(self):
		'''Determine unused directory on remote server'''
		self.connectSSH()

		if self.subdir == "":
			freeDir = False
			dirCounter = 0
			dirName = ''
			while freeDir is False:
				dirName = "dir%06d" % dirCounter
				sin, sout, serr = self.ssh.exec_command( "find " + 
					self.workdir + " -maxdepth 1 -name " + dirName + " | wc -l")
				stat = sout.channel.recv_exit_status()
				if sout.readlines()[0].strip() == "0":
					freeDir = True
				dirCounter += 1
			self.subdir   = dirName
		else:
			# If folder already exists, move it to .bak
			self.execCmd( "rm -rf " + self.workdir 
				+ "/" + self.subdir + ".bak")
			self.execCmd( "mv " + self.workdir + "/" + self.subdir 
				+ " " + self.workdir + "/" + self.subdir + ".bak")
		self.remdir   = self.workdir + "/" + self.subdir
		print self.remdir
		self.execCmd("mkdir -p " + self.remdir)
		self.disconnectSSH()

	def putFile(self, myFile):
		baseFile = myFile
		if baseFile.find("/") != -1:
			baseFile = myFile[myFile.rfind("/")+1:]
		destFile = self.remdir + "/" + baseFile
		oriFile = os.path.abspath(myFile)
		trials = 0
		putSuccess = False
		while trials < self.maxtrials and putSuccess == False:
			try:
				self.sftp.put(oriFile, destFile)
			except:
				trials += 1
				continue
			break
		if trials == self.maxtrials:
			print "Error. Can't copy", myFile
			exit(1)
		print "copied",baseFile,"to the remote server"

	def getFile(self, myFile):
		baseFile = myFile
		if baseFile.find("/") != -1:
			baseFile = myFile[myFile.rfind("/")+1:]
		remFile = self.remdir + "/" + baseFile
		trials = 0
		getSuccess = False
		while trials < self.maxtrials and putSuccess == False:
			try:
				self.sftp.get(remFile, self.locdir + "/" + baseFile)
			except:
				trials += 1
				continue
			break
		if trials == self.maxtrials:
			print "Error. Can't copy", myFile
			exit(1)
		print "copied",baseFile,"from the remote server"

	def execCmd(self, cmd):
		self.stdin, self.stdout, self.stderr = self.ssh.exec_command(cmd)
		# The following is a blocking command.
		return self.stdout.channel.recv_exit_status()

	def getStdin(self):
		return self.stdin.readlines()

	def getStdout(self):
		return self.stdout.readlines()

	def getStderr(self):
		return self.stderr.readlines()

	def __del__(self):
		self.disconnectSSH()


if __name__ == "__main__":
	# Testing with verdi
	server   = 'verdi'
	cmd = "hostname; which charmmsub"
	remoteCmd = RunCommandRemotely(server, 'dir000000')
	remoteCmd.execCmd(cmd)
	remoteCmd.putFile('hosts.ini')
	remoteCmd.getFile('hosts.ini')
	print remoteCmd.getStdout()

