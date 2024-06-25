import os
import sys
import subprocess
import argparse

def output(text, color="default"):
    colors = {
        "default": "\033[0m",
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "magenta": "\033[95m",
        "cyan": "\033[96m",
        "white": "\033[97m",
    }
    color_code = colors.get(color, colors["default"])
    print(f"{color_code}{text}\033[0m")

def is_git_repository(folder_path):
    return os.path.isdir(os.path.join(folder_path, '.git'))

def branch_exists(folder_path, branch_name):
    try:
        result = subprocess.run(
            ["git", "show-ref", "--verify", "--quiet", f"refs/heads/{branch_name}"],
            cwd=folder_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return result.returncode == 0
    except Exception as e:
        print(f"Error checking if branch exists: {e}")
        return False

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

def main(folder_path, branch_name):
    if not os.path.isdir(folder_path):
        print(f"The provided path '{folder_path}' is not a valid directory.")
        return

    if not is_git_repository(folder_path):
        print(f"The provided path '{folder_path}' is not a git repository.")
        return
    
    if not branch_exists(folder_path, branch_name):
        print(f"The branch '{branch_name}' does not exist in the repository.")
        return

    active_branch = get_active_git_branch(folder_path)
    
    if active_branch:
        print(f"Active git branch: {active_branch}")
    else:
        print("Could not determine the active git branch.")
    
    if active_branch == branch_name:
        print(f"The active branch '{active_branch}' matches the specified branch '{branch_name}'.")
    else:
        print(f"The active branch '{active_branch}' does not match the specified branch '{branch_name}'.")

    print(f"Processing folder: {folder_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process a git repository folder.")
    parser.add_argument("--folder", required=True, help="Path to the folder")
    parser.add_argument("--branch", required=True, help="Name of the branch to compare against")
    
    args = parser.parse_args()
    
    main(args.folder, args.branch)
