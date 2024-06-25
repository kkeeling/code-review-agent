import os
import sys

def is_git_repository(folder_path):
    return os.path.isdir(os.path.join(folder_path, '.git'))

def main(folder_path):
    if not os.path.isdir(folder_path):
        print(f"The provided path '{folder_path}' is not a valid directory.")
        return

    if not is_git_repository(folder_path):
        print(f"The provided path '{folder_path}' is not a git repository.")
        return
    print(f"Processing folder: {folder_path}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python code_review_agent.py <folder_path>")
    else:
        main(sys.argv[1])
