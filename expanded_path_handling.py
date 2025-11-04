#!/usr/bin/env python3

"""
File selector utility: select files by modification time, with kind filtering and flexible slicing.

Supports glob patterns, range slicing (Python slice syntax), and file type filtering via --kind.
"""

import sys
import os
import argparse
from typing import List, Optional, Callable, Tuple, Dict

import magic

try:
    from newr.__about__ import __version__
except Exception:
    __version__ = "(unknown)"

# Supported MIME types for filtering
DOC_MIME_TYPES: List[str] = [
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.oasis.opendocument.text",
]
XLS_MIME_TYPES: List[str] = [
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.oasis.opendocument.spreadsheet",
]
PPT_MIME_TYPES: List[str] = [
    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/vnd.oasis.opendocument.presentation",
]
ZIP_MIME_TYPES: List[str] = [
    "application/zip",
    "application/x-tar",
    "application/x-bzip2",
    "application/gzip",
    "application/x-7z-compressed",
    "application/x-rar-compressed",
    "application/x-xz",
    "application/x-lzma",
    "application/x-compress",
]

# Additional MIME types for common categories
IMAGE_MIME_TYPES: List[str] = [
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/bmp",
    "image/tiff",
    "image/webp",
    "image/svg+xml",
]
AUDIO_MIME_TYPES: List[str] = [
    "audio/mpeg",
    "audio/wav",
    "audio/ogg",
    "audio/flac",
    "audio/aac",
    "audio/midi",
    "audio/x-ms-wma",
]
VIDEO_MIME_TYPES: List[str] = [
    "video/mp4",
    "video/mpeg",
    "video/quicktime",
    "video/x-msvideo",
    "video/x-ms-wmv",
    "video/webm",
    "video/3gpp",
]
TEXT_MIME_TYPES: List[str] = [
    "text/plain",
    "text/html",
    "text/css",
    "text/csv",
    "text/javascript",
    "text/xml",
    "text/markdown",
]

KIND_MIME_MAP: Dict[str, List[str]] = {
    "doc": DOC_MIME_TYPES,
    "xls": XLS_MIME_TYPES,
    "ppt": PPT_MIME_TYPES,
    "zip": ZIP_MIME_TYPES,
    "image": IMAGE_MIME_TYPES,
    "audio": AUDIO_MIME_TYPES,
    "video": VIDEO_MIME_TYPES,
    "text": TEXT_MIME_TYPES,
}


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


def get_kind_checker(kind: Optional[str]) -> Callable[[str], bool]:
    """
    Return a function to check if a file matches the given kind (by MIME type).

    Args:
        kind (Optional[str]): Kind keyword (e.g. "doc", "xls", etc.)
    Returns:
        Callable[[str], bool]: Function that accepts a file path and returns True if it matches.
    """
    if not kind:
        # No kind specified: always return True
        return lambda x: True
    kind = kind.lower()
    if kind in KIND_MIME_MAP:
        targets = KIND_MIME_MAP[kind]

        def checker(path: str) -> bool:
            mime = magic.from_file(path, mime=True)
            return mime in targets

        return checker

    # Fallback: check if the major MIME type matches the kind
    def checker(path: str) -> bool:
        mime = magic.from_file(path, mime=True)
        return mime.split("/")[0] == kind

    return checker


def parse_argv() -> Tuple[argparse.Namespace, argparse.ArgumentParser]:
    """
    Parse command line arguments.

    Returns:
        Tuple[argparse.Namespace, argparse.ArgumentParser]: Parsed arguments and parser instance.
    """
    parser = argparse.ArgumentParser(
        description="Select files by modification time, with advanced kind filtering and flexible slicing.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "-n", "--number", type=int, default=1, help="Select top N files (N>0: newest, N<0: oldest). (default: 1)"
    )
    parser.add_argument("-k", "--kind", type=str, help="File kind: doc/xls/ppt/zip/image/video/audio/text")
    parser.add_argument("-q", "--quiet", action="store_true", help="Suppress all log output to stderr")
    parser.add_argument("file", nargs="+", help="Files/glob patterns")
    parser.add_argument(
        "-0",
        "--allow-empty-result",
        action="store_true",
        help="If no files are found, exit without error (do not treat as failure).",
    )
    parser.add_argument("--version", action="version", version="%(prog)s " + __version__)
    args = parser.parse_args()
    return args, parser


def main() -> None:
    """
    Main CLI entry point.
    Handles argument parsing, file resolution, sorting, filtering, slicing, and output.
    """
    args, parser = parse_argv()
    script_name = os.path.basename(sys.argv[0])

    # Set up logging function based on quiet mode
    if args.quiet:

        def log(s: str) -> None:
            pass

    else:

        def log(s: str) -> None:
            print(s, file=sys.stderr)

    if not args.file:
        parser.error("No file patterns provided.")

    # Step 1: Expand glob patterns to file paths and create path mapping
    all_files, path_mapping = resolve_files(args.file)
    if not all_files:
        if args.allow_empty_result:
            return
        log(f"{script_name}: No files found matching the given path or wildcard pattern(s).")
        sys.exit(1)

    # Step 2: Sort files by modification time (newest first)
    all_files = sorted(all_files, key=lambda f: os.stat(f).st_mtime, reverse=True)

    # Step 3: Apply kind filter if specified, and select files by slice/count
    selected: List[str] = []
    if args.kind:
        kind_checker = get_kind_checker(args.kind)
        needed = abs(args.number)
        count = 0
        # Select files in desired order (newest or oldest)
        files_iter = all_files if args.number > 0 else reversed(all_files)
        for f in files_iter:
            if kind_checker(f):
                selected.append(f)
                count += 1
                if count >= needed:
                    break
    else:
        # No kind: just slice the sorted list
        selected = all_files[: args.number] if args.number > 0 else all_files[args.number :]

    if not selected:
        if args.allow_empty_result:
            return
        if args.kind:
            log(f"{script_name}: No files matched the specified kind filter and slice.")
        else:
            log(f"{script_name}: No files selected from the given input.")
        sys.exit(1)
    elif len(selected) < abs(args.number):
        if not args.allow_empty_result:
            log(f"{script_name}: Fewer files were found than requested: {len(selected)}")

    # Step 4: Output selected file paths to stdout
    if args.number < 0:
        selected = list(reversed(selected))  # show oldest first

    for path in selected:
        # Use the original path format for logging (with ~ if applicable)
        display_path = path_mapping.get(path, path)
        log(f"{script_name}: Selected {display_path}")
        # Output the absolute path to stdout for programmatic use
        print(path)


if __name__ == "__main__":
    main()
