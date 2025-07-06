"""
Utility functions for VibeCLI
Includes ANSI colors, path validation, and diff formatting
"""

import os
from pathlib import Path
from rich.console import Console
from rich.syntax import Syntax

console = Console()


class Colors:
    """ANSI color codes for terminal output"""

    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    RESET = "\033[0m"


def print_colored(
    text: str, color: str = Colors.WHITE, bold: bool = False, underline: bool = False
):
    """Print colored text to terminal"""
    style = color
    if bold:
        style += Colors.BOLD
    if underline:
        style += Colors.UNDERLINE

    print(f"{style}{text}{Colors.RESET}")


def validate_directory(path: str) -> bool:
    """Validate if directory exists and is writable"""
    try:
        dir_path = Path(path).resolve()

        # Check if directory exists
        if not dir_path.exists():
            print_colored(f"❌  Directory non esistente: {path}", Colors.RED)
            return False

        # Check if it's actually a directory
        if not dir_path.is_dir():
            print_colored(f"❌  Il percorso non è una directory: {path}", Colors.RED)
            return False

        # Check write permissions
        if not os.access(dir_path, os.W_OK):
            print_colored(f"❌  Permessi di scrittura negati: {path}", Colors.RED)
            return False

        return True

    except Exception as e:
        print_colored(f"❌  Errore nella validazione: {str(e)}", Colors.RED)
        return False


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1

    return f"{size_bytes:.1f} {size_names[i]}"


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to specified length with ellipsis"""
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def format_diff(diff_text: str) -> str:
    """Format diff text with colors for better readability"""
    if not diff_text or diff_text == "📝 Nessuna modifica":
        return diff_text

    lines = diff_text.split("\n")
    formatted_lines = []

    for line in lines:
        if line.startswith("+++") or line.startswith("---"):
            formatted_lines.append(f"{Colors.BOLD}{line}{Colors.RESET}")
        elif line.startswith("@@"):
            formatted_lines.append(f"{Colors.CYAN}{line}{Colors.RESET}")
        elif line.startswith("+"):
            formatted_lines.append(f"{Colors.GREEN}{line}{Colors.RESET}")
        elif line.startswith("-"):
            formatted_lines.append(f"{Colors.RED}{line}{Colors.RESET}")
        else:
            formatted_lines.append(line)

    return "\n".join(formatted_lines)


def safe_filename(filename: str) -> str:
    """Make filename safe for filesystem"""
    # Remove or replace dangerous characters
    unsafe_chars = ["<", ">", ":", '"', "|", "?", "*", "\\", "/"]
    safe_name = filename

    for char in unsafe_chars:
        safe_name = safe_name.replace(char, "_")

    # Remove leading/trailing spaces and dots
    safe_name = safe_name.strip(" .")

    # Ensure it's not empty
    if not safe_name:
        safe_name = "untitled"

    return safe_name


def is_text_file(file_path: Path) -> bool:
    """Check if file is likely a text file"""
    try:
        # Check file extension
        text_extensions = {
            ".txt",
            ".py",
            ".js",
            ".html",
            ".css",
            ".json",
            ".xml",
            ".yaml",
            ".yml",
            ".md",
            ".rst",
            ".cfg",
            ".ini",
            ".conf",
            ".log",
            ".sql",
            ".sh",
            ".bash",
            ".zsh",
            ".fish",
            ".ps1",
            ".bat",
            ".cmd",
            ".java",
            ".c",
            ".cpp",
            ".h",
            ".hpp",
            ".cs",
            ".php",
            ".rb",
            ".go",
            ".rs",
            ".swift",
            ".kt",
            ".scala",
            ".clj",
            ".hs",
            ".ml",
            ".fs",
            ".elm",
            ".ex",
            ".exs",
            ".erl",
            ".pl",
            ".pm",
            ".r",
            ".R",
            ".m",
            ".mm",
            ".vb",
            ".pas",
            ".ada",
            ".f",
            ".f90",
            ".f95",
            ".for",
            ".cob",
            ".cbl",
            ".asm",
            ".s",
            ".S",
            ".tex",
            ".bib",
            ".csv",
            ".tsv",
            ".dockerfile",
            ".gitignore",
            ".gitattributes",
            ".editorconfig",
            ".env",
            ".example",
            ".sample",
            ".template",
        }

        if file_path.suffix.lower() in text_extensions:
            return True

        # Check if file has no extension but common text file names
        text_filenames = {
            "README",
            "LICENSE",
            "CHANGELOG",
            "CONTRIBUTING",
            "AUTHORS",
            "COPYING",
            "INSTALL",
            "NEWS",
            "TODO",
            "HISTORY",
            "NOTICE",
            "Makefile",
            "makefile",
            "Dockerfile",
            "docker-compose",
        }

        if file_path.name in text_filenames:
            return True

        # Try to read first few bytes to check for binary content
        if file_path.exists() and file_path.is_file():
            try:
                with open(file_path, "rb") as f:
                    chunk = f.read(1024)
                    if b"\x00" in chunk:  # Null bytes indicate binary
                        return False
                    # Try to decode as UTF-8
                    chunk.decode("utf-8")
                    return True
            except (UnicodeDecodeError, PermissionError):
                return False

        return False

    except Exception:
        return False


def print_syntax_highlighted(
    content: str, language: str = "text", theme: str = "monokai"
):
    """Print syntax highlighted content using rich"""
    try:
        syntax = Syntax(content, language, theme=theme, line_numbers=True)
        console.print(syntax)
    except Exception:
        # Fallback to plain text
        console.print(content)


def get_file_info(file_path: Path) -> dict:
    """Get comprehensive file information"""
    try:
        if not file_path.exists():
            return {"error": "File non esistente"}

        stat = file_path.stat()

        info = {
            "name": file_path.name,
            "path": str(file_path),
            "size": format_file_size(stat.st_size),
            "size_bytes": stat.st_size,
            "is_file": file_path.is_file(),
            "is_dir": file_path.is_dir(),
            "is_text": is_text_file(file_path) if file_path.is_file() else False,
            "modified": stat.st_mtime,
            "permissions": oct(stat.st_mode)[-3:],
            "readable": os.access(file_path, os.R_OK),
            "writable": os.access(file_path, os.W_OK),
            "executable": os.access(file_path, os.X_OK),
        }

        return info

    except Exception as e:
        return {"error": f"Errore nell'ottenere informazioni: {str(e)}"}


def create_progress_bar(current: int, total: int, width: int = 50) -> str:
    """Create a simple ASCII progress bar"""
    if total == 0:
        return "[" + "=" * width + "]"

    progress = current / total
    filled_width = int(width * progress)
    bar = "=" * filled_width + "-" * (width - filled_width)
    percentage = int(progress * 100)

    return f"[{bar}] {percentage}% ({current}/{total})"


def confirm_action(message: str, default: bool = False) -> bool:
    """Simple confirmation prompt"""
    default_text = "Y/n" if default else "y/N"
    response = input(f"{message} [{default_text}]: ").strip().lower()

    if not response:
        return default

    return response in ["y", "yes", "si", "sì"]


def confirm_yes_no(prompt: str) -> bool:
    """Simple yes/no confirmation prompt"""
    while True:
        response = input(f"{prompt} [y/N] › ").strip().lower()
        if response in ["y", "yes", "si", "sì"]:
            return True
        elif response in ["n", "no", ""] or not response:
            return False
        else:
            print("Rispondi con 'y' per sì o 'n' per no.")


def print_banner(title: str, width: int = 60):
    """Print a formatted banner"""
    border = "=" * width
    title_line = f"| {title.center(width - 4)} |"

    print_colored(border, Colors.CYAN)
    print_colored(title_line, Colors.CYAN)
    print_colored(border, Colors.CYAN)
