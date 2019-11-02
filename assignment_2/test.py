import subprocess

test = subprocess.Popen(["nohup", "sh",  "testing.sh", "small.txt"])
test.wait()
