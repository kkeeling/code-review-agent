import os
import pytest
import subprocess
from unittest.mock import patch, MagicMock
from src.code_review_agent import (
    output,
    is_git_repository,
    branch_exists,
    get_diff,
    get_changed_files,
    get_active_git_branch,
    run_code_review_agent,
    process_files,
    main
)

# ... (keep all the existing test functions)

if __name__ == "__main__":
    pytest.main()
