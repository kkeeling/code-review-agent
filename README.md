# Code Review Agent

A code review agent that reviews git diffs and provides feedback on changes to the codebase using the Anthropic API.

## Installation

### Using pipx (recommended for end-users)

To install the Code Review Agent using pipx, follow these steps:

1. Ensure you have pipx installed. If not, install it using:

   ```bash
   python3 -m pip install --user pipx
   python3 -m pipx ensurepath
   ```

2. Install the Code Review Agent:

   ```bash
   pipx install git+https://github.com/kkeeling/code-review-agent.git
   ```

### For Development

If you want to contribute to the project or run the tests, follow these steps:

1. Clone the repository:

   ```bash
   git clone https://github.com/kkeeling/code-review-agent.git
   cd code-review-agent
   ```

2. Create a virtual environment:

   You can use either venv or conda to create a virtual environment. Choose the method you prefer:

   #### Using venv

   ```bash
   python3 -m venv venv
   ```

   #### Using conda

   ```bash
   conda create --name code-review-agent python=3.9
   ```

3. Activate the virtual environment:

   #### For venv

   - On macOS and Linux:

     ```bash
     source venv/bin/activate
     ```

   - On Windows:

     ```bash
     venv\Scripts\activate
     ```

   #### For conda

   ```bash
   conda activate code-review-agent
   ```

4. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Running Tests

To run the tests for the Code Review Agent, follow these steps:

1. Ensure you have completed the "For Development" installation steps above.

2. Make sure your virtual environment is activated.

3. Run the tests using pytest:

   ```bash
   pytest
   ```

This will run all the tests in the `test_code_review_agent.py` file and display the results.

## Usage

To use the Code Review Agent, you need to have an Anthropic API key. You can set it as an environment variable or pass it as an argument.

### Basic Usage

```bash
code-review-agent [--folder FOLDER] [--branch BRANCH] [--api-key API_KEY]
```

- `--folder`: Path to the git repository folder (default: current working directory)
- `--branch`: Name of the branch to compare against (default: main)
- `--api-key`: Anthropic API key (default: environment variable ANTHROPIC_API_KEY)

### Examples

1. Review changes in the current directory against the main branch:

   ```bash
   code-review-agent
   ```

2. Review changes in a specific folder against a different branch:

   ```bash
   code-review-agent --folder /path/to/repo --branch develop
   ```

3. Provide the API key as an argument:

   ```bash
   code-review-agent --api-key your_api_key_here
   ```

### Setting up the API Key

It's recommended to set the Anthropic API key as an environment variable:

```bash
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
4. `test_code_review_agent.py`: Contains unit tests for the Code Review Agent.
5. `requirements.txt`: Lists all the Python dependencies required for the project.

## Contributing

Contributions to the Code Review Agent are welcome! Please follow these steps to contribute:

1. Fork the repository
2. Create a new branch for your feature or bug fix
3. Make your changes and commit them with a clear commit message
4. Push your changes to your fork
5. Create a pull request with a description of your changes

When contributing, please ensure that you add or update tests as necessary to maintain code coverage.

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Acknowledgments

- This project uses the Anthropic API for AI-powered code reviews.
- Thanks to all contributors and users of the Code Review Agent.

## Support

If you encounter any issues or have questions, please open an issue on the GitHub repository.