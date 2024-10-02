"""
This type stub file was generated by pyright.
"""

_logger = ...
handler = ...
formatter = ...
class _Unbuffered:
    """
    Disable buffering for standard output and standard error.

    https://stackoverflow.com/a/107717
    https://docs.python.org/3/library/io.html
    """
    def __init__(self, stream) -> None:
        ...
    
    def __getattr__(self, attr): # -> Any:
        ...
    
    def write(self, b): # -> None:
        ...
    
    def writelines(self, lines): # -> None:
        ...
    


def eprint(*args, **kwargs):
    ...

def get_char(prompt):
    ...

def get_float(prompt): # -> float | None:
    """
    Read a line of text from standard input and return the equivalent float
    as precisely as possible; if text does not represent a double, user is
    prompted to retry. If line can't be read, return None.
    """
    ...

def get_int(prompt): # -> int | None:
    """
    Read a line of text from standard input and return the equivalent int;
    if text does not represent an int, user is prompted to retry. If line
    can't be read, return None.
    """
    ...

def get_string(prompt): # -> str | None:
    """
    Read a line of text from standard input and return it as a string,
    sans trailing line ending. Supports CR (\r), LF (\n), and CRLF (\r\n)
    as line endings. If user inputs only a line ending, returns "", not None.
    Returns None upon error or no input whatsoever (i.e., just EOF).
    """
    ...

