import os
import sys
import subprocess
import argparse
import requests
from colorama import Fore, Style, init
from halo import Halo
from anthropic import Anthropic

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

def get_diff(folder_path, branch_name, active_branch):
    try:
        # Checkout the branch_name (ex. main)
        subprocess.run(["git", "checkout", branch_name], cwd=folder_path, check=True)

        # Perform a git pull
        subprocess.run(["git", "pull"], cwd=folder_path, check=True)

        # Checkout the active branch again (your branch)
        subprocess.run(["git", "checkout", active_branch], cwd=folder_path, check=True)

        # Merge the branch_name into the active branch
        subprocess.run(["git", "merge", branch_name], cwd=folder_path, check=True)

        # Return the result of "git --no-pager diff branch_name" excluding package-lock.json and yarn.lock
        result = subprocess.run(
            ["git", "--no-pager", "diff", branch_name, "--", ":!package-lock.json", ":!yarn.lock"],
            cwd=folder_path,
            check=True,
            text=True,
            stdout=subprocess.PIPE
        )
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

def run_code_review_agent(git_diff, branch_name, api_key):
    # Initialize the Anthropic client
    output("Initializing the Anthropic client...", color="green")
    client = Anthropic(api_key=api_key)

    # Load the system prompt
    output("Loading the system prompt...", color="green")
    system_prompt = "You are a code review agent that reviews code for potential issues."  # fallback system prompt
    try:
        response = requests.get("https://raw.githubusercontent.com/kkeeling/code-review-agent/main/system_prompt.md")
        response.raise_for_status()
        system_prompt = response.text
    except requests.RequestException as e:
        output(f"Error loading system prompt from remote location: {e}", color="red")

    output("Preparing the messages for Claude...", color="green")
    messages = [
        {"role": "user", "content": f"# INPUT\n$> git --no-pager diff {branch_name}\n\n{git_diff}"}
    ]

    output("Sending the diff result to Claude...", color="green")
    with Halo(text='Waiting for Claude to respond...', spinner='dots'):
        response = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=4000,
            system=system_prompt,
            messages=messages
        )

    # Process the response
    output("Processing the response from Claude...", color="green")
    assistant_response = ""
    for content_block in response.content:
        if content_block.type == "text":
            assistant_response += content_block.text
            output(f"\n{content_block.text}", color="blue")
    
    return assistant_response

def main(folder_path=None, branch_name="main", api_key=None):
    # check if the API key is set
    if not api_key:
        output("ERROR: Anthropic API key is not set.", color="red")
        exit(1)

    # Set default folder path if not provided
    if not folder_path:
        folder_path = os.getcwd()
        output(f"No folder path provided. Using current working directory: {folder_path}", color="yellow")
    else:
        # Check if the provided path is a valid directory
        if not os.path.isdir(folder_path):
            output(f"ERROR: The provided path '{folder_path}' is not a valid directory.", color="red")
            exit(1)

    # Check if the provided path is a git repository
    if not is_git_repository(folder_path):
        output(f"ERROR: The provided path '{folder_path}' is not a git repository.", color="red")
        exit(1)
    
    # Check if the specified branch exists in the repository
    if branch_name and not branch_exists(folder_path, branch_name):
        output(f"ERROR: The branch '{branch_name}' does not exist in the repository.", color="red")
        exit(1)

    # Get the active git branch
    active_branch = get_active_git_branch(folder_path)

    # Check if the active git branch could be determined
    if not active_branch:
        output("ERROR: Could not determine the active git branch.", color="red")
        exit(1)

    # Check if the active branch and the specified branch are the same
    if active_branch == branch_name:
        output(f"ERROR: Active branch and specified branch are the same: {active_branch}", color="red")
        exit(1)

    # Get the diff between the active branch and the specified branch
    output(f"Processing folder: {folder_path}", color="yellow")
    diff_result = get_diff(folder_path, branch_name, active_branch)
    
    # Run the code review agent
    run_code_review_agent(diff_result, active_branch, api_key)

def cli():
    parser = argparse.ArgumentParser(description="Process a git repository folder.")
    parser.add_argument("--folder", help="Path to the folder (default: current working directory)")
    parser.add_argument("--api-key", default=os.environ.get("ANTHROPIC_API_KEY"), help="Anthropic API key (default: environment variable ANTHROPIC_API_KEY)")
    parser.add_argument("--branch", default="main", help="Name of the branch to compare against (default: main)")

    args = parser.parse_args()

    main(args.folder, args.branch, args.api_key)

if __name__ == "__main__":
    cli()
