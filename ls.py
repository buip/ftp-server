import subprocess

# define the ls command
ls = subprocess.Popen(["ls", "-l", "."],  
                      stdout=subprocess.PIPE,
                     )

# define the grep command

# read from the end of the pipe (stdout)
endOfPipe = ls.stdout

# output the files line by line
for line in endOfPipe:  
    print(type(line))
    print (line)