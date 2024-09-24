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
def test_main(mock_process_files, mock_is_git_repo, mock_branch_exists, mock_get_active_branch, 
              mock_get_changed_files, mock_get_diff, mock_run_code_review):
    # Mock the necessary functions
    mock_process_files.return_value = ["/path/to/file1.py", "/path/to/file2.py"]
    mock_is_git_repo.return_value = True
    mock_branch_exists.return_value = True
    mock_get_active_branch.return_value = "feature-branch"
    mock_get_changed_files.return_value = ["file1.py", "file2.py"]
    mock_get_diff.return_value = "Mocked diff content"

    # Call the main function
    main(["path/to/repo"], branch_name="main", api_key="fake_api_key")

    # Assert that the functions were called with the correct arguments
    mock_process_files.assert_called_once_with(["path/to/repo"], None, False)
    mock_is_git_repo.assert_called_once()
    mock_branch_exists.assert_called_once()
    mock_get_active_branch.assert_called_once()
    mock_get_changed_files.assert_called_once()
    mock_get_diff.assert_called_once()
    mock_run_code_review.assert_called_once_with(
        "Mocked diff content", 
        ["file1.py", "file2.py"], 
        "feature-branch", 
        "fake_api_key",
        False  # use_cxml
    )

if __name__ == "__main__":
    pytest.main()import os
import pytest
from unittest.mock import patch, MagicMock
from src.code_review_agent import (
    is_git_repository,
    branch_exists,
    get_diff,
    get_changed_files,
    get_active_git_branch,
    run_code_review_agent,
    process_files,
)

@pytest.fixture
def mock_subprocess_run():
    with patch('subprocess.run') as mock_run:
        yield mock_run

def test_is_git_repository():
    with patch('os.path.isdir') as mock_isdir:
        mock_isdir.return_value = True
        assert is_git_repository('/path/to/repo') == True
        mock_isdir.assert_called_once_with('/path/to/repo/.git')

        mock_isdir.return_value = False
        assert is_git_repository('/path/to/not_repo') == False

def test_branch_exists(mock_subprocess_run):
    mock_subprocess_run.return_value.returncode = 0
    assert branch_exists('/path/to/repo', 'main') == True
    mock_subprocess_run.assert_called_once_with(
        ["git", "show-ref", "--verify", "--quiet", "refs/heads/main"],
        cwd='/path/to/repo',
        stdout=-1,
        stderr=-1
    )

    mock_subprocess_run.return_value.returncode = 1
    assert branch_exists('/path/to/repo', 'non_existent') == False

def test_get_diff(mock_subprocess_run):
    mock_subprocess_run.return_value.stdout = "mock diff output"
    result = get_diff('/path/to/repo', 'main', 'feature_branch', 'file.py')
    assert result == "mock diff output"
    assert mock_subprocess_run.call_count == 5  # 4 git operations + 1 diff

def test_get_changed_files(mock_subprocess_run):
    mock_subprocess_run.return_value.stdout = "file1.py\nfile2.py\n"
    result = get_changed_files('/path/to/repo', 'main')
    assert result == ['file1.py', 'file2.py']
    mock_subprocess_run.assert_called_once_with(
        ["git", "diff", "--name-only", "main"],
        cwd='/path/to/repo',
        check=True,
        text=True,
        stdout=-1
    )

def test_get_active_git_branch(mock_subprocess_run):
    mock_subprocess_run.return_value.stdout = "feature_branch\n"
    mock_subprocess_run.return_value.returncode = 0
    result = get_active_git_branch('/path/to/repo')
    assert result == "feature_branch"
    mock_subprocess_run.assert_called_once_with(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd='/path/to/repo',
        stdout=-1,
        stderr=-1,
        text=True
    )

@patch('anthropic.Anthropic')
@patch('requests.get')
def test_run_code_review_agent(mock_requests_get, mock_anthropic):
    mock_requests_get.return_value.text = "<system>Test system prompt</system>"
    mock_anthropic.return_value.messages.create.return_value.content = [
        MagicMock(type="text", text="Mock review result")
    ]

    result = run_code_review_agent('file.py', 'mock diff', 'main', 'mock_api_key')
    assert result == "Mock review result"

def test_process_files():
    with patch('os.walk') as mock_walk:
        mock_walk.return_value = [
            ('/path/to/repo', ['dir1', '.hidden_dir'], ['file1.py', '.hidden_file', 'file2.py']),
            ('/path/to/repo/dir1', [], ['file3.py', 'file4.py']),
        ]

        result = process_files(['/path/to/repo'])
        assert result == [
            '/path/to/repo/file1.py',
            '/path/to/repo/file2.py',
            '/path/to/repo/dir1/file3.py',
            '/path/to/repo/dir1/file4.py',
        ]

        result_with_hidden = process_files(['/path/to/repo'], include_hidden=True)
        assert result_with_hidden == [
            '/path/to/repo/file1.py',
            '/path/to/repo/.hidden_file',
            '/path/to/repo/file2.py',
            '/path/to/repo/dir1/file3.py',
            '/path/to/repo/dir1/file4.py',
        ]

        result_with_ignore = process_files(['/path/to/repo'], ignore_patterns=['*.py'])
        assert result_with_ignore == []
