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

---

## Synthesis

### Opportunity Gaps
- None of the three tools surface blockers prominently at the board level
- Async update workflows (standups, status posts) treated as afterthought
- ...
```

## usage

```bash
# analyze a single screenshot
python prism.py competitor.png

# compare multiple (gets a synthesis section)
python prism.py figma.png sketch.png adobe.png

# add context about your space
python prism.py dashboard.png --context "analytics tool for marketers"

# save the report
python prism.py *.png --output competitive-analysis.md

# also save raw JSON
python prism.py *.png --output report.md --json
```

## setup

```bash
git clone https://github.com/asifmdo11y/prism
cd prism
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
python prism.py screenshot.png
```

## what you get per screenshot

- **Features visible**: each UI element identified with a description of how it's presented
- **UX patterns**: named patterns (progressive disclosure, empty states, etc.) with observations
- **Information architecture**: layout and content hierarchy
- **Copy & tone**: how they talk to users
- **Design observations**: notable visual decisions
- **What stands out**: the most interesting/differentiated thing on this screen

When you pass multiple screenshots, prism also generates a cross-product synthesis with a feature matrix, differentiators, and opportunity gaps.

## notes

This is most useful when you're preparing for a strategy review, a positioning exercise, or just doing your quarterly competitive refresh. Screenshot your competitors' onboarding, pricing pages, and core workflows and run them through here.

Works best with clear, full-page screenshots. Blurry or cropped screenshots produce less useful output.

---

authored by asif
