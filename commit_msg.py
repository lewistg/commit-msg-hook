#!/usr/bin/env python

import argparse
import subprocess
import re
import sys
import os

parser = argparse.ArgumentParser(description="`commit-msg` git hook")
parser.add_argument(
    "file", type=str, help="Temporary file containing the commit message"
)

EMPTY_LINE_PATTERN = re.compile(r"(^\s*$|^\s*#.*$)")
ISSUE_NUMBER_PATTERN = re.compile(
    r"[^A-Za-z0-9]*(?P<issue_number>[A-Z]+-[0-9]+)[^A-Za-z0-9]*"
)
FIXUP_PATTERN = re.compile("^fixup!")
SUBJECT_LINE_FORMAT = "{issue_number} {subject}"


def find_issue_number(branch_name):
    matches = re.findall(ISSUE_NUMBER_PATTERN, branch_name)
    if not matches:
        raise Exception("Could not find issue number in branch name")
    return matches[0]


def get_branch_name():
    result = subprocess.run(
        ["git", "branch", "--show-current"], capture_output=True, text=True, check=True
    )
    branch_name = result.stdout.strip() or get_rebasing_branch_name()
    if not branch_name:
        raise Exception("Error getting branch name")
    return branch_name

def get_rebasing_branch_name():
    """
    During the middle of a rebase, git branch --show-current does not work. Instead we resort to the method
    described on StackOverflow [1].

    [1]: https://stackoverflow.com/a/59115583/1460808
    """
    for directory in ["rebase-merge", "rebase-apply"]:
        result = subprocess.run(["git", "rev-parse", "--git-path", directory], capture_output=True, text=True, check=True)
        path = result.stdout.strip()
        if os.path.isdir(path):
            with open(os.path.join(path, "head-name"), "r") as branch_file:
                return branch_file.readline().strip().rsplit("/", 1)[-1]
    return ""


def insert_issue_number(commit_message, issue_number):
    subject_line_index = find_subject_line(commit_message)
    if subject_line_index == -1:
        print("Warning: Could not find commit subject line", file=sys.stderr)
        return commit_message
    if re.findall(ISSUE_NUMBER_PATTERN, commit_message[subject_line_index]):
        # Subject already has an issue number. The issue number may not match
        # the current branch's issue number, but we just assume the author
        # knows what they're doing and don't append the branch's issue number.
        return
    commit_message[subject_line_index] = SUBJECT_LINE_FORMAT.format(
        issue_number=issue_number, subject=commit_message[subject_line_index]
    )


def is_fixup(commit_message):
    subject_line_index = find_subject_line(commit_message)
    return subject_line_index != -1 and re.match(
        FIXUP_PATTERN, commit_message[subject_line_index]
    )


def find_subject_line(commit_message):
    return next(
        (
            i
            for i in range(0, len(commit_message))
            if not re.match(EMPTY_LINE_PATTERN, commit_message[i])
        ),
        -1,
    )


def main():
    args = parser.parse_args()

    commit_message = []
    with open(args.file, "r") as commit_message_file:
        commit_message = commit_message_file.read().split("\n")
        if not is_fixup(commit_message):
            issue_number = find_issue_number(get_branch_name())
            insert_issue_number(commit_message, issue_number)

    with open(args.file, "w") as commit_message_file:
        commit_message_file.write("\n".join(commit_message))


if __name__ == "__main__":
    main()
