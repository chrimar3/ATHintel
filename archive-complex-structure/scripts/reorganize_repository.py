#!/usr/bin/env python3
"""
Repository Reorganization Script
Story 1.2: Repository Structure Reorganization
Safely reorganizes repository structure to separate production from experimental code
"""

import os
import sys
import shutil
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import argparse
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RepositoryReorganizer:
    """
    Handles repository structure reorganization
    Moves files while preserving git history
    """
    
    def __init__(self, repo_root: str, dry_run: bool = True):
        """
        Initialize reorganizer
        
        Args:
            repo_root: Root directory of the repository
            dry_run: If True, only preview changes without executing
        """
        self.repo_root = Path(repo_root).resolve()
        self.dry_run = dry_run
        self.moves = []
        self.errors = []
        self.backup_dir = None
        
        # Define the new structure
        self.structure_map = {
            # Production code (real data only)
            'src/core': 'src/production/core',
            'src/adapters': 'src/production/adapters',
            'src/validators': 'src/production/validators',
            
            # Fake data to test fixtures
            'fakedata': 'test/fixtures/fake_data',
            
            # Scripts reorganization
            'scripts/production': 'scripts/production',  # Keep as is
            'scripts/experimental': 'test/experimental_scripts',
            
            # Keep these as-is
            'src/config': 'src/config',
            'src/utils': 'src/utils',
            'realdata': 'realdata',
            'docs': 'docs',
            'reports': 'reports',
            'analysis': 'analysis'
        }
        
        logger.info(f"Initialized reorganizer for {self.repo_root}")
        logger.info(f"Dry run mode: {self.dry_run}")
    
    def validate_repository(self) -> bool:
        """Validate that we're in a git repository"""
        git_dir = self.repo_root / '.git'
        if not git_dir.exists():
            logger.error(f"Not a git repository: {self.repo_root}")
            return False
        
        # Check for uncommitted changes
        result = subprocess.run(
            ['git', 'status', '--porcelain'],
            cwd=self.repo_root,
            capture_output=True,
            text=True
        )
        
        if result.stdout.strip():
            logger.warning("Uncommitted changes detected:")
            logger.warning(result.stdout)
            if not self.dry_run:
                response = input("Continue with uncommitted changes? (y/n): ")
                if response.lower() != 'y':
                    return False
        
        return True
    
    def create_backup(self) -> Path:
        """Create a backup of current structure"""
        if self.dry_run:
            logger.info("Dry run: Skipping backup creation")
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_dir = self.repo_root / f'.backup_{timestamp}'
        
        logger.info(f"Creating backup at {self.backup_dir}")
        
        # Create backup of file structure
        structure_backup = {
            'timestamp': timestamp,
            'structure': {},
            'git_head': self._get_git_head()
        }
        
        for root, dirs, files in os.walk(self.repo_root):
            # Skip git and backup directories
            if '.git' in root or '.backup' in root:
                continue
            
            rel_path = Path(root).relative_to(self.repo_root)
            structure_backup['structure'][str(rel_path)] = files
        
        # Save structure backup
        self.backup_dir.mkdir(exist_ok=True)
        with open(self.backup_dir / 'structure.json', 'w') as f:
            json.dump(structure_backup, f, indent=2)
        
        logger.info("Backup created successfully")
        return self.backup_dir
    
    def _get_git_head(self) -> str:
        """Get current git HEAD commit"""
        result = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            cwd=self.repo_root,
            capture_output=True,
            text=True
        )
        return result.stdout.strip()
    
    def plan_moves(self) -> List[Tuple[Path, Path]]:
        """Plan all file moves"""
        moves = []
        
        for src_pattern, dest_pattern in self.structure_map.items():
            src_path = self.repo_root / src_pattern
            
            if src_path.exists():
                dest_path = self.repo_root / dest_pattern
                
                # If source is a directory, plan moves for all contents
                if src_path.is_dir():
                    for item in src_path.rglob('*'):
                        if item.is_file() and '.git' not in str(item):
                            rel_path = item.relative_to(src_path)
                            dest_item = dest_path / rel_path
                            moves.append((item, dest_item))
                else:
                    moves.append((src_path, dest_path))
        
        self.moves = moves
        return moves
    
    def execute_moves(self) -> bool:
        """Execute the planned moves using git mv"""
        if not self.moves:
            logger.warning("No moves planned")
            return True
        
        success_count = 0
        error_count = 0
        
        for src, dest in self.moves:
            try:
                if self.dry_run:
                    logger.info(f"[DRY RUN] Would move: {src.relative_to(self.repo_root)} -> {dest.relative_to(self.repo_root)}")
                else:
                    # Create destination directory
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Use git mv to preserve history
                    result = subprocess.run(
                        ['git', 'mv', str(src.relative_to(self.repo_root)), str(dest.relative_to(self.repo_root))],
                        cwd=self.repo_root,
                        capture_output=True,
                        text=True
                    )
                    
                    if result.returncode == 0:
                        logger.info(f"Moved: {src.relative_to(self.repo_root)} -> {dest.relative_to(self.repo_root)}")
                        success_count += 1
                    else:
                        # Fallback to regular move if git mv fails
                        shutil.move(str(src), str(dest))
                        subprocess.run(['git', 'add', str(dest.relative_to(self.repo_root))], cwd=self.repo_root)
                        subprocess.run(['git', 'rm', str(src.relative_to(self.repo_root))], cwd=self.repo_root)
                        logger.info(f"Moved (fallback): {src.relative_to(self.repo_root)} -> {dest.relative_to(self.repo_root)}")
                        success_count += 1
                        
            except Exception as e:
                logger.error(f"Failed to move {src}: {e}")
                self.errors.append((src, dest, str(e)))
                error_count += 1
        
        logger.info(f"Moves completed: {success_count} successful, {error_count} failed")
        return error_count == 0
    
    def update_imports(self) -> bool:
        """Update Python imports to reflect new structure"""
        if self.dry_run:
            logger.info("[DRY RUN] Would update imports")
            return True
        
        logger.info("Updating Python imports...")
        
        # Define import replacements
        replacements = [
            ('from src.core', 'from src.production.core'),
            ('import src.core', 'import src.production.core'),
            ('from src.adapters', 'from src.production.adapters'),
            ('import src.adapters', 'import src.production.adapters'),
        ]
        
        # Find all Python files
        python_files = list(self.repo_root.glob('**/*.py'))
        
        updated_count = 0
        for py_file in python_files:
            if '.git' in str(py_file) or '.backup' in str(py_file):
                continue
            
            try:
                with open(py_file, 'r') as f:
                    content = f.read()
                
                original_content = content
                for old, new in replacements:
                    content = content.replace(old, new)
                
                if content != original_content:
                    with open(py_file, 'w') as f:
                        f.write(content)
                    updated_count += 1
                    logger.debug(f"Updated imports in {py_file.relative_to(self.repo_root)}")
                    
            except Exception as e:
                logger.error(f"Failed to update {py_file}: {e}")
        
        logger.info(f"Updated imports in {updated_count} files")
        return True
    
    def update_documentation(self) -> bool:
        """Update README and documentation"""
        if self.dry_run:
            logger.info("[DRY RUN] Would update documentation")
            return True
        
        readme_path = self.repo_root / 'README.md'
        if readme_path.exists():
            logger.info("Updating README.md...")
            
            # Add reorganization notice
            notice = """
## 📁 Repository Structure (Updated)

The repository has been reorganized to separate production code from experimental/test code:

```
ATHintel/
├── src/
│   ├── production/     # Production code (real data only)
│   │   ├── core/       # Core business logic
│   │   ├── adapters/   # External integrations
│   │   └── validators/ # Data validation
│   ├── config/         # Configuration
│   └── utils/          # Shared utilities
├── test/
│   ├── fixtures/       # Test data (including fake data)
│   ├── unit/           # Unit tests
│   └── integration/    # Integration tests
├── realdata/           # Real property data
├── scripts/
│   └── production/     # Production scripts
└── docs/               # Documentation
```

**Note:** All fake/synthetic data has been moved to `test/fixtures/` to ensure production code only processes real data.
"""
            
            try:
                with open(readme_path, 'r') as f:
                    content = f.read()
                
                # Add notice after the first heading
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if line.startswith('# '):
                        lines.insert(i + 1, notice)
                        break
                
                with open(readme_path, 'w') as f:
                    f.write('\n'.join(lines))
                
                logger.info("README.md updated")
                
            except Exception as e:
                logger.error(f"Failed to update README: {e}")
                return False
        
        return True
    
    def verify_structure(self) -> bool:
        """Verify the new structure is correct"""
        logger.info("Verifying new structure...")
        
        expected_dirs = [
            'src/production/core',
            'src/production/adapters',
            'src/production/validators',
            'src/config',
            'src/utils',
            'test/fixtures',
            'test/unit',
            'test/integration',
            'realdata',
            'scripts/production',
            'docs'
        ]
        
        missing = []
        for dir_path in expected_dirs:
            full_path = self.repo_root / dir_path
            if not full_path.exists():
                missing.append(dir_path)
        
        if missing:
            logger.warning(f"Missing directories: {missing}")
            return False
        
        # Check that fakedata is gone
        if (self.repo_root / 'fakedata').exists():
            logger.warning("fakedata directory still exists")
            return False
        
        logger.info("✅ Structure verification passed")
        return True
    
    def create_rollback_script(self) -> Optional[Path]:
        """Create a rollback script"""
        if self.dry_run:
            logger.info("[DRY RUN] Would create rollback script")
            return None
        
        rollback_script = self.repo_root / 'rollback_reorg.sh'
        
        script_content = f"""#!/bin/bash
# Rollback script for repository reorganization
# Generated: {datetime.now().isoformat()}

echo "Rolling back repository reorganization..."

# Reset to previous git state
git reset --hard {self._get_git_head()}

echo "Rollback complete"
echo "You may need to run: git clean -fd"
"""
        
        with open(rollback_script, 'w') as f:
            f.write(script_content)
        
        rollback_script.chmod(0o755)
        logger.info(f"Rollback script created: {rollback_script}")
        
        return rollback_script
    
    def generate_report(self) -> str:
        """Generate reorganization report"""
        report = f"""
Repository Reorganization Report
================================
Timestamp: {datetime.now().isoformat()}
Repository: {self.repo_root}
Dry Run: {self.dry_run}

Moves Planned: {len(self.moves)}
Errors: {len(self.errors)}

Structure Changes:
------------------
"""
        
        for src, dest in self.moves[:10]:  # Show first 10 moves
            report += f"  {src.relative_to(self.repo_root)} -> {dest.relative_to(self.repo_root)}\n"
        
        if len(self.moves) > 10:
            report += f"  ... and {len(self.moves) - 10} more\n"
        
        if self.errors:
            report += "\nErrors:\n-------\n"
            for src, dest, error in self.errors:
                report += f"  {src.relative_to(self.repo_root)}: {error}\n"
        
        return report
    
    def run(self) -> bool:
        """Execute the full reorganization"""
        logger.info("Starting repository reorganization...")
        
        # Step 1: Validate repository
        if not self.validate_repository():
            return False
        
        # Step 2: Create backup
        if not self.dry_run:
            self.create_backup()
        
        # Step 3: Plan moves
        self.plan_moves()
        logger.info(f"Planned {len(self.moves)} file moves")
        
        if not self.moves:
            logger.info("No moves needed - repository may already be organized")
            return True
        
        # Step 4: Execute moves
        if not self.execute_moves():
            logger.error("Some moves failed")
            if not self.dry_run:
                logger.info("Run rollback script to restore previous state")
            return False
        
        # Step 5: Update imports
        if not self.dry_run:
            self.update_imports()
        
        # Step 6: Update documentation
        if not self.dry_run:
            self.update_documentation()
        
        # Step 7: Verify structure
        if not self.dry_run:
            self.verify_structure()
        
        # Step 8: Create rollback script
        if not self.dry_run:
            self.create_rollback_script()
        
        # Generate report
        report = self.generate_report()
        logger.info(report)
        
        # Save report
        if not self.dry_run:
            report_file = self.repo_root / 'reorganization_report.txt'
            with open(report_file, 'w') as f:
                f.write(report)
            logger.info(f"Report saved to {report_file}")
        
        logger.info("✅ Repository reorganization completed successfully")
        return True


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Reorganize repository structure to separate production from experimental code'
    )
    parser.add_argument(
        '--repo-root',
        default='.',
        help='Repository root directory (default: current directory)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        default=True,
        help='Preview changes without executing (default: True)'
    )
    parser.add_argument(
        '--execute',
        action='store_true',
        help='Actually execute the reorganization'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Override dry_run if execute is specified
    dry_run = not args.execute
    
    if not dry_run:
        response = input("⚠️  This will reorganize your repository structure. Continue? (yes/no): ")
        if response.lower() != 'yes':
            logger.info("Reorganization cancelled")
            return
    
    reorganizer = RepositoryReorganizer(args.repo_root, dry_run=dry_run)
    success = reorganizer.run()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()