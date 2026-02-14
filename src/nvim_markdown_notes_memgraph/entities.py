"""Entity extraction for markdown notes.

This module provides shared regex patterns and extraction functions for
wikilinks, mentions, and hashtags in markdown files.
"""

import os
import re
from pathlib import Path
from typing import Dict, List


# Regex patterns for entity extraction
WIKILINK_PATTERN = re.compile(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]')
MENTION_PATTERN = re.compile(r'@([a-zA-Z][a-zA-Z0-9_-]*)')
HASHTAG_PATTERN = re.compile(r'(?<![/=])#([a-zA-Z][a-zA-Z0-9_-]*)')

# Hashtags to exclude (common false positives)
EXCLUDED_HASHTAGS = {'gid', 'browse', 'edit', 'resource'}


def extract_wikilinks(line: str, line_num: int, notes_root: str) -> List[Dict]:
    """Extract wikilinks from a line.

    Args:
        line: Line of text to parse
        line_num: Line number (1-indexed)
        notes_root: Root directory for notes

    Returns:
        List of wikilink dictionaries with target, target_path, and line_number
    """
    wikilinks = []
    for match in WIKILINK_PATTERN.finditer(line):
        link_text = match.group(1)
        target_path = os.path.join(notes_root, link_text + '.md')
        wikilinks.append({
            'target': link_text,
            'target_path': target_path,
            'line_number': line_num
        })
    return wikilinks


def extract_mentions(line: str, line_num: int) -> List[Dict]:
    """Extract @mentions from a line.

    Filters out email addresses by checking what follows the mention.

    Args:
        line: Line of text to parse
        line_num: Line number (1-indexed)

    Returns:
        List of mention dictionaries with name and line_number
    """
    mentions = []
    for match in MENTION_PATTERN.finditer(line):
        name = match.group(1)
        end_pos = match.end()
        rest_of_line = line[end_pos:]
        # Skip if this is part of an email
        if rest_of_line.startswith(('@', '.com', '.co', '.org', '.io', '.nl', '.uk')):
            continue
        mentions.append({
            'name': name,
            'line_number': line_num
        })
    return mentions


def extract_hashtags(line: str, line_num: int) -> List[Dict]:
    """Extract #hashtags from a line.

    Excludes common false positives like #gid, #browse, etc.

    Args:
        line: Line of text to parse
        line_num: Line number (1-indexed)

    Returns:
        List of hashtag dictionaries with name and line_number
    """
    hashtags = []
    for match in HASHTAG_PATTERN.finditer(line):
        tag = match.group(1)
        if tag not in EXCLUDED_HASHTAGS:
            hashtags.append({
                'name': tag,
                'line_number': line_num
            })
    return hashtags


def extract_from_file(filepath: str, notes_root: str = None) -> Dict:
    """Extract all entities from a markdown file.

    Args:
        filepath: Path to the markdown file
        notes_root: Root directory for notes (defaults to file's parent dir)

    Returns:
        Dictionary with path, title, content, wikilinks, mentions, and hashtags
    """
    if notes_root is None:
        notes_root = os.path.dirname(filepath)

    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception:
        return {
            'path': filepath,
            'title': Path(filepath).stem,
            'content': '',
            'wikilinks': [],
            'mentions': [],
            'hashtags': []
        }

    lines = content.split('\n')
    title = lines[0] if lines else Path(filepath).stem
    title = re.sub(r'^#+ ', '', title)  # Remove heading prefix

    wikilinks = []
    mentions = []
    hashtags = []

    for line_num, line in enumerate(lines, 1):
        wikilinks.extend(extract_wikilinks(line, line_num, notes_root))
        mentions.extend(extract_mentions(line, line_num))
        hashtags.extend(extract_hashtags(line, line_num))

    return {
        'path': filepath,
        'title': title,
        'content': content,
        'wikilinks': wikilinks,
        'mentions': mentions,
        'hashtags': hashtags
    }
