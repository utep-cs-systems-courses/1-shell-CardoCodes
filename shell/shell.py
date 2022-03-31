import os, sys, re

"""----Function to execute program----"""
def exeprog(path):
    for dir in re.split(":", os.environ['PATH']): #for each dir in PATH
        program = "%s/%s" % (dir, path[0]) #assign program
        try:
            os.execve(program, path, os.environ)
        except FileNotFoundError: # fail quietly
            pass 
    os.write(2, ("[Child]Error: Could not exec %s\n" % path[0]).encode()) #write to fd 2(std error) could not exec
    sys.exit(1)       

"""----Function to handle pipe----"""
def pf(path):
    #split the user input into variabes read and write
    pipeIndex = path.index("|")
    w = path[0:pipeIndex]
    r = path[pipeIndex + 1:]
    pipeRead, pipeWrite = os.pipe() #pipeRead and pipeWrite get pair of fd's from os.pipe() function
    duplicate = ""

    rc = os.fork()#fork a child process, return 0 in child, and the childs proess id in the parent

    #need second fork, fork off first child, fork off second child, 
    if rc == 0:
        duplicate = pipeWrite
        os.close(1) #close file descriptor 1
        os.dup(duplicate) #
        os.set_inheritable(1, True)
        for fd in (pipeRead, pipeWrite):
            exeprog(w)
            
    elif rc > 0:
        duplicate = pipeRead
        os.close(0) # close file descriptor 0
        os.dup(duplicate) #
        os.set_inheritable(0, True)
        for fd in (pipeRead, pipeWrite):
            exeprog(r)

    else:
        os.write(2, ("Error occured while forking").encode())
        sys.exit(1)

pid = os.getpid()
while(True): #always true, always working

    """----Start shell----"""
    if "PS1" not in os.environ: #Check for PS1 in enviroment
        path = os.getcwd() + " :$" #copy current working directory to path variable
        os.write(1, path.encode()) #write path to fd 1 (std out)
    else:   
        os.environ["PS1"] #set 
    
    """----Take input----"""
    userIn = os.read(0,1000).decode().split() # read at most 1000 bytes from fd 1 (std in)

    """----User input functionality----"""
    if userIn[0] == "cd":
        try:
            os.chdir(userIn[1]) #change the current directory to the user input path(userIn[i])
        except FileNotFoundError:
            os.write(1, f'file not found: {userIn[1]}')# write error to fd 1 (std out)
        continue

    elif "exit" in userIn:
        print("Program exiting...")
        sys.exit(0) #clean exit withount any errors or problems

    elif "|" in userIn:
        pf(userIn) #call pipe function

    else:
        os.write(1, ("About to fork (pid:%d)\n" % pid).encode())
        rc = os.fork() #obtain race condition, needed to keep the shell afterwards - child would not keep shell after executing

        if rc < 0: #if rc is less than 0 then fork failed
            os.write(2, ("Fork failed, returning %d\n" % rc).encode())
            sys.exit(1)
        
        elif rc == 0: # if rc is 0 then write to fd 1 child and parent
            os.write(1, ("[Child] PID: %d.  Parent PID: %d\n" % (os.getpid(), pid)).encode())
            if ">" in userIn:
                os.close(1) #close fd 1 (std out)
                os.open(userIn[2], os.O_CREAT | os.O_WRONLY) #open the file path
                os.set_inheritable(1, True) #set the inharitable flag of fd1 to true
                userIn = userIn[:1]
            if "<" in userIn:
                os.close(0) #close fd 0 (std in)
                os.open(userIn[2], os.O_RDONLY) #open the file path
                os.set_inheritable(0, True) #set the inharitable flag of fd0 to true
                userIn = userIn[:1]
            
            exeprog(userIn) #execute program
        else:
            os.write(1, ("[Parent] PID: %d.  Child PID: %d\n" % (pid, rc)).encode())
            # Wait for the rest to finish their processes
            childPidCode = os.wait()
            os.write(1, ("Parent: Child %d terminated with exit code %d\n"
                         % childPidCode).encode())
    