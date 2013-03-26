'''Submit CHARMM jobs remotely'''

import ssh

class RunCharmmRemotely(ssh.RunCommandRemotely):
	'''Run CHARMM job remotely'''
	def __init__(self, server, charmmInp="", subdir=""):
		ssh.RunCommandRemotely.__init__(self, server=server, subdir=subdir)
		self.charmmInp = ""
		self.charmmOut = ""

	def generateCharmmJob(self):
		return \
'''#!/bin/bash
#$ -m a
#$ -M %s

input=%s
output=%s
tempdir=%s/$JOB_ID
mkdir -p $tempdir
oridir=${SGE_O_WORKDIR}

cp -r $oridir/* $tempdir/
mpirun=%s
charmm=%s
if [  "$NSLOTS" -gt 1 ]; then
  $mpirun -v -np $NSLOTS $charmm < $tempdir/$input > $tempdir/$output
else
    $charmm < $tempdir/$input > $tempdir/$output
fi

mv $tempdir/* $oridir/
rmdir $tempdir
''' % (self.config.get('misc','email'), self.charmmInp, self.charmmOut,
	self.config.get(server, 'scratchdir'), self.config.get(server,'mpirun'),
	self.config.get(server, 'charmm'))


if __name__ == "__main__":
	# Testing with verdi
	server = 'verdi'
	rmtChm = RunCharmmRemotely(server, subdir='dir000000')
	print rmtChm.generateCharmmJob()