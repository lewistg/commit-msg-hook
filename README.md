# README

This git hook extracts the issue number from your branch name and automatically
adds it your commit messages.

To install this hook copy the contents of [commit_msg.py](./commit_msg.py) to
`.git/hooks/commit-msg` in your repo. Make sure to make `commit-msg`
executable.

[Here][1] is a direct link to the contents of `commit_msg.py`.

The hook uses the following format for the commit subject's line:

```
<issue-number> <original-subject>
```

You can modify this format, however, by changing the `SUBJECT_LINE_FORMAT`
variable in the hook's script.

[1]: https://bitbucket.org/marqhq/tys-dev-scripts/raw/main/git/commit-msg-hook/commit_msg.py
