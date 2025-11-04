from typing import List, Optional, Callable

import magic

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

KIND_MIME_MAP: dict = {
    "doc": DOC_MIME_TYPES,
    "xls": XLS_MIME_TYPES,
    "ppt": PPT_MIME_TYPES,
    "zip": ZIP_MIME_TYPES,
    # Add more kinds and corresponding MIME lists if needed
}


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
