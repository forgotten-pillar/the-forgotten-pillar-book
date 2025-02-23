import sys

def modify_text(text: str) -> str:
    """
    Processes the input text and replaces quotes based on context.
    
    Rules:
      - For a double quote ("):
          * If the previous character is not a letter (or there is none), replace with opening quote “.
          * Else if the next character is not a letter (or there is none), replace with closing quote ”.
          * Otherwise, leave it unchanged.
      - For a single quote ('):
          * If the previous character is not a letter (or there is none), replace with opening quote ‘.
          * Else if the next character is not a letter (or there is none), replace with closing quote ’.
          * Otherwise, leave it unchanged.
    """
    new_chars = []
    for i, ch in enumerate(text):
        if ch == '“':
            new_chars.append('"')
        elif ch == '”':
            new_chars.append('"')
        elif ch == '‘':
            new_chars.append('\'')
        elif ch == '’':
            new_chars.append('\'')
        else:
            new_chars.append(ch)
    
    return ''.join(new_chars)

def main():
    # Ensure that the script is called with one argument: the file path
    if len(sys.argv) != 2:
        print("Usage: python script.py input_file.tex")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    # Read the content from the file
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Modify the text using our function
    modified_content = modify_text(content)
    
    # Write the modified content back to the same file
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(modified_content)
    
    print("File has been updated.")

if __name__ == "__main__":
    main()