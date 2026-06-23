#!/usr/bin/env python3
# touchtree.py
import argparse
import sys
from pathlib import Path

def parse_tree_line(line: str) -> tuple[int, str]:
    """
    Extracts the indentation depth and the clean item name from a tree line.
    Supports standard box-drawing characters across different charsets.
    """
    # Replace common tree artifacts with spaces to calculate uniform depth
    cleaned = line.replace('├──', '    ')\
                  .replace('└──', '    ')\
                  .replace('│',   '    ')\
                  .replace('─',   ' ')\
                  .replace('└',   ' ')\
                  .replace('├',   ' ')
    
    stripped = cleaned.lstrip()
    if not stripped:
        return -1, ""
        
    # Standard tree depth is 4 spaces per indentation level
    depth = (len(cleaned) - len(stripped)) // 4
    
    # Clean up trailing folder slashes if present
    name = stripped.rstrip('/')
    return depth, name

def build_from_lines(lines: list[str], root_dir: Path):
    """
    Processes the raw lines to map hierarchy and generate empty folders/files.
    """
    # Keep track of active parent folders at each indentation depth level
    # We initialise level -1 to point to the base output directory
    path_history = {-1: root_dir}
    
    for line in lines:
        line = line.strip('\r\n')
        if not line or line.strip() in ['.', './']:
            continue
            
        depth, name = parse_tree_line(line)
        if depth == -1 or not name:
            continue
            
        # The immediate parent is the folder recorded at the level just above
        parent_path = path_history.get(depth - 1, root_dir)
        target_path = parent_path / name
        
        # Determine if it is a directory or a file based on formatting hints
        is_dir = line.rstrip().endswith('/') or '.' not in name
        
        if is_dir:
            target_path.mkdir(parents=True, exist_ok=True)
            path_history[depth] = target_path
        else:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.touch(exist_ok=True)

def get_interactive_input() -> list[str]:
    """
    Fallback interactive loop collecting lines until a completely empty enter is pressed.
    """
    print("No input file provided. Entering interactive mode.")
    print("--> Paste your tree text below.")
    print("--> Press [ENTER] on a totally blank line when you are finished.")
    print("--> Type 'quit' or 'exit' immediately to cancel the script.")
    print("-" * 50)
    
    lines = []
    while True:
        try:
            line = input()
            # If the very first input or any line is 'quit'/'exit', stop immediately
            if line.strip().lower() in ['quit', 'exit']:
                print("Operation cancelled by user.")
                sys.exit(0)
            # Empty input line acts as the 'done' marker
            if line == "":
                break
            lines.append(line)
        except (KeyboardInterrupt, EOFError):
            print("\nInput interrupted. Exiting.")
            sys.exit(1)
    return lines

def main():
    parser = argparse.ArgumentParser(
        description="Replicate an empty skeleton folder structure from a 'tree' output text layout."
    )
    parser.add_argument(
        '-i', '--input', 
        type=Path, 
        help="Path to a text file containing the output layout of a 'tree' command."
    )
    parser.add_argument(
        '-o', '--output', 
        type=Path, 
        default=Path('./replicated_structure'), 
        help="Target root folder to generate the layout within (Defaults to './replicated_structure')."
    )
    
    args = parser.parse_args()
    
    # Load raw text layout lines either from the file argument or user interactive paste
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
        
    print(f"Creating empty replica structure inside: {args.output.resolve()}")
    build_from_lines(lines, args.output)
    print("Structure successfully created.")

if __name__ == '__main__':
    main()
