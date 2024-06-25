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

def checkout_and_merge_branch(folder_path, branch_name):
    try:
        # Checkout the branch_name
        subprocess.run(["git", "checkout", branch_name], cwd=folder_path, check=True)
        output(f"Checked out branch '{branch_name}'", color="green")

        # Perform a git pull
        subprocess.run(["git", "pull"], cwd=folder_path, check=True)
        output(f"Pulled latest changes for branch '{branch_name}'", color="green")

        # Get the active branch before checkout
        active_branch = get_active_git_branch(folder_path)

        # Checkout the active branch again
        subprocess.run(["git", "checkout", active_branch], cwd=folder_path, check=True)
        output(f"Checked out back to active branch '{active_branch}'", color="green")

        # Merge the branch_name into the active branch
        subprocess.run(["git", "merge", branch_name], cwd=folder_path, check=True)
        output(f"Merged branch '{branch_name}' into '{active_branch}'", color="green")

        # Return the result of "git --no-pager diff branch_name"
        result = subprocess.run(["git", "--no-pager", "diff", branch_name], cwd=folder_path, check=True, text=True, stdout=subprocess.PIPE)
        return result.stdout

    except subprocess.CalledProcessError as e:
        output(f"Error during git operations: {e}", color="red")

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
        output(f"The provided path '{folder_path}' is not a valid directory.", color="red")
        return

    if not is_git_repository(folder_path):
        output(f"The provided path '{folder_path}' is not a git repository.", color="red")
        return
    
    if not branch_exists(folder_path, branch_name):
        output(f"The branch '{branch_name}' does not exist in the repository.", color="red")
        return

    active_branch = get_active_git_branch(folder_path)
    
    if active_branch:
        output(f"Active git branch: {active_branch}", color="green")
    else:
        output("Could not determine the active git branch.", color="red")
    
    if active_branch == branch_name:
        output(f"The active branch '{active_branch}' matches the specified branch '{branch_name}'.", color="green")
    else:
        output(f"Processing folder: {folder_path}", color="yellow")
        diff_result = checkout_and_merge_branch(folder_path, branch_name)
        output(f"Diff with branch '{branch_name}':\n{diff_result}", color="blue")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process a git repository folder.")
    parser.add_argument("--folder", required=True, help="Path to the folder")
    parser.add_argument("--branch", required=True, help="Name of the branch to compare against")
    
    args = parser.parse_args()
    
    main(args.folder, args.branch)
