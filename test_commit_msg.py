import unittest
import tempfile
import subprocess
import os
import commit_msg


class in_temp_repo:
    def __init__(self):
        self._temp_dir = tempfile.TemporaryDirectory()
        self._orginal_dir = os.getcwd()
        self.name = self._temp_dir.name
        os.chdir(self._temp_dir.name)
        subprocess.run(["git", "init", "-q"], check=True)

    def create_branch(self, branch_name):
        subprocess.run(["git", "checkout", "-q", "-b", branch_name], check=True)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        os.chdir(self._orginal_dir)
        self._temp_dir.__exit__(exc_type, exc, traceback)


class TestCommitMsg(unittest.TestCase):
    def test_get_branch_name(self):
        """
        Gets the branch name
        """
        branch_name = "foo-bar-baz-PRESS-123"
        with in_temp_repo() as temp_repo:
            temp_repo.create_branch(branch_name)
            self.assertEqual(commit_msg.get_branch_name(), branch_name)

    def test_find_issue_number(self):
        """
        Finds the issue number in a branch name
        """
        branch_names = [
            "foo-bar-baz-PRESS-123",
            "foo-bar-PRESS-123-baz",
            "PRESS-123-foo-bar-baz",
        ]
        issue_numbers = [
            commit_msg.find_issue_number(branch_name) for branch_name in branch_names
        ]
        self.assertEqual(issue_numbers, ["PRESS-123" for branch_name in branch_names])

    def test_insert_issue_number(self):
        """
        Adds the issue number to commit's subject line
        """
        commit_message = """Add integration test

We recently experienced an outage due a bug in this untested code.""".split(
            "\n"
        )

        commit_msg.insert_issue_number(commit_message, "PRESS-123")
        expected_commit_message = """PRESS-123 Add integration test

We recently experienced an outage due a bug in this untested code."""
        self.assertEqual("\n".join(commit_message), expected_commit_message)

    def test_skip_issue_number_insert(self):
        """
        Does not attempt to insert the issue number if one is already there
        """
        commit_message = """Add integration test (PRESS-123)

We recently experienced an outage due a bug in this untested code."""
        commit_message_with_issue = commit_message.split("\n")
        commit_msg.insert_issue_number(commit_message_with_issue, "PRESS-123")
        self.assertEqual("\n".join(commit_message_with_issue), commit_message)

    def test_integration(self):
        with in_temp_repo() as temp_repo:
            self._install_git_hook(temp_repo.name)

            temp_repo.create_branch("foo-bar-baz-PRESS-123")

            subprocess.run(["touch", "main.py"], check=True)
            subprocess.run(["git", "add", "main.py"], check=True)
            subprocess.run(
                ["git", "commit", "-q", "-m", "Oops, forgot the issue number"],
                check=True,
            )

            result = subprocess.run(
                ["git", "log", "--pretty=format:%s"],
                check=True,
                capture_output=True,
                text=True,
            )
            subject_line = result.stdout
            self.assertEqual(subject_line, "PRESS-123 Oops, forgot the issue number")

    def test_fixup_commits(self):
        """
        It shouldn't add issue numbers to fixup commits
        """
        with in_temp_repo() as temp_repo:
            self._install_git_hook(temp_repo.name)

            temp_repo.create_branch("foo-bar-baz-PRESS-123")

            subprocess.run(["touch", "main.py"], check=True)
            subprocess.run(["git", "add", "main.py"], check=True)
            subprocess.run(
                [
                    "git",
                    "commit",
                    "-q",
                    "--no-verify",
                    "-m",
                    "Oops, forgot the issue number",
                ],
                check=True,
            )
            subprocess.run(["touch", "foo.py"], check=True)
            subprocess.run(["git", "add", "foo.py"], check=True)
            subprocess.run(["git", "commit", "-q", "--fixup", "HEAD"], check=True)
            result = subprocess.run(
                ["git", "log", "--pretty=format:%s", "-n", "1"],
                check=True,
                capture_output=True,
                text=True,
            )
            subject_line = result.stdout
            self.assertEqual(subject_line, "fixup! Oops, forgot the issue number")

    def _install_git_hook(self, repo_dir):
        hook_path = os.path.join(repo_dir, ".git", "hooks", "commit-msg")
        subprocess.run(
            ["cp", commit_msg.__file__, hook_path],
            check=True,
            capture_output=True,
            text=True,
        )


if __name__ == "__main__":
    unittest.main()
