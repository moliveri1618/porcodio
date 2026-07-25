# Working with Claude Code

This project uses Claude Code as a development assistant.

Following the workflow below produces more accurate code, fewer unnecessary changes, and keeps implementations consistent with the project architecture.

---

# One Conversation = One Ticket

Create a new Claude conversation for every ticket or feature.

Examples:

- BE-421 Product Search API
- FE-421 Product Table Filters
- BE-422 PDF Parsing Improvements

Avoid using one conversation for multiple unrelated tasks.

---

# Before Starting

Start every conversation with:

```text
Use the CLAUDE.md file as your project instructions and follow its guidelines throughout this conversation.

Speak in English.
```

---

# Step 1 - Explain the Goal

Describe the business problem before discussing implementation.

Example:

```text
Implement BE-421 Product Search API.

Goal:
Allow users to search products by name.

Requirements:
- partial search
- case insensitive
- preserve pagination
- preserve existing API response
- do not break existing filters
```

Avoid only saying:

```text
Add search.
```

More context produces better solutions.

---

# Step 2 - Ask Claude to Analyze First

Before editing code, ask Claude to inspect the codebase.

Example:

```text
Read the relevant files first.

Explain your proposed implementation before making any code changes.

Wait for my approval.
```

Claude should:

- identify the files to modify
- explain the implementation
- mention assumptions
- identify possible side effects

---

# Step 3 - Review the Plan

Review Claude's proposal.

Check:

- Are the correct files being modified?
- Is the architecture consistent?
- Is the API backwards compatible?
- Are there unnecessary changes?

If the approach looks correct, continue.

Example:

```text
Proceed with the implementation.
```

---

# Step 4 - Review the Code

Never blindly accept generated code.

Check:

- only relevant files changed
- no unnecessary refactoring
- no duplicated logic
- existing patterns are respected
- naming remains consistent

---

# Step 5 - Ask for a Self Review

Before accepting changes, ask Claude to review its own implementation.

Example:

```text
Review your implementation.

Look for:
- bugs
- regressions
- edge cases
- duplicated logic
- unnecessary complexity

Do not modify the code yet.
```

Claude often catches mistakes during this step.

---

# Step 6 - Approve Changes

Only accept edits after reviewing:

- implementation
- architecture
- self review

---

# Good Prompt Template

```text
Use the CLAUDE.md file as your project instructions and follow its guidelines throughout this conversation.

Speak in English.

Implement BE-421.

Requirements:
- ...
- ...
- ...

Before making changes:

1. Read the relevant files.
2. Explain your proposed implementation.
3. Mention any assumptions.
4. Wait for my approval before editing.
```

---

# Workflow Summary

```
Describe the problem
        │
        ▼
Claude analyzes the codebase
        │
        ▼
Claude explains the implementation
        │
        ▼
You review the plan
        │
        ▼
Claude implements the solution
        │
        ▼
Claude performs a self review
        │
        ▼
You approve the changes
```

---

# Best Practices

- One conversation per ticket.
- Keep prompts focused.
- Give business context, not only technical details.
- Prefer small, incremental changes.
- Avoid asking Claude to refactor unrelated code.
- Preserve backwards compatibility unless the ticket explicitly requires otherwise.
- Let Claude inspect the existing implementation before writing code.
- Always review generated code before accepting edits.

Following this workflow consistently leads to higher-quality implementations and fewer regressions.