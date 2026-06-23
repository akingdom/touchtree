#!/usr/bin/env python3
# touchtree.py
import argparse
import sys
import re
from pathlib import Path

def parse_tree_line(line: str) -> tuple[int, str]:
    """
    Normalises all whitespace variations (including non-breaking spaces) and 
    extracts the nesting depth based on the length of the structural prefix.
    """
    # Replace non-breaking spaces (\xa0) with standard spaces
    line_clean = line.replace('\xa0', ' ')
    
    # Match any combination of leading spaces, tabs, and box-drawing elements
    match = re.match(r'^([\s│├└─]+)', line_clean)
    if not match:
        return 0, line_clean.strip().rstrip('/')
        
    prefix = match.group(1)
    name = line_clean[len(prefix):].strip().rstrip('/')
    
    # Standard tree structures use exactly 4 characters per nesting level
    depth = len(prefix) // 4
    return depth, name

def build_from_lines(lines: list[str], root_dir: Path):
    """
    Maintains an active directory stack based on exact node depth to accurately 
    place files inside their respective parent directories.
    """
    # Level 0 represents items sitting directly in the root target directory
    dir_stack = {0: root_dir}
    
    for line in lines:
        if not line.strip():
            continue
            
        depth, name = parse_tree_line(line)
        if not name or name in ['.', './']:
            continue
            
        # Retrieve the immediate parent directory recorded one level above this item
        parent_path = dir_stack.get(depth, root_dir)
        target_path = parent_path / name
        
        # Explicit trailing slashes or the total absence of an extension dot flags a folder
        is_dir = line.rstrip().endswith('/') or '.' not in name
        
        if is_dir:
            target_path.mkdir(parents=True, exist_ok=True)
            # Save this directory path context to handle any deeper nested children next
            dir_stack[depth + 1] = target_path
        else:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.touch(exist_ok=True)

def get_interactive_input() -> list[str]:
    """
    Fallback interactive loop collecting lines. 
    Pressing Enter on the very first prompt quits immediately.
    """
    print("No input file provided. Entering interactive mode.")
    print("--> Paste your tree text below.")
    print("--> Press [ENTER] on a blank line when you are finished.")
    print("--> NOTE: Pressing [ENTER] immediately on the first empty line will quit.")
    print("-" * 50)
    
    lines = []
    is_first_line = True
    
    while True:
        try:
            line = input()
            if line == "":
                if is_first_line:
                    print("No input provided. Exiting.")
                    sys.exit(0)
                break
            lines.append(line)
            is_first_line = False
        except (KeyboardInterrupt, EOFError):
            print("\nInput interrupted. Exiting.")
            sys.exit(1)
    return lines

def main():
    parser = argparse.ArgumentParser(
        description="touchtree: Replicate an empty skeleton folder structure from a 'tree' output layout."
    )
    parser.add_argument(
        '-i', '--input', 
        type=Path, 
        help="Path to a text file containing the output layout of a 'tree' command."
    )
    parser.add_argument(
        '-o', '--output', 
        type=Path, 
        default=Path('.'), 
        help="Target root folder to generate the layout within (Defaults to current directory '.')."
    )
    parser.add_argument(
        '-y', '--yes',
        action='store_true',
        help="Bypass confirmation prompt and proceed immediately with structure creation."
    )
    
    args = parser.parse_args()
    
    if args.input:
        if not args.input.is_file():
            print(f"Error: Input file '{args.input}' not found.", file=sys.stderr)
            sys.exit(1)
        lines = args.input.read_text(encoding='utf-8', errors='ignore').splitlines()
    else:
        lines = get_interactive_input()
        
    if not lines:
        print("No valid tree layout data was provided. Exiting.")
        sys.exit(0)
        
    target_dir = args.output.resolve()
    if not args.yes:
        print(f"\nWARNING: About to generate file structure inside: {target_dir}")
        response = input("Are you sure you want to proceed? (y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            print("Operation aborted.")
            sys.exit(0)
            
    print(f"Creating empty replica structure inside: {target_dir}")
    build_from_lines(lines, args.output)
    print("Structure successfully created.")

if __name__ == '__main__':
    main()
