import pytest
from src.code_review_agent import (
    output,
    is_git_repository,
    get_changed_files,
    get_active_git_branch,
    run_code_review_agent,
    process_files,
    main
)
import os
import subprocess
from unittest.mock import patch, MagicMock, call, ANY as mock_ANY

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

@patch('src.code_review_agent.Anthropic')
@patch('src.code_review_agent.requests.get')
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
    run_code_review_agent("git diff content", "file1.py", "main", api_key)

    # Check if Anthropic client was initialized with the correct API key
    mock_anthropic.assert_called_once_with(api_key=api_key)

    # Check if the messages were created with the correct content
    mock_client.messages.create.assert_called_once()
    call_kwargs = mock_client.messages.create.call_args[1]
    assert "git diff content" in call_kwargs['messages'][0]['content']
    assert "file1.py" in call_kwargs['messages'][0]['content']

    # Check if the run_code_review_agent function was called with the correct arguments
    mock_client.messages.create.assert_called_once()
    mock_client.messages.create.assert_called_with(
        model="claude-3-5-sonnet-20240620",
        max_tokens=4000,
        messages=[{
            'role': 'user',
            'content': "# INPUT\n$> git --no-pager diff main file1.py\n\ngit diff content\n\nFile being reviewed: file1.py"
        }],
        system="Mocked system prompt"
    )

def test_process_files(tmp_path):
    # Create a temporary directory structure
    root = tmp_path / "test_repo"
    root.mkdir()
    (root / "file1.py").touch()
    (root / "file2.txt").touch()
    (root / ".hidden_file").touch()
    sub_dir = root / "subdir"
    sub_dir.mkdir()
    (sub_dir / "file3.py").touch()

    # Test without any filters
    result = process_files([str(root)])
    assert set(result) == {
        str(root / "file1.py"),
        str(root / "file2.txt"),
        str(root / "subdir" / "file3.py")
    }

    # Test with ignore patterns
    result = process_files([str(root)], ignore_patterns=["*.txt"])
    assert set(result) == {
        str(root / "file1.py"),
        str(root / "subdir" / "file3.py")
    }

    # Test with include_hidden
    result = process_files([str(root)], include_hidden=True)
    assert set(result) == {
        str(root / "file1.py"),
        str(root / "file2.txt"),
        str(root / ".hidden_file"),
        str(root / "subdir" / "file3.py")
    }

@patch('src.code_review_agent.run_code_review_agent')
@patch('src.code_review_agent.get_diff')
@patch('src.code_review_agent.get_changed_files')
@patch('src.code_review_agent.get_active_git_branch')
@patch('src.code_review_agent.branch_exists')
@patch('src.code_review_agent.is_git_repository')
@patch('src.code_review_agent.process_files')
@patch('subprocess.run')
def test_main(mock_subprocess_run, mock_process_files, mock_is_git_repo, mock_branch_exists, mock_get_active_branch, 
              mock_get_changed_files, mock_get_diff, mock_run_code_review):
    # Mock the necessary functions
    mock_process_files.return_value = ["/path/to/repo/file1.py", "/path/to/repo/file2.py"]
    mock_is_git_repo.return_value = True
    mock_branch_exists.return_value = True
    mock_get_active_branch.return_value = "feature-branch"
    mock_get_changed_files.return_value = ["file1.py", "file2.py"]
    mock_get_diff.return_value = "Mocked diff content"
    mock_subprocess_run.return_value.returncode = 0

    # Call the main function
    main(["path/to/repo"], branch_name="main", api_key="fake_api_key")

    # Assert that the functions were called with the correct arguments
    mock_process_files.assert_called_once_with(["path/to/repo"], None, False)
    mock_is_git_repo.assert_called_once()
    mock_branch_exists.assert_called_once()
    mock_get_active_branch.assert_called_once()
    mock_get_changed_files.assert_called_once()
    assert mock_get_diff.call_count == 2
    mock_get_diff.assert_has_calls([
        call("/path/to/repo/file1.py", "main", "file1.py"),
        call("/path/to/repo/file2.py", "main", "file2.py")
    ])
    assert mock_run_code_review.call_count == 2
    mock_run_code_review.assert_has_calls([
        call("Mocked diff content", "file1.py", "feature-branch", "fake_api_key", False),
        call("Mocked diff content", "file2.py", "feature-branch", "fake_api_key", False)
    ], any_order=True)
    
    # Assert that subprocess.run was called for git commands
    mock_subprocess_run.assert_any_call(["git", "checkout", "main"], cwd="/path/to/repo", check=True)
    mock_subprocess_run.assert_any_call(["git", "pull"], cwd="/path/to/repo", check=True)
    mock_subprocess_run.assert_any_call(["git", "checkout", "feature-branch"], cwd="/path/to/repo", check=True)
    mock_subprocess_run.assert_any_call(["git", "merge", "main"], cwd="/path/to/repo", check=True)

if __name__ == "__main__":
    pytest.main()
