# Importing python's regex module, re provides pattern matching and subsitution function
import re

# CPU bound string work so no async
# why order matters: 
# if you strip first, you might lose intentional leading/trailing content
# if you normalize spaces before newlines, you might mishandle mixed line endings
def clean_text(text: str) -> str:
    """Normalize white space and newlines"""
    # Normalize new lines
    # re.sub(pattern, replacement, string): substitutes all matches of pattern with replacement in string
    # r'\r\n': raw string pattern matching Windows line endings (\r\n)
    # handles \r\n before standalone \r to avoid double-processing
    text = re.sub(r'\r\n', '\n', text)
    text = re.sub(r'\r', '\n', text)

    # Normalize multiple spaces to single space but preserve newlines
    # r'[ \t]+': character class matching one or more spaces or tabs
    # [ \t]: matches a space or tab
    # +: one or more
    # ' ': Replaces with a single space
    text = re.sub(r'[ \t]+', ' ', text)

    # Remove trailing whitespace from lines
    # text.split('\n'): splits into lines (list of strings).
    # line.rstrip(): removes trailing whitespace from each line.
    # '\n'.join(...): joins lines back with \n.
    # why this approach: processes line-by-line to remove trailing spaces while keeping line structure.
    text = '\n'.join(line.rstrip() for line in text.split('\n'))
    return text.strip()

