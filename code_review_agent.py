import os
import sys
import subprocess
import argparse
from colorama import Fore, Style, init
from anthropic import AnthropicClient

# Initialize colorama
init()

def output(text, color="default"):
    colors = {
        "default": Style.RESET_ALL,
        "red": Fore.RED,
        "green": Fore.GREEN,
        "yellow": Fore.YELLOW,
        "blue": Fore.BLUE,
        "magenta": Fore.MAGENTA,
        "cyan": Fore.CYAN,
        "white": Fore.WHITE,
    }
    color_code = colors.get(color, Style.RESET_ALL)
    print(f"{color_code}{text}{Style.RESET_ALL}")

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

def checkout_and_merge_branch(folder_path, branch_name, active_branch):
    try:
        # Checkout the branch_name (ex. main)
        subprocess.run(["git", "checkout", branch_name], cwd=folder_path, check=True)

        # Perform a git pull
        subprocess.run(["git", "pull"], cwd=folder_path, check=True)

        # Checkout the active branch again (your branch)
        subprocess.run(["git", "checkout", active_branch], cwd=folder_path, check=True)

        # Merge the branch_name into the active branch
        subprocess.run(["git", "merge", branch_name], cwd=folder_path, check=True)

        # Return the result of "git --no-pager diff branch_name"
        result = subprocess.run(["git", "--no-pager", "diff", branch_name], cwd=folder_path, check=True, text=True, stdout=subprocess.PIPE)
        return result.stdout

    except subprocess.CalledProcessError as e:
        output(f"Error during git operations: {e}", color="red")
        return None

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
    # Initialize the Anthropic client
    anthropic_client = AnthropicClient(api_key="your_api_key_here")

    if not os.path.isdir(folder_path):
        output(f"ERROR: The provided path '{folder_path}' is not a valid directory.", color="red")
        exit(1)

    if not is_git_repository(folder_path):
        output(f"ERROR: The provided path '{folder_path}' is not a git repository.", color="red")
        exit(1)
    
    if not branch_exists(folder_path, branch_name):
        output(f"ERROR: The branch '{branch_name}' does not exist in the repository.", color="red")
        exit(1)

    active_branch = get_active_git_branch(folder_path)
    
    if not active_branch:
        output("ERROR: Could not determine the active git branch.", color="red")
        exit(1)

    if active_branch == branch_name:
        output(f"ERROR: Active branch and specified branch are the same: {active_branch}", color="red")
        exit(1)

    output(f"Processing folder: {folder_path}", color="yellow")
    diff_result = checkout_and_merge_branch(folder_path, branch_name, active_branch)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process a git repository folder.")
    parser.add_argument("--folder", required=True, help="Path to the folder")
    parser.add_argument("--branch", required=True, help="Name of the branch to compare against")
    
    args = parser.parse_args()
    
    main(args.folder, args.branch)
