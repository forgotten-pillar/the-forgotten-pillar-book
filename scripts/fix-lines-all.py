import os
import re
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def read_latex_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def fix_latex_lines(content):
    """
    Fix line spacing in LaTeX content.
    - Replace multiple consecutive empty lines with a single empty line
    - Preserve cases where there are no empty lines or just one empty line
    """
    # Replace multiple consecutive empty lines with a single empty line
    # This regex matches 2 or more consecutive newlines and replaces them with exactly 2 newlines
    # (which represents 1 empty line between content)
    fixed_content = re.sub(r'\n{3,}', '\n\n', content)
    
    return fixed_content

def process_latex_file(input_file):
    content = read_latex_file(input_file)
    fixed_content = fix_latex_lines(content)

    with open(input_file, 'w', encoding='utf-8') as f:
        f.write(fixed_content)

def main():
    # Ensure exactly one argument: the target language code
    if len(sys.argv) != 2:
        sys.exit("Usage: python fix-lines-all.py <target_lang_code>")

    # Get the target language code
    target_lang_code = sys.argv[1]

    # Determine root directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.abspath(os.path.join(script_dir, ".."))

    # Define input directory
    input_dir = os.path.join(root_dir, "lang", target_lang_code, "chapters")
    
    # Validate input directory
    if not os.path.exists(input_dir):
        sys.exit(f"Error: Input directory '{input_dir}' does not exist.")
    
    # Get all .tex files
    files_to_process = sorted([f for f in os.listdir(input_dir) if f.endswith(".tex")])

    total = len(files_to_process)
    if total == 0:
        print("All files are already processed.")
        return

    print(f"Fixing {total} files in '{target_lang_code}'...")

    for i, chapter_file in enumerate(files_to_process, 1):
        input_file = os.path.join(input_dir, chapter_file)

        print(f"[{i}/{total}] Fixing '{chapter_file}'...")
        process_latex_file(input_file)
        print(f"Done: '{chapter_file}'")

    print("Fixing lines complete.")

if __name__ == "__main__":
    main()