'''ssh computer cluster and run job'''

import ConfigParser
import paramiko
import os

config = ConfigParser.RawConfigParser()
config.read('hosts.ini')

class RunCommandRemotely:
	'''Run remote command on server'''
	def __init__(self, server, subdir=''):
		self.locdir   = os.getcwd()
		self.server   = server
		self.hostname = config.get(server, 'hostname')
		self.username = config.get(server, 'user')
		self.workdir  = config.get(server, 'workdir')
		self.subdir   = subdir
		self.remdir   = ''
		self.pkeyfile = os.path.expanduser('~/.ssh/id_rsa')
		self.mykey    = paramiko.RSAKey.from_private_key_file(
			self.pkeyfile)
		self.trnsprt  = paramiko.Transport((self.hostname, 22))
		self.trnsprt.connect(username=self.username, pkey=self.mykey)
		self.sftp     = paramiko.SFTPClient.from_transport(self.trnsprt)
		self.ssh      = paramiko.SSHClient()
		self.stdin    = ''
		self.stdout   = ''
		self.stderr   = ''

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
				if sout.readlines()[0].strip() == "0":
					freeDir = True
				dirCounter += 1
			self.subdir   = dirName
		self.remdir   = self.workdir + "/" + self.subdir
		self.execCmd("mkdir -p " + self.remdir)
		self.disconnectSSH()

	def putFile(self, myFile):
		partFile = myFile
		if partFile.find("/") != -1:
			partFile = myFile[:myFile.rfind("/")]
		print "copying",partFile,"to the remote server"
		self.sftp.put(self.locdir + "/" + partFile,
			self.remdir + "/" + partFile)

	def getFile(self, myFile):
		partFile = myFile
		if partFile.find("/") != -1:
			partFile = myFile[:myFile.rfind("/")]
		print "copying",partFile,"from the remote server"
		self.sftp.get(self.remdir + "/" + partFile,
			self.locdir + "/" + partFile)

	def execCmd(self, cmd):
		self.stdin, self.stdout, self.stderr = self.ssh.exec_command(cmd)

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

