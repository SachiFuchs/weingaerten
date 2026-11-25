---
applyTo: "**/*.py"
---

# Clean Code Skill

Apply these rules whenever you write or edit Python code in this workspace.

## 1. Clean Code Principles
- Single Responsibility: each function/class does one thing well.
- Meaningful names: descriptive variable/function/class names, no abbreviations unless universally understood (e.g. `id`, `url`).
- No dead code, no commented-out code blocks left behind.
- Prefer early returns / guard clauses over deep nesting.
- Avoid duplication (DRY): extract repeated logic into helper functions.
- Keep side effects explicit; avoid hidden state mutations.
- Add docstrings (Args/Returns/Raises) for public functions and classes.
- Type hints are required for function signatures (args + return type).

## 1a. The Core Clean Code Principles (detailed)

1. **Meaningful Names**
   Variables, functions, and classes should have intent-revealing names. If
   you need a comment to explain what a variable is, the name is poor.
   Rule of thumb: use searchable, pronounceable names. Avoid single-letter
   variables (like `int d;`) or arbitrary abbreviations.

2. **Functions Should Do One Thing (SRP)**
   A function should do one thing, and do it well. If a function is
   validating an input, updating the database, and sending an email, it
   should be broken into three distinct, smaller functions.
   Rule of thumb: keep functions small. Pass as few arguments as possible
   (ideally zero or one), and avoid boolean "flag arguments" that tell the
   function to do two different things depending on the value passed.

3. **DRY: Don't Repeat Yourself**
   Avoid copying and pasting code. If you find similar logic or repeating
   structures in multiple places, extract it into a central, reusable
   function or class. This ensures that if you need to fix a bug or update
   logic, you only have to do it in one place.

4. **KISS: Keep It Simple, Stupid**
   Always write the simplest possible solution that works. Avoid
   over-engineering or adding complex design patterns for features you
   "might need later" (also known as YAGNI: You Aren't Gonna Need It).

5. **Principle of Least Surprise**
   Your code should behave exactly as a reader or user would intuitively
   expect. Method names should accurately reflect exactly what the
   function does — no hidden side effects or unexpected state changes in
   the background.

6. **Self-Documenting Code**
   Write your code with clear naming and structure so that the code itself
   documents *what* it does. Comments (see 3a) carry the *why*: intent,
   decisions and non-obvious constraints. Keep them in sync with the code,
   since outdated comments are worse than none.

7. **The Boy Scout Rule**
   "Always leave the campground cleaner than you found it." When you
   touch a piece of code, take a few minutes to clean up any messy
   variable names, extract a confusing block into a small function, or
   remove dead code.

## 2. Size Limits
- **Function length**: max **80 lines** (including docstring/blank lines). If a function grows beyond this, split it into smaller private helper functions (e.g. `_collect_x`, `_build_y`, `_parse_z`).
- **File length**: max **256 lines** per file.
  If a file grows beyond this, split it into multiple modules (e.g. by responsibility: `*_client.py`, `*_parsing.py`, `*_formatting.py`) and re-export via `__init__.py` if needed to preserve the public API.

## 2a. Classes and File Structure
- **Prefer classes whenever possible**: group related state and behaviour in a class instead of loose module-level functions. Use module-level functions only for small stateless helpers or entry points (`main`).
- **One class per file**: each class lives in its own module, named after the class in snake_case (e.g. `WallBuilder` -> `wall_builder.py`).
- **Use sub-folders where it adds clarity**: structure related classes in packages (folders with `__init__.py`), e.g. `core/geometry/`, `core/bom/`. Re-export the public classes in the package's `__init__.py`.


## 3. Readability for Humans
- Prioritize clarity over cleverness; avoid one-liners that sacrifice readability.
- Use blank lines to separate logical sections within a function.
- Keep comments purposeful: explain *why*, not *what* (the code should already say *what*).
- Consistent formatting (4-space indents, consistent quote style).
- Prefer explicit over implicit (e.g. explicit `is None` checks instead of falsy checks when `None` has special meaning).
- Public methods in class module should contain the main logic of this method.

## 3a. Comments
- **Add comments**: every class and every public method gets a docstring. Non-trivial blocks (algorithms, geometry, business rules, workarounds) get a short comment explaining *why* they are done this way.
- Keep comments up to date when the code changes; remove comments that no longer match the code.

## 4. When Editing Existing Code
- If an edit would push a function past 80 lines or a file past 256 lines, refactor as part of the change (extract helpers / split files) rather than skipping the limit.
- If a class file exceeds the size limit, split the class by responsibility into collaborating classes (one file each, see 2a).
- Preserve existing public function signatures unless the user explicitly asks for a rename/refactor of the public API.
- After refactors, validate with a syntax/compile check before finishing.

## 5. Add Logging
- add always loggings to python files 

## 6. Jira Acceptance Criteria: Given/When/Then (Behavioral/BDD) Pattern
- Whenever building or generating Jira acceptance criteria (e.g. checklist items for the `acceptance_criteria` custom field), format each criterion using the Given/When/Then behavioral (BDD/Gherkin) pattern.
- Recognize existing Gherkin steps (lines starting with `Given`, `When`, `Then`, `And`, `But`, case-insensitive) and keep them as-is, one checklist item per step.
- If the raw input is plain, non-Gherkin text (e.g. free-form bullet points), auto-wrap it into a single Given/When/Then scenario so acceptance criteria are consistently behavior-driven rather than left as flat statements.
- Keep this logic in a small, pure, testable helper function (e.g. `_build_acceptance_criteria_items`) with type hints and a docstring per the rules above.

