# Commit Scope Policy

Use this policy when a repository has many local modifications and the user wants a clean synchronization workflow.

## Include By Default

- the files directly related to the active task
- matching docs and configs that are part of the same logical change
- new files required to make that logical change usable

## Exclude By Default

- whitespace-only or line-ending-only changes
- generated outputs unless the repository intentionally versions them
- restored copies, recheck directories, or mail-check artifacts unless the user explicitly wants them committed
- unrelated experiments mixed into the same worktree

## Split Into Another Commit When

- docs and source belong to different tasks
- one group is active product code and another is archived output
- one group is clean and high-confidence while another is noisy or ambiguous

## Verification Hints

- use line-ending-insensitive diff checks for suspected noise
- inspect `diff --stat` before staging a large set
- verify `diff --cached --name-only` before creating the commit

## Output Contract

When summarizing a commit decision, report:

- what was included
- what was excluded
- why each excluded category stayed out
