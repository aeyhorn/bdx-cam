from pathlib import Path


TEXT_EXTENSIONS = {
    ".nc",
    ".txt",
    ".tap",
    ".gcode",
    ".md",
    ".json",
    ".xml",
    ".log",
    ".csv",
    ".py",
    ".step",
    ".stp",
    ".eia",
    ".cps",
}

TEXT_MIME_TYPES = {
    "application/json",
    "application/xml",
    "application/javascript",
}


def is_text_content(file_name: str, file_type: str | None) -> bool:
    if file_type and (file_type.startswith("text/") or file_type in TEXT_MIME_TYPES):
        return True
    ext = Path(file_name).suffix.lower()
    return ext in TEXT_EXTENSIONS

