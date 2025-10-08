#!/usr/bin/env python3
"""
Script to generate a directory tree structure and save it to DIRECTORY_STRUCTURE.md
This script runs automatically before each commit via Git pre-commit hook.
"""

import os
import sys
import fnmatch
from pathlib import Path

# Configuration: File extensions to ignore (in addition to .gitignore)
ADDITIONAL_IGNORED_EXTENSIONS = [
    '.pyc', '.pyo', '.pyd',
    '.log', '.tmp', '.cache',
    '.egg-info', '.pytest_cache',
    'node_modules',
    'dump.rdb',  # Redis dump
    '.pem', '.key',  # SSL certificates
]

# Additional directories to ignore (in addition to .gitignore)
ADDITIONAL_IGNORED_DIRS = {
    '__pycache__', '.pytest_cache',
    '.egg-info', 'node_modules', 'fonts'
}

def read_gitignore_patterns(project_root):
    """Read and parse .gitignore file patterns."""
    gitignore_path = project_root / '.gitignore'
    patterns = []

    if gitignore_path.exists():
        try:
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if line and not line.startswith('#'):
                        # Remove trailing slashes for directory patterns
                        pattern = line.rstrip('/')
                        patterns.append(pattern)
        except Exception as e:
            print(f"Warning: Could not read .gitignore: {e}")

    return patterns

def matches_gitignore_pattern(path, patterns, project_root):
    """Check if a path matches any .gitignore pattern."""
    # Get relative path from project root
    try:
        rel_path = Path(path).relative_to(project_root)
        path_str = str(rel_path)
        path_name = Path(path).name

        for pattern in patterns:
            # Handle different pattern types
            if pattern.startswith('*'):
                # Wildcard patterns like *__pycache__
                if fnmatch.fnmatch(path_name, pattern):
                    return True
            elif '/' in pattern:
                # Path-specific patterns like alembic/versions/__pycache__/
                if fnmatch.fnmatch(path_str, pattern) or fnmatch.fnmatch(path_str, pattern + '/*'):
                    return True
            else:
                # Simple name patterns
                if fnmatch.fnmatch(path_name, pattern):
                    return True
                # Also check if any parent directory matches
                if pattern in path_str.split('/'):
                    return True

        return False
    except ValueError:
        # Path is not relative to project root
        return False

def should_ignore(path, gitignore_patterns, project_root):
    """Check if a file or directory should be ignored."""
    path_obj = Path(path)
    path_name = path_obj.name

    # Check gitignore patterns first
    if matches_gitignore_pattern(path, gitignore_patterns, project_root):
        return True

    # Check if it's a hidden file (starts with .) except .gitignore
    if path_name.startswith('.') and path_name not in ['.gitignore']:
        return True

    # Check against additional ignored extensions
    for ext in ADDITIONAL_IGNORED_EXTENSIONS:
        if path_name.endswith(ext) or ext in path_name:
            return True

    # Check against additional ignored directories
    if path_obj.is_dir() and path_name in ADDITIONAL_IGNORED_DIRS:
        return True

    return False

def generate_tree(root_path, gitignore_patterns, project_root, prefix="", is_last=True, max_depth=10, current_depth=0):
    """Generate directory tree structure recursively."""
    if current_depth > max_depth:
        return ""

    root = Path(root_path)
    if not root.exists() or should_ignore(root_path, gitignore_patterns, project_root):
        return ""

    tree_str = ""

    # Add current directory/file
    if current_depth > 0:  # Don't add root directory in the tree
        connector = "└── " if is_last else "├── "
        tree_str += f"{prefix}{connector}{root.name}"
        if root.is_dir():
            tree_str += "/\n"
        else:
            tree_str += "\n"

    # If it's a directory, process its contents
    if root.is_dir():
        try:
            # Get all items in directory, filter out ignored ones
            items = [item for item in root.iterdir()
                    if not should_ignore(item, gitignore_patterns, project_root)]

            # Sort items: directories first, then files
            items.sort(key=lambda x: (not x.is_dir(), x.name.lower()))

            for i, item in enumerate(items):
                is_last_item = i == len(items) - 1
                new_prefix = prefix + ("    " if is_last and current_depth > 0 else "│   " if current_depth > 0 else "")
                tree_str += generate_tree(item, gitignore_patterns, project_root, new_prefix, is_last_item, max_depth, current_depth + 1)

        except PermissionError:
            # Skip directories we can't read
            pass

    return tree_str

def main():
    """Main function to generate and save directory tree."""
    # Get the project root (parent of scripts directory)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    project_name = project_root.name

    print(f"Generating directory tree for {project_name}...")

    # Read .gitignore patterns
    gitignore_patterns = read_gitignore_patterns(project_root)
    print(f"Found {len(gitignore_patterns)} .gitignore patterns")

    # Generate the tree
    tree_content = f"{project_name}/\n"
    tree_content += generate_tree(project_root, gitignore_patterns, project_root, "", True, max_depth=15, current_depth=0)

    # Create list of ignored patterns for documentation
    ignored_items = []
    ignored_items.extend([f"- {pattern}" for pattern in gitignore_patterns])
    ignored_items.extend([f"- {ext}" for ext in ADDITIONAL_IGNORED_EXTENSIONS])
    ignored_items.extend([f"- {dir_name}/" for dir_name in ADDITIONAL_IGNORED_DIRS])

    # Create the markdown content
    markdown_content = f"""# Project Directory Structure

Generated automatically on commit.

```
{tree_content.rstrip()}
```

## Configuration

This tree excludes files and directories matching patterns from:

### .gitignore patterns:
{chr(10).join([f"- {pattern}" for pattern in gitignore_patterns]) if gitignore_patterns else "- (no .gitignore patterns found)"}

### Additional exclusions:
- Python cache files (*.pyc, __pycache__)
- Hidden files and directories (except .gitignore)
- SSL certificates (*.pem, *.key)
- Database dumps (dump.rdb)
- Log files (*.log)
- Temporary files (*.tmp, *.cache)
- Node modules
- Build artifacts (*.egg-info, .pytest_cache)

To modify additional ignored extensions, edit `scripts/generate_tree.py`.
The script automatically respects all patterns in `.gitignore`.
"""

    # Write to DIRECTORY_STRUCTURE.md
    output_file = project_root / "DIRECTORY_STRUCTURE.md"
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(tree_content)

        print(f"Directory tree saved to {output_file}")
        print(f"Excluded {len(gitignore_patterns)} .gitignore patterns + additional rules")

    except Exception as e:
        print(f"Error writing to {output_file}: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
