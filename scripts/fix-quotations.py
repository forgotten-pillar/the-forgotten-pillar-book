import sys

def is_considered_letter(c: str) -> bool:
    """
    Returns True if c is an alphabetic character (using Unicode)
    for our purposes. For our logic, we want to treat the LaTeX 
    brace characters '{' and '}' as nonalphabetic.
    """
    if c == "{":
        return False
    if c == "}":
        return True
    # if c in "{}":
    #     return False
    return c.isalpha()

def modify_text(text: str) -> str:
    """
    Processes the input text and replaces straight quotes with 
    typographic quotes based on context. The decision is based on 
    whether the character immediately preceding or following the quote 
    is considered alphabetic (using is_considered_letter). This works 
    across Unicode letters (like Ž) and treats '{' and '}' as exceptions.
    
    For double quotes ("):
      - If the previous character is missing or not "alphabetic", 
        replace with an opening double quote “.
      - Else if the next character is missing or not "alphabetic", 
        replace with a closing double quote ”.
      - Otherwise, leave it unchanged.
    
    For single quotes ('):
      - If both previous and next characters exist and are "alphabetic", 
        assume it’s an apostrophe (like in Michael's) and leave it unchanged.
      - Otherwise, if the previous character is missing or not "alphabetic", 
        replace with an opening single quote ‘.
      - Else if the next character is missing or not "alphabetic", 
        replace with a closing single quote ’.
      - Otherwise, leave it unchanged.
    """
    result = []
    for i, ch in enumerate(text):
        if ch in "\"'":
            prev = text[i-1] if i > 0 else None
            nxt = text[i+1] if i < len(text)-1 else None

            if ch == "'":
                # If it's an apostrophe in a contraction, leave it unchanged.
                if prev is not None and nxt is not None and is_considered_letter(prev) and is_considered_letter(nxt):
                    result.append(ch)
                    continue

            # Determine opening vs. closing:
            # If previous character is missing or nonalphabetic, assume opening.
            if prev is None or not is_considered_letter(prev):
                if ch == '"':
                    result.append('“')
                else:
                    result.append('‘')
            # Otherwise, if next character is missing or nonalphabetic, assume closing.
            elif nxt is None or not is_considered_letter(nxt):
                if ch == '"':
                    result.append('”')
                else:
                    result.append('’')
            # Otherwise, if both previous and next characters are alphabetic, then close quotations, this is because how is_considered_letter made with {} brackets.
            elif is_considered_letter(prev) and is_considered_letter(nxt):
                if ch == '"':
                    result.append('”')
                if ch == '\'':
                    result.append('’')
            else:
                result.append(ch)
        else:
            result.append(ch)
    return ''.join(result)

def main():
    if len(sys.argv) != 2:
        print("Usage: python script.py input_file.tex")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    # Read the content from the file.
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Modify the text.
    modified_content = modify_text(content)
    
    # Write the modified content back to the same file.
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(modified_content)
    
    print("File has been updated.")

if __name__ == '__main__':
    main()