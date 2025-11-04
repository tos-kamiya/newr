#!/usr/bin/env python3

"""
File selector utility: select files by modification time, with kind filtering and flexible slicing.

Supports glob patterns, range slicing (Python slice syntax), and file type filtering via --kind.
"""

import sys
import os
import argparse
from typing import List, Tuple, Dict

from .file_types import get_kind_checker

try:
    from .__about__ import __version__
except Exception:
    __version__ = "(unknown)"


def resolve_files(patterns: List[str]) -> Tuple[List[str], Dict[str, str]]:
    """
    Expand a list of glob patterns and collect matching files.

    Args:
        patterns (List[str]): List of glob/wildcard patterns.
    Returns:
        Tuple[List[str], Dict[str, str]]: List of absolute file paths and mapping of abs paths to original paths.
    """
    import glob

    files: List[str] = []
    path_mapping: Dict[str, str] = {}  # Maps absolute paths to original paths for tilde expansion

    for pat in patterns:
        # Expand tilde in pattern
        expanded_pat = os.path.expanduser(pat)
        matched_files = glob.glob(expanded_pat, recursive=True)

        for f in matched_files:
            if os.path.isfile(f):
                abs_path = os.path.abspath(f)
                files.append(abs_path)

                # Keep track of the original path format (with ~ if applicable)
                if "~" in pat and os.path.expanduser("~") in abs_path:
                    home_path = os.path.expanduser("~")
                    rel_path = os.path.relpath(abs_path, home_path)
                    path_mapping[abs_path] = os.path.join("~", rel_path)
                else:
                    path_mapping[abs_path] = abs_path

    # Remove duplicates while preserving order
    unique_files = []
    seen = set()
    for f in files:
        if f not in seen:
            unique_files.append(f)
            seen.add(f)

    return unique_files, path_mapping


def parse_argv() -> Tuple[argparse.Namespace, argparse.ArgumentParser]:
    """
    Parse command line arguments.

    Returns:
        Tuple[argparse.Namespace, argparse.ArgumentParser]: Parsed arguments and parser instance.
    """
    p = argparse.ArgumentParser(
        description="Select files by modification time, with optional reverse order and kind filtering.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument(
        "-n",
        "--number",
        type=int,
        default=1,
        metavar="N",
        help="Number of files to select (default: %(default)s)",
    )
    p.add_argument(
        "-r",
        "--reverse",
        action="store_true",
        help="Select in ascending (oldest-first) order",
    )
    p.add_argument("-k", "--kind", type=str, help="File kind: doc/xls/ppt/zip/image/video/audio/text")
    p.add_argument("-q", "--quiet", action="store_true", help="Suppress all log output to stderr")
    p.add_argument("file", nargs="+", help="Files/glob patterns")
    p.add_argument(
        "-0",
        "--allow-empty-result",
        action="store_true",
        help="If no files are found, exit without error (do not treat as failure).",
    )
    p.add_argument("--version", action="version", version="%(prog)s " + __version__)
    args = p.parse_args()

    if not args.file:
        p.error("No file patterns provided.")

    if args.number <= 0:
        p.error("-n/--number must be a positive integer")

    return args, p


def main() -> None:
    args, parser = parse_argv()
    script_name = os.path.basename(sys.argv[0])

    # Set up logging function based on quiet mode
    if args.quiet:
        def log(s: str) -> None:
            pass
    else:
        def log(s: str) -> None:
            print(script_name + ": " + s, file=sys.stderr)

    # Step 1: Expand glob patterns to file paths and create path mapping
    all_files, path_mapping = resolve_files(args.file)
    if not all_files:
        if args.allow_empty_result:
            return
        log("No files found matching the given path or wildcard pattern(s).")
        sys.exit(1)

    # Step 2: Sort files by modification time
    all_files = sorted(
        all_files,
        key=lambda f: os.stat(f).st_mtime,
        reverse=not args.reverse,
    )

    # Step 3: Apply kind filter if specified, and select files by slice/count
    needed = args.number
    selected: List[str] = []
    if args.kind:
        kind_checker = get_kind_checker(args.kind)

        # Select files in desired order (newest or oldest)
        count = 0
        for f in all_files:
            if kind_checker(f):
                selected.append(f)
                count += 1
                if count >= needed:
                    break
    else:
        # No kind: just slice the sorted list
        selected = all_files[:needed]

    if not selected:
        if args.allow_empty_result:
            return
        log(
            "No files matched the specified kind filter and slice."
            if args.kind
            else "No files selected from the given input."
        )
        sys.exit(1)
    elif len(selected) < needed:
        if not args.allow_empty_result:
            log(f"Fewer files were found than requested: {len(selected)}")

    # Step 4: Output selected file paths to stdout
    for path in selected:
        # Use the original path format for logging (with ~ if applicable)
        display_path = path_mapping.get(path, path)
        log(f"Selected: {display_path}")

        # Output the absolute path to stdout for programmatic use
        print(path)


if __name__ == "__main__":
    main()
