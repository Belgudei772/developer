import os
                                                                                                                                                                                                          
def list_files(directory: str = ".") -> str:
    """List all files and directories in the given path."""
    try:
        entries = os.listdir(directory)
        return "\n".join(entries)
    except Exception as e:
        return f"Error: {e}"
      
def read_file(file_path: str) -> str:
    """Read the content of a file."""
    try:
        with open(file_path, 'r') as f:
            return f.read()
    except Exception as e:
        err = f"Error reading file {file_path}: {e}"
        return err
    
def write_file(file_path: str, content: str) -> str:
    """Write content to a file."""
    try:
        with open(file_path, 'w') as f:
            f.write(content)
        return f"Wrote to {file_path}"
    except Exception as e:
        err = f"Error writing to file {file_path}: {e}"
        return err

def run_command(command: str) -> str:
    """Run a shell command and return its output."""
    import subprocess
    try:
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=100)
        return result.stdout.decode()
    except subprocess.CalledProcessError as e:
        err = f"Command '{command}' failed with error: {e.stderr.decode()}"
        return err
    

