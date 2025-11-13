"""
Wordlist processor for handling files and directories.

Supports:
- Single files (username lists, password lists)
- Combo files (username:password format)
- Directory scanning (all .txt files)
- Automatic format detection
"""

from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class WordlistProcessor:
    """
    Process wordlists from files or directories.
    
    Automatically detects:
    - Single column format (usernames or passwords)
    - Combo format (username:password)
    - Multiple files in a directory
    """
    
    @staticmethod
    def is_combo_file(file_path: Path) -> bool:
        """
        Detect if file is combo format (username:password).
        
        Args:
            file_path: Path to wordlist file
            
        Returns:
            True if file contains colon-separated credentials
        """
        if not file_path.exists():
            return False
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                # Check first 10 non-empty lines
                lines_checked = 0
                colon_count = 0
                
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    if ':' in line:
                        colon_count += 1
                    
                    lines_checked += 1
                    if lines_checked >= 10:
                        break
                
                # If >50% have colons, it's a combo file
                if lines_checked > 0:
                    return (colon_count / lines_checked) > 0.5
                    
        except Exception as e:
            logger.warning(f"Error checking combo format for {file_path}: {e}")
        
        return False
    
    @staticmethod
    def collect_wordlist_files(path: Path) -> List[Path]:
        """
        Collect all wordlist files from path.
        
        Args:
            path: File or directory path
            
        Returns:
            List of wordlist file paths
        """
        if path.is_file():
            return [path]
        
        if path.is_dir():
            # Collect all .txt files
            files = list(path.glob("*.txt"))
            logger.info(f"Found {len(files)} wordlist files in {path}")
            return sorted(files)
        
        return []
    
    @staticmethod
    def parse_combo_file(file_path: Path) -> Tuple[List[str], List[str]]:
        """
        Parse combo file (username:password) into separate lists.
        
        Args:
            file_path: Path to combo file
            
        Returns:
            Tuple of (usernames, passwords)
        """
        usernames = set()
        passwords = set()
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    if ':' in line:
                        parts = line.split(':', 1)
                        if len(parts) == 2:
                            usernames.add(parts[0].strip())
                            passwords.add(parts[1].strip())
                    else:
                        # No colon - treat as password
                        passwords.add(line)
        
        except Exception as e:
            logger.error(f"Error parsing combo file {file_path}: {e}")
        
        return sorted(usernames), sorted(passwords)
    
    @staticmethod
    def merge_wordlists(
        username_path: Optional[Path],
        password_path: Optional[Path],
        temp_dir: Path,
        max_entries: int = 1000
    ) -> Tuple[Path, Path]:
        """
        Merge multiple wordlists into temp files for Hydra.
        
        Handles:
        - Single files → use directly
        - Directories → merge all files
        - Combo files → split into user/pass
        - Same path for both → smart categorization by filename
        
        Args:
            username_path: Path to username file/dir (or combo)
            password_path: Path to password file/dir (or combo)
            temp_dir: Directory for temporary merged files
            max_entries: Maximum entries per list (default: 1000 to prevent huge combinations)
            
        Returns:
            Tuple of (merged_usernames_path, merged_passwords_path)
        """
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        usernames = set()
        passwords = set()
        
        # If same path provided for both, use smart categorization
        if username_path and password_path and username_path == password_path:
            logger.info(f"Same path for both lists - using smart categorization")
            files = WordlistProcessor.collect_wordlist_files(username_path)
            
            # Prioritize combo files for efficiency
            combo_files = [f for f in files if WordlistProcessor.is_combo_file(f)]
            non_combo_files = [f for f in files if not WordlistProcessor.is_combo_file(f)]
            
            # Process combo files first (most efficient)
            for file in combo_files:
                logger.info(f"Detected combo file: {file.name}")
                users, pwds = WordlistProcessor.parse_combo_file(file)
                usernames.update(users)
                passwords.update(pwds)
                
                # Stop early if we have enough entries from combo files
                if len(usernames) >= max_entries and len(passwords) >= max_entries:
                    logger.info(f"Reached max entries from combo files - skipping remaining files")
                    break
            
            # Only process non-combo files if we don't have enough entries
            if len(usernames) < max_entries or len(passwords) < max_entries:
                for file in non_combo_files:
                    # Categorize by filename
                    filename_lower = file.name.lower()
                    
                    # Check if file is clearly a username list
                    is_username_file = any(keyword in filename_lower for keyword in [
                        'user', 'username', 'login', 'account', 'admin'
                    ])
                    
                    # Check if file is clearly a password list
                    is_password_file = any(keyword in filename_lower for keyword in [
                        'pass', 'password', 'pwd', 'secret'
                    ])
                    
                    try:
                        with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                        
                        if is_username_file and not is_password_file:
                            logger.info(f"Categorized as username list: {file.name}")
                            usernames.update(lines[:max_entries])  # Limit entries
                        elif is_password_file and not is_username_file:
                            logger.info(f"Categorized as password list: {file.name}")
                            passwords.update(lines[:max_entries])  # Limit entries
                        else:
                            # Ambiguous - add to both for maximum coverage (but limited)
                            logger.warning(f"Ambiguous file (adding to both lists): {file.name}")
                            usernames.update(lines[:max_entries // 2])
                            passwords.update(lines[:max_entries // 2])
                    
                    except Exception as e:
                        logger.error(f"Error reading {file}: {e}")
                    
                    # Stop if we have enough entries
                    if len(usernames) >= max_entries and len(passwords) >= max_entries:
                        logger.info(f"Reached max entries limit ({max_entries}) - stopping")
                        break
        
        else:
            # Different paths - process separately
            
            # Process username source
            if username_path:
                files = WordlistProcessor.collect_wordlist_files(username_path)
                
                for file in files:
                    if WordlistProcessor.is_combo_file(file):
                        logger.info(f"Detected combo file: {file.name}")
                        users, pwds = WordlistProcessor.parse_combo_file(file)
                        usernames.update(users)
                        passwords.update(pwds)
                    else:
                        # Single column - usernames
                        try:
                            with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                                for line in f:
                                    line = line.strip()
                                    if line and not line.startswith('#'):
                                        usernames.add(line)
                                        if len(usernames) >= max_entries:
                                            break
                        except Exception as e:
                            logger.error(f"Error reading {file}: {e}")
                    
                    if len(usernames) >= max_entries:
                        break
            
            # Process password source
            if password_path:
                files = WordlistProcessor.collect_wordlist_files(password_path)
                
                for file in files:
                    if WordlistProcessor.is_combo_file(file):
                        logger.info(f"Detected combo file: {file.name}")
                        users, pwds = WordlistProcessor.parse_combo_file(file)
                        usernames.update(users)
                        passwords.update(pwds)
                    else:
                        # Single column - passwords
                        try:
                            with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                                for line in f:
                                    line = line.strip()
                                    if line and not line.startswith('#'):
                                        passwords.add(line)
                                        if len(passwords) >= max_entries:
                                            break
                        except Exception as e:
                            logger.error(f"Error reading {file}: {e}")
                    
                    if len(passwords) >= max_entries:
                        break
        
        # Write merged files
        username_file = temp_dir / "merged_usernames.txt"
        password_file = temp_dir / "merged_passwords.txt"
        
        with open(username_file, 'w', encoding='utf-8') as f:
            for user in sorted(usernames):
                f.write(f"{user}\n")
        
        with open(password_file, 'w', encoding='utf-8') as f:
            for pwd in sorted(passwords):
                f.write(f"{pwd}\n")
        
        logger.info(
            f"Merged wordlists: {len(usernames)} usernames, {len(passwords)} passwords"
        )
        
        return username_file, password_file
    
    @staticmethod
    def get_wordlist_stats(path: Path) -> Dict[str, Any]:
        """
        Get statistics about wordlist(s).
        
        Args:
            path: File or directory path
            
        Returns:
            Statistics dictionary
        """
        stats = {
            'files': 0,
            'total_lines': 0,
            'unique_entries': 0,
            'is_combo': False,
            'has_usernames': False,
            'has_passwords': False
        }
        
        files = WordlistProcessor.collect_wordlist_files(path)
        stats['files'] = len(files)
        
        all_entries = set()
        has_combo = False
        
        for file in files:
            if WordlistProcessor.is_combo_file(file):
                has_combo = True
                stats['is_combo'] = True
                users, pwds = WordlistProcessor.parse_combo_file(file)
                all_entries.update(users)
                all_entries.update(pwds)
                stats['has_usernames'] = True
                stats['has_passwords'] = True
            else:
                try:
                    with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#'):
                                stats['total_lines'] += 1
                                all_entries.add(line)
                except Exception:
                    pass
        
        stats['unique_entries'] = len(all_entries)
        
        return stats
