# GitHub Projects Setup Guide

## 📊 Create Project Board

### 1️⃣ Create New Project

1. Go to GitHub repository: https://github.com/deokhwajeong/grocery-inventory-tracker
2. Click **Projects** in the top menu
3. Click **New project**
4. Select template: **Board** (Kanban style)

### 2️⃣ Project Configuration

**Project Name**: `OCR Enhancement 2026`

**Description**:
```
Receipt OCR recognition accuracy 85% + mobile optimization project
Duration: 2026-01-16 ~ 2026-03-15 (8 weeks)
```

**Visibility**: Public (or Private)

## 📋 Board Column Structure

Customize the default template as follows:

### Column Layout

1. **📥 Backlog**
   - Planned work
   - Priority not yet assigned

2. **📝 Todo**
   - This sprint's work
   - Prioritized

3. **🚧 In Progress**
   - Currently working
   - Assignee designated
   - Limit: Max 3 items (WIP limit)

4. **👀 In Review**
   - PR created
   - Awaiting code review

5. **✅ Done**
   - Completed and merged
   - Auto-archive (after 7 days)

## 🏷️ Add Custom Fields

### Required Fields

1. **Priority**
   - Type: Single select
   - Options:
     - 🔴 P0 - Critical
     - 🟠 P1 - High
     - 🟡 P2 - Medium
     - 🟢 P3 - Low

2. **Estimate** (Time estimate)
   - Type: Number
   - Unit: hours

3. **Phase**
   - Type: Single select
   - Options:
     - Phase 1: Foundation ✅
     - Phase 2: Accuracy Improvement
     - Phase 3: UX Enhancement
     - Phase 4: Advanced Features

4. **Component**
   - Type: Single select
   - Options:
     - OCR Engine
     - Mobile UI
     - Backend
     - Database
     - Testing
     - Documentation

5. **Status** (Progress)
   - Type: Single select
   - Options:
     - Not Started
     - In Progress
     - Blocked
     - In Review
     - Complete

## 🎯 Views Configuration

### View 1: Board (Default)
- Layout: Board
- Group by: Status
- Sort by: Priority (P0 → P3)

### View 2: Priority List
- Layout: Table
- Sort by: Priority, then Estimate
- Columns: Title, Priority, Estimate, Assignee, Phase

### View 3: Phase Timeline
- Layout: Timeline
- Group by: Phase
- Sort by: Start date

### View 4: Sprint Backlog
- Layout: Board
- Filter: Phase = "Phase 2"
- Group by: Component

## 🔧 Automation Rules

### Rule 1: Auto-move to In Progress
**Trigger**: When issue is assigned
**Action**: Move to "In Progress" column

### Rule 2: Auto-move to In Review
**Trigger**: When PR is created
**Action**: Move to "In Review" column

### Rule 3: Auto-move to Done
**Trigger**: When PR is merged
**Action**: Move to "Done" column

### Rule 4: Auto-archive
**Trigger**: Item in "Done" for 7 days
**Action**: Archive item

### Rule 5: Stale Item Alert
**Trigger**: Item in "In Progress" for 3+ days
**Action**: Add label "stale"

## 📌 Add Issues to Project

### Method 1: Bulk Add (Recommended)
1. Go to project board
2. Click **Add items** (bottom right)
3. Search: `repo:deokhwajeong/grocery-inventory-tracker is:issue is:open`
4. Select all 8 issues
5. Click **Add selected items**

### Method 2: CLI (Alternative)
```bash
gh project item-add PROJECT_NUMBER --owner deokhwajeong --url https://github.com/deokhwajeong/grocery-inventory-tracker/issues/1
gh project item-add PROJECT_NUMBER --owner deokhwajeong --url https://github.com/deokhwajeong/grocery-inventory-tracker/issues/2
# ... repeat for issues 3-8
```

### Method 3: Individual Add
1. Open each issue
2. Click **Projects** on the right sidebar
3. Select "OCR Enhancement 2026"

## 🎨 Visual Customization

### Color Coding
- **P0 (Critical)**: 🔴 Red
- **P1 (High)**: 🟠 Orange
- **P2 (Medium)**: 🟡 Yellow
- **P3 (Low)**: 🟢 Green

### Labels Enhancement
Add emoji to labels:
- `enhancement` → `✨ enhancement`
- `bug` → `🐛 bug`
- `documentation` → `📚 documentation`
- `performance` → `⚡ performance`
- `testing` → `🧪 testing`

### Card Layout
Show on cards:
- ✅ Title
- ✅ Assignee
- ✅ Labels
- ✅ Priority
- ✅ Estimate

## 📊 Metrics and Insights

### Enable Insights
1. Go to project settings
2. Enable **Insights**
3. Create charts:

#### Chart 1: Burndown
- Type: Line chart
- X-axis: Date
- Y-axis: Total estimate (hours)
- Series: Sum of estimate for open items

#### Chart 2: Velocity
- Type: Bar chart
- X-axis: Week
- Y-axis: Completed points
- Series: Sum of estimate for completed items

#### Chart 3: Priority Distribution
- Type: Pie chart
- Slices: Priority
- Values: Count of items

#### Chart 4: Phase Progress
- Type: Stacked bar
- X-axis: Phase
- Y-axis: Count
- Series: Status

## 🚀 Quick Start Checklist

### Initial Setup
- [ ] Create project board
- [ ] Configure columns
- [ ] Add custom fields
- [ ] Set up automation rules
- [ ] Add all 8 issues to project

### Assign Work
- [ ] Set priority for all items
- [ ] Estimate time for each task
- [ ] Assign phase to each issue
- [ ] Assign owners (optional)

### Start Tracking
- [ ] Move P0 items to "Todo"
- [ ] Begin work on first issue
- [ ] Update progress daily
- [ ] Review metrics weekly

## 📋 Project Board URL

After creation, your board will be at:
```
https://github.com/users/deokhwajeong/projects/YOUR_PROJECT_NUMBER
```

### Link to README
Add this badge to README.md:
```markdown
[![Project](https://img.shields.io/badge/Project-OCR%20Enhancement-blue)](https://github.com/users/deokhwajeong/projects/YOUR_PROJECT_NUMBER)
```

## 🔗 Integration with Issues

### Issue Template
When creating new issues, include:
```markdown
## Description
[Brief description]

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2

## Estimate
X hours

## Priority
P1 - High

## Phase
Phase 2: Accuracy Improvement
```

### Linking PRs
When creating PRs:
```markdown
Closes #1
Part of #2

**Changes:**
- Added feature X
- Fixed bug Y

**Testing:**
- [ ] Unit tests pass
- [ ] Manual testing complete
```

## 📞 Support

### Getting Help
- **Documentation**: See this guide
- **GitHub Docs**: [GitHub Projects Documentation](https://docs.github.com/en/issues/planning-and-tracking-with-projects)
- **Issues**: Create an issue if stuck

### Best Practices
1. Update project board daily
2. Keep WIP limit (max 3 in progress)
3. Review metrics weekly
4. Archive completed items
5. Celebrate milestones! 🎉

---

**Ready to start?** [Create your project now!](https://github.com/deokhwajeong/grocery-inventory-tracker/projects)

**Last Updated**: 2026-01-16  
**Guide Version**: 1.0.0
