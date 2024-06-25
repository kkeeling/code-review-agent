import os
import sys
import subprocess

def is_git_repository(folder_path):
    return os.path.isdir(os.path.join(folder_path, '.git'))

def get_active_git_branch(folder_path):
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=folder_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return None
    except Exception as e:
        print(f"Error detecting git branch: {e}")
        return None

def main(folder_path):
    if not os.path.isdir(folder_path):
        print(f"The provided path '{folder_path}' is not a valid directory.")
        return

    if not is_git_repository(folder_path):
        print(f"The provided path '{folder_path}' is not a git repository.")
        return
    
    active_branch = get_active_git_branch(folder_path)
    if active_branch:
        print(f"Active git branch: {active_branch}")
    else:
        print("Could not determine the active git branch.")
    
    print(f"Processing folder: {folder_path}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python code_review_agent.py <folder_path>")
    else:
        main(sys.argv[1])
