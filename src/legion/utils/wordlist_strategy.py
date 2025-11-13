"""
Wordlist Strategy Manager for Hydra Attacks.

This module analyzes wordlist directories and determines the optimal
attack strategy: combo-mode vs separate username/password lists.

Author: Gotham Security
Date: 2025-11-13
"""

import logging
from pathlib import Path
from typing import Optional, Tuple, List, Dict
from dataclasses import dataclass
from enum import Enum

from legion.utils.wordlist_processor import WordlistProcessor

logger = logging.getLogger(__name__)


class AttackMode(Enum):
    """Hydra attack modes."""
    COMBO = "combo"          # -C file (user:pass format)
    SEPARATE = "separate"    # -L users -P passwords
    MIXED = "mixed"          # Combo files + separate lists


@dataclass
class WordlistAnalysis:
    """Analysis results for wordlist directory."""
    mode: AttackMode
    combo_files: List[Path]
    username_files: List[Path]
    password_files: List[Path]
    ambiguous_files: List[Path]
    total_combo_entries: int
    total_username_entries: int
    total_password_entries: int
    estimated_combinations: int
    recommendation: str


class WordlistStrategy:
    """
    Analyzes wordlist directories and recommends optimal Hydra attack strategy.
    
    This class examines all wordlist files and categorizes them into:
    - Combo files (user:pass format) → Use Hydra -C mode
    - Username files → Use Hydra -L mode
    - Password files → Use Hydra -P mode
    - Ambiguous files → User decision required
    
    The goal is to minimize attack time by using the most efficient mode.
    """
    
    @staticmethod
    def analyze_directory(path: Path, max_combo_entries: int = 10000) -> WordlistAnalysis:
        """
        Analyze wordlist directory and recommend attack strategy.
        
        Args:
            path: Directory containing wordlist files
            max_combo_entries: Maximum combo entries to use (prevents huge files)
        
        Returns:
            WordlistAnalysis with categorized files and recommendations
        """
        if not path.exists():
            raise ValueError(f"Path does not exist: {path}")
        
        # Collect all wordlist files
        all_files = WordlistProcessor.collect_wordlist_files(path)
        
        combo_files = []
        username_files = []
        password_files = []
        ambiguous_files = []
        
        total_combo_entries = 0
        total_username_entries = 0
        total_password_entries = 0
        
        # Categorize each file
        for file in all_files:
            if WordlistProcessor.is_combo_file(file):
                combo_files.append(file)
                # Count entries
                try:
                    with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                        entries = sum(1 for line in f if line.strip() and ':' in line and not line.startswith('#'))
                        total_combo_entries += entries
                except Exception as e:
                    logger.error(f"Error counting entries in {file}: {e}")
            
            else:
                # Categorize by filename
                filename_lower = file.name.lower()
                
                is_username_file = any(keyword in filename_lower for keyword in [
                    'user', 'username', 'login', 'account', 'admin'
                ])
                
                is_password_file = any(keyword in filename_lower for keyword in [
                    'pass', 'password', 'pwd', 'secret'
                ])
                
                # Count entries
                try:
                    with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                        entries = sum(1 for line in f if line.strip() and not line.startswith('#'))
                    
                    if is_username_file and not is_password_file:
                        username_files.append(file)
                        total_username_entries += entries
                    elif is_password_file and not is_username_file:
                        password_files.append(file)
                        total_password_entries += entries
                    else:
                        # Ambiguous - could be either
                        ambiguous_files.append(file)
                        logger.warning(f"Ambiguous file: {file.name}")
                
                except Exception as e:
                    logger.error(f"Error reading {file}: {e}")
        
        # Determine optimal mode
        mode, recommendation = WordlistStrategy._determine_mode(
            combo_files,
            username_files,
            password_files,
            ambiguous_files,
            total_combo_entries,
            total_username_entries,
            total_password_entries,
            max_combo_entries
        )
        
        # Calculate estimated combinations
        if mode == AttackMode.COMBO:
            estimated_combinations = min(total_combo_entries, max_combo_entries)
        elif mode == AttackMode.SEPARATE:
            estimated_combinations = total_username_entries * total_password_entries
        else:  # MIXED
            combo_part = min(total_combo_entries, max_combo_entries)
            separate_part = total_username_entries * total_password_entries
            estimated_combinations = combo_part + separate_part
        
        return WordlistAnalysis(
            mode=mode,
            combo_files=combo_files,
            username_files=username_files,
            password_files=password_files,
            ambiguous_files=ambiguous_files,
            total_combo_entries=total_combo_entries,
            total_username_entries=total_username_entries,
            total_password_entries=total_password_entries,
            estimated_combinations=estimated_combinations,
            recommendation=recommendation
        )
    
    @staticmethod
    def _determine_mode(
        combo_files: List[Path],
        username_files: List[Path],
        password_files: List[Path],
        ambiguous_files: List[Path],
        combo_count: int,
        user_count: int,
        pass_count: int,
        max_combo: int
    ) -> Tuple[AttackMode, str]:
        """
        Determine optimal attack mode based on file analysis.
        
        Priority:
        1. COMBO mode if we have combo files (most efficient)
        2. SEPARATE mode if we have clear username/password split
        3. MIXED mode if we have both
        
        Args:
            combo_files: List of combo files
            username_files: List of username files
            password_files: List of password files
            ambiguous_files: List of ambiguous files
            combo_count: Total combo entries
            user_count: Total username entries
            pass_count: Total password entries
            max_combo: Maximum combo entries to use
        
        Returns:
            Tuple of (AttackMode, recommendation string)
        """
        
        # Priority 1: Combo files exist and are reasonable size
        if combo_files and combo_count > 0:
            if combo_count <= max_combo:
                return (
                    AttackMode.COMBO,
                    f"Use COMBO mode: {len(combo_files)} combo file(s) with {combo_count} entries. "
                    f"Most efficient approach - Hydra will test exact pairs."
                )
            else:
                # Too many combo entries - limit them
                return (
                    AttackMode.COMBO,
                    f"Use COMBO mode with LIMIT: {combo_count} entries available, limiting to {max_combo}. "
                    f"Consider reducing combo files or increasing max_combo parameter."
                )
        
        # Priority 2: Clear username/password split
        if username_files and password_files:
            combinations = user_count * pass_count
            
            if combinations > 10_000_000:  # 10 million
                return (
                    AttackMode.SEPARATE,
                    f"⚠️ SEPARATE mode with HIGH combinations: {user_count} users × {pass_count} passwords = "
                    f"{combinations:,} combinations. This may take a VERY long time! "
                    f"Consider reducing wordlists or using combo files instead."
                )
            else:
                return (
                    AttackMode.SEPARATE,
                    f"Use SEPARATE mode: {user_count} users × {pass_count} passwords = "
                    f"{combinations:,} combinations. Reasonable attack size."
                )
        
        # Priority 3: Only username files (missing passwords)
        if username_files and not password_files:
            return (
                AttackMode.SEPARATE,
                f"⚠️ Only USERNAME files found ({user_count} entries). "
                f"You need to provide password files or combo files for the attack to work!"
            )
        
        # Priority 4: Only password files (missing usernames)
        if password_files and not username_files:
            return (
                AttackMode.SEPARATE,
                f"⚠️ Only PASSWORD files found ({pass_count} entries). "
                f"You need to provide username files or combo files for the attack to work!"
            )
        
        # Priority 5: Only ambiguous files
        if ambiguous_files:
            return (
                AttackMode.SEPARATE,
                f"⚠️ Only AMBIGUOUS files found. Cannot determine if they contain usernames or passwords. "
                f"Please rename files with 'user' or 'pass' keywords, or use combo format (user:pass)."
            )
        
        # No files found
        return (
            AttackMode.SEPARATE,
            "❌ No wordlist files found! Directory is empty or contains no .txt files."
        )
    
    @staticmethod
    def prepare_combo_file(
        combo_files: List[Path],
        temp_dir: Path,
        max_entries: int = 10000
    ) -> Path:
        """
        Merge multiple combo files into single temp file for Hydra -C mode.
        
        Args:
            combo_files: List of combo files to merge
            temp_dir: Directory for temporary file
            max_entries: Maximum entries to include
        
        Returns:
            Path to merged combo file
        """
        temp_dir.mkdir(parents=True, exist_ok=True)
        merged_file = temp_dir / "merged_combo.txt"
        
        entries = set()
        
        for file in combo_files:
            try:
                with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        line = line.strip()
                        if line and ':' in line and not line.startswith('#'):
                            entries.add(line)
                            
                            if len(entries) >= max_entries:
                                logger.warning(f"Reached max combo entries ({max_entries}) - stopping")
                                break
                
                if len(entries) >= max_entries:
                    break
            
            except Exception as e:
                logger.error(f"Error reading combo file {file}: {e}")
        
        # Write merged file
        with open(merged_file, 'w', encoding='utf-8') as f:
            for entry in sorted(entries):
                f.write(f"{entry}\n")
        
        logger.info(f"Created merged combo file: {len(entries)} entries → {merged_file}")
        
        return merged_file
    
    @staticmethod
    def prepare_separate_files(
        username_files: List[Path],
        password_files: List[Path],
        temp_dir: Path,
        max_entries: int = 1000
    ) -> Tuple[Path, Path]:
        """
        Merge username and password files into separate temp files for Hydra -L/-P mode.
        
        Args:
            username_files: List of username files
            password_files: List of password files
            temp_dir: Directory for temporary files
            max_entries: Maximum entries per file
        
        Returns:
            Tuple of (username_file, password_file)
        """
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        usernames = set()
        passwords = set()
        
        # Merge username files
        for file in username_files:
            try:
                with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            usernames.add(line)
                            
                            if len(usernames) >= max_entries:
                                break
                
                if len(usernames) >= max_entries:
                    break
            
            except Exception as e:
                logger.error(f"Error reading username file {file}: {e}")
        
        # Merge password files
        for file in password_files:
            try:
                with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            passwords.add(line)
                            
                            if len(passwords) >= max_entries:
                                break
                
                if len(passwords) >= max_entries:
                    break
            
            except Exception as e:
                logger.error(f"Error reading password file {file}: {e}")
        
        # Write files
        username_file = temp_dir / "merged_usernames.txt"
        password_file = temp_dir / "merged_passwords.txt"
        
        with open(username_file, 'w', encoding='utf-8') as f:
            for user in sorted(usernames):
                f.write(f"{user}\n")
        
        with open(password_file, 'w', encoding='utf-8') as f:
            for pwd in sorted(passwords):
                f.write(f"{pwd}\n")
        
        logger.info(
            f"Created separate wordlists: {len(usernames)} users, {len(passwords)} passwords"
        )
        
        return username_file, password_file
