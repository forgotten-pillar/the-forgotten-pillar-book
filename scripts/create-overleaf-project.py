#!/usr/bin/env python3
import os
import sys
import re
import zipfile
import argparse

def main():
    # Set up argument parsing; default language is 'en'
    parser = argparse.ArgumentParser(description="Create an Overleaf project zip file")
    parser.add_argument('language', nargs='?', default='en', help="Language code (default: en)")
    args = parser.parse_args()

    lang = args.language.lower()
    lang_folder = os.path.join('lang', lang)
    
    # Check if the language folder exists
    if not os.path.isdir(lang_folder):
        print(f"Error: The language folder '{lang_folder}' does not exist.")
        sys.exit(1)

    # Name the zip file using the language code in uppercase
    zip_filename = f"The Forgotten Pillar Book {lang.upper()}.zip"

    # Create the zip file and add required folders and modified main.tex
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # List of folders to include in the zip
        folders_to_include = [
            'images',
            lang_folder,
            'latex-setup'
        ]
        
        for folder in folders_to_include:
            if os.path.isdir(folder):
                for root, _, files in os.walk(folder):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # Preserve the directory structure relative to the project root
                        arcname = os.path.relpath(file_path, '.')
                        zipf.write(file_path, arcname)
            else:
                print(f"Warning: Folder '{folder}' not found. Skipping it.")

        # Process main.tex: read, modify, and add to the zip
        main_tex_path = 'main.tex'
        if os.path.isfile(main_tex_path):
            with open(main_tex_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            import re

            # Replace \def\currentlang{*} with \def\currentlang{[lang]}
            pattern = r'\\def\\currentlang\{[^}]+\}'
            replaced_content = re.sub(pattern, r'\\def\\currentlang{' + lang + '}', content)
            
            # Write the modified main.tex directly into the zip
            zipf.writestr('main.tex', replaced_content)
        else:
            print("Warning: 'main.tex' not found. It will not be included in the zip.")

    print(f"Created Overleaf project zip: {zip_filename}")

if __name__ == '__main__':
    main()