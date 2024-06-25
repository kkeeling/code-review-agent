import os
import sys

def main(folder_path):
    if not os.path.isdir(folder_path):
        print(f"The provided path '{folder_path}' is not a valid directory.")
        return

    # Add your code to process the folder here
    print(f"Processing folder: {folder_path}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python code_review_agent.py <folder_path>")
    else:
        main(sys.argv[1])
