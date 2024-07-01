# Code Review Agent

A code review agent that reviews git diffs and provides feedback on changes to the codebase using the Anthropic API.

## Installation

To install the Code Review Agent using pipx, follow these steps:

1. Ensure you have pipx installed. If not, install it using:

   ```
   python3 -m pip install --user pipx
   python3 -m pipx ensurepath
   ```

2. Install the Code Review Agent:

   ```
   pipx install git+https://github.com/kkeeling/code-review-agent.git
   ```

## Usage

To use the Code Review Agent, you need to have an Anthropic API key. You can set it as an environment variable or pass it as an argument.

### Basic Usage

```
code-review-agent [--folder FOLDER] [--branch BRANCH] [--api-key API_KEY]
```

- `--folder`: Path to the git repository folder (default: current working directory)
- `--branch`: Name of the branch to compare against (default: main)
- `--api-key`: Anthropic API key (default: environment variable ANTHROPIC_API_KEY)

### Examples

1. Review changes in the current directory against the main branch:

   ```
   code-review-agent
   ```

2. Review changes in a specific folder against a different branch:

   ```
   code-review-agent --folder /path/to/repo --branch develop
   ```

3. Provide the API key as an argument:

   ```
   code-review-agent --api-key your_api_key_here
   ```

### Setting up the API Key

It's recommended to set the Anthropic API key as an environment variable:

```
export ANTHROPIC_API_KEY=your_api_key_here
```

You can add this line to your shell configuration file (e.g., `.bashrc` or `.zshrc`) to make it permanent.

## How It Works

The Code Review Agent performs the following steps:

1. Checks if the specified folder is a git repository.
2. Retrieves the git diff between the current branch and the specified branch.
3. Sends the diff to the Anthropic API for analysis.
4. Displays the code review feedback, including:
   - A summary of changes
   - Identified issues (if any)
   - A code quality score
   - Reasoning for the score

## Requirements

- Python 3.6+
- Git
- Anthropic API key

## Project Structure

The main components of the Code Review Agent are:

1. `code_review_agent.py`: The main script that handles the git operations and interacts with the Anthropic API.
2. `system_prompt.md`: Contains the system prompt used to guide the AI in performing the code review.
3. `pyproject.toml`: Defines the project metadata and dependencies.

## Contributing

Contributions to the Code Review Agent are welcome! Please follow these steps to contribute:

1. Fork the repository
2. Create a new branch for your feature or bug fix
3. Make your changes and commit them with a clear commit message
4. Push your changes to your fork
5. Create a pull request with a description of your changes

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Acknowledgments

- This project uses the Anthropic API for AI-powered code reviews.
- Thanks to all contributors and users of the Code Review Agent.

## Support

If you encounter any issues or have questions, please open an issue on the GitHub repository.