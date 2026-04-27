# prism

Competitive intelligence from product screenshots. Drop in one or more screenshots of a competitor's product — prism uses Claude's vision to extract structured intelligence: features, UX patterns, information architecture, and opportunity gaps.

```
$ python prism.py linear.png jira.png notion.png \
    --context "B2B project management tool for engineering teams" \
    --output analysis.md

[prism] analyzing 3 screenshot(s)...
[prism] context: B2B project management tool for engineering teams

  analyzing linear.png...
  analyzing jira.png...
  analyzing notion.png...

  synthesizing across all screenshots...
```

The output is a structured markdown report:

```markdown
## linear.png

**Screen**: Project board / sprint view
**Product**: Linear

### Features Visible
- **Issue grouping by status** — kanban-style columns with swimlane grouping
- **Keyboard shortcut hints** — visible shortcut overlays on hover
- **Cycle progress indicator** — progress bar showing sprint completion %

### UX Patterns
- **Progressive disclosure**: details hidden until hover, reducing visual noise
- **Command palette**: prominent keyboard-first navigation model

### What Stands Out
Linear bets heavily on keyboard-first UX — almost every action has a shortcut
visible in the UI, which signals their ICP is power users who resent the mouse.

