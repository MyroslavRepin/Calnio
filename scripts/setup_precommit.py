#!/usr/bin/env python3
"""
Setup script to install the Git pre-commit hook for directory tree generation.
Run this script to set up or update the pre-commit hook.
"""

import os
import shutil
import stat
from pathlib import Path
from server.app.core.logging_config import logger

def setup_precommit_hook():
    """Install the pre-commit hook."""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Pre-commit hook content
    hook_content = '''#!/bin/sh
# Git pre-commit hook to generate directory tree structure
# This file should be placed in .git/hooks/pre-commit and made executable

echo "Generating directory tree structure..."

# Run the Python script to generate the tree
python3 scripts/generate_tree.py

# Check if the script ran successfully
if [ $? -eq 0 ]; then
    # Add the generated file to the commit
    git add DIRECTORY_STRUCTURE.md
    echo "Directory structure updated and added to commit"
else
    echo "Failed to generate directory tree"
    exit 1
fi

exit 0'''
    
    # Path to the pre-commit hook
    hooks_dir = project_root / '.git' / 'hooks'
    hook_file = hooks_dir / 'pre-commit'
    
    try:
        # Ensure hooks directory exists
        hooks_dir.mkdir(parents=True, exist_ok=True)
        
        # Write the hook file
        with open(hook_file, 'w', encoding='utf-8') as f:
            f.write(hook_content)
        
        # Make it executable
        hook_file.chmod(hook_file.stat().st_mode | stat.S_IEXEC)
        
        logger.info("Pre-commit hook installed successfully!")
        logger.info(f"   Location: {hook_file}")
        logger.info("   The directory tree will now be updated automatically before each commit.")

        return True
        
    except Exception as e:
        logger.error(f"Error setting up pre-commit hook: {e}")
        return False

def test_tree_generation():
    """Test the tree generation script."""
    logger.info("Testing directory tree generation...")

    script_dir = Path(__file__).parent
    generate_script = script_dir / 'generate_tree.py'
    
    if not generate_script.exists():
        logger.error("generate_tree.py not found!")
        return False
    
    # Run the script
    import subprocess
    try:
        result = subprocess.run(['python3', str(generate_script)], 
                              capture_output=True, text=True, cwd=script_dir.parent)
        
        if result.returncode == 0:
            logger.info("Tree generation test successful!")
            logger.info("   DIRECTORY_STRUCTURE.md should be created/updated")
            return True
        else:
            logger.error(f"Tree generation failed: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Error running test: {e}")
        return False

def main():
    """Main setup function."""
    logger.info("Setting up directory tree pre-commit hook...")

    # Test tree generation first
    if not test_tree_generation():
        logger.error("Setup aborted due to test failure.")
        return 1
    
    # Install the hook
    if setup_precommit_hook():
        logger.info("Setup complete!")
        logger.info("Next steps:")
        logger.info("1. Make a test commit to see the hook in action")
        logger.info("2. Check DIRECTORY_STRUCTURE.md to see the generated tree")
        logger.info("3. Modify IGNORED_EXTENSIONS in generate_tree.py to customize what's excluded")
        return 0
    else:
        return 1

if __name__ == "__main__":
    exit(main())
