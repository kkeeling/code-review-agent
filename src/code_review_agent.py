import os
import sys
import subprocess
import argparse
import requests
from colorama import Fore, Style, init
from halo import Halo
from anthropic import Anthropic
import fnmatch

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
    current_path = os.path.abspath(folder_path)
    while current_path != os.path.dirname(current_path):  # Stop at the root directory
        if os.path.isdir(os.path.join(current_path, '.git')):
            return True, current_path
        current_path = os.path.dirname(current_path)
    return False, None

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

def get_diff(folder_path, branch_name, file_path=None):
    try:
        # Prepare the git diff command
        git_diff_command = ["git", "--no-pager", "diff", branch_name]
        if file_path:
            git_diff_command.extend(["--", os.path.join(folder_path, file_path)])
        else:
            git_diff_command.extend(["--", ":!package-lock.json", ":!yarn.lock"])

        # Run the git diff command
        result = subprocess.run(
            git_diff_command,
            cwd=folder_path,
            check=True,
            text=True,
            stdout=subprocess.PIPE
        )
        return result.stdout

    except subprocess.CalledProcessError as e:
        output(f"Error during git diff: {e}", color="red")
        return None

def get_changed_files(folder_path, branch_name):
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", branch_name],
            cwd=folder_path,
            check=True,
            text=True,
            stdout=subprocess.PIPE
        )
        return result.stdout.strip().split('\n')
    except subprocess.CalledProcessError as e:
        output(f"Error getting changed files: {e}", color="red")
        return []

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

def run_code_review_agent(git_diff, file_path, branch_name, api_key, use_cxml=False):
    # Initialize the Anthropic client
    client = Anthropic(api_key=api_key)

    # Load the system prompt
    system_prompt = "You are a code review agent that reviews code for potential issues."  # fallback system prompt
    try:
        response = requests.get("https://raw.githubusercontent.com/kkeeling/code-review-agent/refs/heads/main/src/system_prompt.xml")
        response.raise_for_status()
        system_prompt = response.text
    except requests.RequestException as e:
        output(f"Error loading system prompt from remote location: {e}", color="red")

    if use_cxml:
        content = f"<documents>\n<document index=\"1\">\n<source>{file_path}</source>\n<document_content>\n{git_diff}\n</document_content>\n</document>\n</documents>"
    else:
        content = f"# INPUT\n$> git --no-pager diff {branch_name} {file_path}\n\n{git_diff}\n\nFile being reviewed: {file_path}"

    messages = [
        {"role": "user", "content": content}
    ]

    with Halo(text=f'Reviewing {file_path}...', spinner='dots'):
        response = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=4000,
            system=system_prompt,
            messages=messages
        )

    # Process the response
    assistant_response = ""
    for content_block in response.content:
        if content_block.type == "text":
            assistant_response += content_block.text

    return assistant_response

def process_files(paths, ignore_patterns=None, include_hidden=False):
    all_files = []
    for path in paths:
        if os.path.isfile(path):
            all_files.append(path)
        elif os.path.isdir(path):
            for root, dirs, files in os.walk(path):
                if not include_hidden:
                    files = [f for f in files if not f.startswith('.')]
                    dirs[:] = [d for d in dirs if not d.startswith('.')]
                for file in files:
                    file_path = os.path.join(root, file)
                    if ignore_patterns:
                        if not any(fnmatch.fnmatch(file_path, pattern) for pattern in ignore_patterns):
                            all_files.append(file_path)
                    else:
                        all_files.append(file_path)
    return all_files

def main(paths, branch_name="main", api_key=None, ignore_patterns=None, include_hidden=False, use_cxml=False):
    # check if the API key is set
    if not api_key:
        output("ERROR: Anthropic API key is not set.", color="red")
        return

    # Process all provided paths
    all_files = process_files(paths, ignore_patterns, include_hidden)

    if not all_files:
        output("ERROR: No files found to review.", color="red")
        return

    # Use the first path as the repository root
    folder_path = paths[0] if os.path.isdir(paths[0]) else os.path.dirname(paths[0])

    # Check if the provided path is a git repository
    is_git_repo, repo_root = is_git_repository(folder_path)
    if not is_git_repo:
        output(f"ERROR: No git repository found in '{folder_path}' or its parent directories.", color="red")
        return
    folder_path = repo_root
    
    # Check if the specified branch exists in the repository
    if branch_name and not branch_exists(folder_path, branch_name):
        output(f"ERROR: The branch '{branch_name}' does not exist in the repository.", color="red")
        return

    # Get the active git branch
    active_branch = get_active_git_branch(folder_path)

    # Check if the active git branch could be determined
    if not active_branch:
        output("ERROR: Could not determine the active git branch.", color="red")
        return

    # Check if the active branch and the specified branch are the same
    if active_branch == branch_name:
        output(f"ERROR: Active branch and specified branch are the same: {active_branch}", color="red")
        return

    # Merge the branches once
    try:
        output(f"Merging {branch_name} into {active_branch}...", color="cyan")
        subprocess.run(["git", "checkout", branch_name], cwd=folder_path, check=True)
        subprocess.run(["git", "pull"], cwd=folder_path, check=True)
        subprocess.run(["git", "checkout", active_branch], cwd=folder_path, check=True)
        subprocess.run(["git", "merge", branch_name], cwd=folder_path, check=True)
    except subprocess.CalledProcessError as e:
        output(f"Error during git merge: {e}", color="red")
        return

    # Get the list of changed files
    changed_files = get_changed_files(folder_path, branch_name)
    output(f"Changed files: {', '.join(changed_files)}", color="cyan")

    # Run the code review agent for each changed file
    for file_path in changed_files:
        output(f"\nReviewing file: {file_path}", color="yellow")
        diff_result = get_diff(folder_path, branch_name, os.path.basename(file_path))
        review_result = run_code_review_agent(diff_result, file_path, active_branch, api_key, use_cxml)
        output(f"Review for {file_path}:", color="green")
        output(review_result, color="blue")

def cli():
    parser = argparse.ArgumentParser(description="Process a git repository folder.")
    parser.add_argument("paths", nargs='+', help="Paths to files or directories to review")
    parser.add_argument("--api-key", default=os.environ.get("ANTHROPIC_API_KEY"), help="Anthropic API key (default: environment variable ANTHROPIC_API_KEY)")
    parser.add_argument("--branch", default="main", help="Name of the branch to compare against (default: main)")
    parser.add_argument("--ignore", action='append', help="Patterns to ignore (can be used multiple times)")
    parser.add_argument("--include-hidden", action='store_true', help="Include hidden files and directories")
    parser.add_argument("--cxml", action='store_true', help="Output in Claude XML format")

    args = parser.parse_args()

    main(args.paths, args.branch, args.api_key, args.ignore, args.include_hidden, args.cxml)

if __name__ == "__main__":
    cli()
