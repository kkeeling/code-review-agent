import pytest
from code_review_agent import (
    output,
    is_git_repository,
    get_changed_files,
    get_active_git_branch,
    run_code_review_agent
)
import os
import subprocess
from unittest.mock import patch, MagicMock

def test_output(capsys):
    output("Test message", color="red")
    captured = capsys.readouterr()
    assert "Test message" in captured.out
    assert "\033[31m" in captured.out  # ANSI color code for red

def test_is_git_repository(tmp_path):
    # Create a temporary directory
    non_git_dir = tmp_path / "non_git"
    non_git_dir.mkdir()
    assert not is_git_repository(str(non_git_dir))

    # Create a .git directory to simulate a git repository
    git_dir = tmp_path / "git_repo"
    git_dir.mkdir()
    (git_dir / ".git").mkdir()
    assert is_git_repository(str(git_dir))

@pytest.fixture
def mock_subprocess_run():
    with patch('subprocess.run') as mock_run:
        yield mock_run

def test_get_changed_files(mock_subprocess_run):
    mock_subprocess_run.return_value.stdout = "file1.py\nfile2.py\n"
    result = get_changed_files("/fake/path", "main")
    assert result == ["file1.py", "file2.py"]
    mock_subprocess_run.assert_called_once_with(
        ["git", "diff", "--name-only", "main"],
        cwd="/fake/path",
        check=True,
        text=True,
        stdout=subprocess.PIPE
    )

def test_get_active_git_branch(mock_subprocess_run):
    mock_subprocess_run.return_value.returncode = 0
    mock_subprocess_run.return_value.stdout = "feature-branch\n"
    result = get_active_git_branch("/fake/path")
    assert result == "feature-branch"
    mock_subprocess_run.assert_called_once_with(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd="/fake/path",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

@pytest.mark.parametrize("returncode, expected", [
    (0, "feature-branch"),
    (1, None),
])
def test_get_active_git_branch_error(mock_subprocess_run, returncode, expected):
    mock_subprocess_run.return_value.returncode = returncode
    mock_subprocess_run.return_value.stdout = "feature-branch\n"
    result = get_active_git_branch("/fake/path")
    assert result == expected

@patch('code_review_agent.Anthropic')
@patch('code_review_agent.requests.get')
def test_run_code_review_agent(mock_requests_get, mock_anthropic, capsys):
    # Mock the API key
    api_key = "fake_api_key"

    # Mock the requests.get response
    mock_response = MagicMock()
    mock_response.text = "Mocked system prompt"
    mock_requests_get.return_value = mock_response

    # Mock the Anthropic client and its response
    mock_client = MagicMock()
    mock_anthropic.return_value = mock_client
    mock_message = MagicMock()
    mock_message.content = [MagicMock(type="text", text="Mocked assistant response")]
    mock_client.messages.create.return_value = mock_message

    # Call the function
    run_code_review_agent("git diff content", ["file1.py", "file2.py"], "main", api_key)

    # Check if Anthropic client was initialized with the correct API key
    mock_anthropic.assert_called_once_with(api_key=api_key)

    # Check if the messages were created with the correct content
    mock_client.messages.create.assert_called_once()
    call_kwargs = mock_client.messages.create.call_args[1]
    assert "git diff content" in call_kwargs['messages'][0]['content']
    assert "file1.py, file2.py" in call_kwargs['messages'][0]['content']

    # Check if the response was processed and output
    captured = capsys.readouterr()
    assert "Mocked assistant response" in captured.out

if __name__ == "__main__":
    pytest.main()