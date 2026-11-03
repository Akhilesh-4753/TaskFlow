# TaskFlow — Agent Development Guidelines

These instructions are permanent project rules for all AI agents working on TaskFlow. Follow them automatically on every task without requiring the user to repeat them.

---

## Core Development Priorities
1. **Fast Implementation:** Prioritize direct, swift implementation over unnecessary investigation and lengthy planning.
2. **Minimal File Modifications:** Modify or create only the files strictly required for the requested change.
3. **Targeted Testing Only:** Run only tests directly relevant to the modified code. Never run full project-wide test suites for minor changes.
4. **Preserve Existing Functionality:** Protect existing MVT architecture, coding patterns, responsive UI design, and features.
5. **Avoid Unnecessary Analysis:** Avoid scanning the entire project or repeatedly analyzing unchanged files.

---

## 1. Inspect Only Relevant Files
- Check only files directly related to the requested change.
- Do not scan the entire project or unrelated modules for small modifications.
- Avoid unnecessary dependency checks and broad analysis.

## 2. Minimal Code Modifications
- Modify or create only the specific lines and files needed.
- Do not rewrite existing code or re-architect working patterns unnecessarily.
- Maintain consistent coding style, indentation, and UI aesthetics.
- Do not modify unrelated apps, views, templates, or styles.

## 3. Targeted Testing Only
- Do not run full project-wide test suites (`python manage.py test`) for minor or localized changes.
- Test only the specific functionality or view modified (e.g., test a single test method or test case).
- Run broader tests only when explicitly requested by the user or when fundamental cross-app dependencies change.

## 4. Direct & Fast Execution
- Understand the requirement and proceed immediately to implementation.
- Avoid lengthy explanations or excessive back-and-forth planning before making changes.
- Reuse existing components, helper functions, and services wherever possible.
- Avoid introducing unnecessary third-party dependencies or boilerplate abstractions.

## 5. Concise Response Format
After completing any change, keep the final response short and clear, containing only:
1. **What was changed:** Brief, direct summary.
2. **Files modified:** Clickable file links.
3. **Verification:** How the specific change was verified.
4. **Important notes:** Any critical context or issues (if applicable).

