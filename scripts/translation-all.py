import os
import re
import yaml
import sys
from anthropic import Anthropic
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ----------------------------
# Utility functions
# ----------------------------

def is_considered_letter(c: str) -> bool:
    """
    Returns True if c is an alphabetic character (using Unicode)
    for our purposes. For our logic, we want to treat the LaTeX 
    brace characters '{' and '}' as nonalphabetic.
    """
    if c in "{}":
        return False
    return c.isalpha()

def fix_quotation_marks(text: str) -> str:
    """
    Check fix-quotations.py 'modify_text' for the original function.
    """
    result = []
    for i, ch in enumerate(text):
        if ch in "\"'":
            prev = text[i-1] if i > 0 else None
            nxt = text[i+1] if i < len(text)-1 else None

            if ch == "'":
                # If it's an apostrophe in a contraction, leave it unchanged.
                if prev is not None and nxt is not None and is_considered_letter(prev) and is_considered_letter(nxt):
                    result.append("'")
                    continue

            # Determine opening vs. closing:
            # If previous character is missing or nonalphabetic, assume opening.
            if prev is None or prev.isspace() or (not prev.isalpha() and prev not in '{}' and prev not in '.,?!:;') or prev == '{':
                if ch == '"':
                    result.append('“')
                else:
                    result.append('‘')
            # Otherwise, if next character is missing or nonalphabetic, assume closing.
            elif nxt is None or nxt.isspace() or not is_considered_letter(nxt):
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

def get_config_value(yaml_path, value_name):
    if not yaml_path:
        sys.exit("Error: No YAML configuration file path provided.")
    if not os.path.exists(yaml_path):
        sys.exit(f"Error: YAML configuration file '{yaml_path}' does not exist.")
    try:
        with open(yaml_path, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
    except Exception as e:
        sys.exit(f"Error: Failed to load YAML file: {e}")
    if not config or value_name not in config:
        sys.exit(f"Error: '{value_name}' variable is missing in the YAML file.")
    return config[value_name]

def generate_system_prompt(yaml_path):
    language = get_config_value(yaml_path, "language")
    translation_mapping = get_config_value(yaml_path, "translation_mapping")
    bible_verse_translation = get_config_value(yaml_path, "bible_verse_translation")

    mapping_lines = []
    for src, tgt in translation_mapping.items():
        mapping_lines.append(f'   - "{src}" → "{tgt}"')
    mapping_text = "\n".join(mapping_lines)

    system_prompt = f"""You are a specialized translation assistant tasked with translating text to {language}.
Your output must be only the translated text—do not include any extra meta information or introductory phrases (e.g., "Here's the {language} translation..."). Output clean translation, please.

Key rules to follow:
1. **Preservation of LaTeX and Mathematics:**
   - ALWAYS, preserve all LaTeX commands and any mathematics unchanged. All LaTeX commands present in the source English text should also appear correspondingly in {language}. All LaTeX commands, including \\textbf{{}} \\textit{{}} \\underline{{}} \\emcap{{}} \\footnote{{}} \\egw{{}}[][] \\egwnogap{{}}[][] \\egwinline{{}}[][] \\others{{}}[][] \\othersnogap{{}}[][] \\othersQuote{{}}[][] \\othersQuoteNoGap{{}}[][] \\normalText{{}}[][] \\bible{{}}[] should be preserved fully, and if optional text in [] is translatable, translate it too.
   - Be very careful about the scope of commands delimited by curly brackets. Every command that starts with a curly bracket must finish with a corresponding one.
   - Commands like `\\egw` refer to Ellen G. White; when such commands appear, translate the surrounding text with feminine grammatical forms if required. Commands like `\\others` should be translated with male grammatical forms if not otherwise indicated.

2. **Specific Translation Mappings:**
   Use the following phrase mappings exactly as specified:
{mapping_text}

3. **Bible Verse Translations:**
   - For every Bible verse encountered, use "{bible_verse_translation}" Bible translation.

Follow these instructions carefully to ensure that the translation is accurate and free of any extraneous commentary."""
    return system_prompt

def setup_directories(output_dir):
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

def read_latex_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def split_into_paragraphs(content):
    paragraphs = re.split(r'\n\s*\n', content)
    return [p.strip() for p in paragraphs if p.strip()]

def is_structural_latex_command(paragraph):
    # Only treat as non-translatable if the paragraph is solely a structural command.
    structural_commands = ["\\input"]
    stripped = paragraph.strip()
    return any(stripped.startswith(cmd) for cmd in structural_commands)

def translate_paragraph_batch(client, paragraphs, target_lang, system_message):
    delimiter = "===SPLIT==="
    joined_paragraphs = f"\n{delimiter}\n".join(paragraphs)
    prompt = f"""Translate the following paragraphs to {target_lang}. Preserve all LaTeX commands and mathematics unchanged. Return exactly {len(paragraphs)} translated paragraphs in the same order as the input, separated by the delimiter '{delimiter}'. The LaTeX directives must be preserved fully in its corresponding translation! Do not add any extra commentary or numbering.

Input paragraphs:
{joined_paragraphs}

Translated paragraphs:"""

    message = client.messages.create(
        model="claude-3-7-sonnet-20250219",
        max_tokens=8192,
        temperature=0,
        system=system_message,
        messages=[{"role": "user", "content": prompt}]
    )

    translation_response = message.content
    if isinstance(translation_response, list) and translation_response:
        translation_response = translation_response[0]
    if hasattr(translation_response, 'text'):
        translation_response = translation_response.text

    translated_paragraphs = [part.strip() for part in translation_response.split(delimiter) if part.strip()]
    if len(translated_paragraphs) != len(paragraphs):
        print("Warning: The number of translated paragraphs does not match the input count.")
    return translated_paragraphs

def process_latex_file(input_file, output_dir, client):
    content = read_latex_file(input_file)
    output_file = os.path.join(output_dir, os.path.basename(input_file))
    # Assume config.yaml is in the target language directory (i.e. one level up from output_dir)
    system_prompt_config_file = os.path.join(os.path.dirname(output_dir), "config.yaml")
    system_prompt = generate_system_prompt(system_prompt_config_file)
    target_lang = get_config_value(system_prompt_config_file, "language")
    print(f"System prompt: {system_prompt}")

    paragraphs = split_into_paragraphs(content)
    translated_content = []
    batch = []
    batch_orig = []
    batch_size = 10

    def flush_batch():
        nonlocal batch, batch_orig, translated_content
        if batch:
            print(f"Translating a batch of {len(batch)} paragraphs...")
            translations = translate_paragraph_batch(client, batch, target_lang, system_prompt)
            for orig, trans in zip(batch_orig, translations):
                translated_content.append(orig + "\n")
                translated_content.append(trans + "\n")
            batch.clear()
            batch_orig.clear()

    for paragraph in paragraphs:
        if not paragraph.strip():
            continue
        if is_structural_latex_command(paragraph):
            flush_batch()
            translated_content.append(paragraph)
        else:
            batch.append(paragraph)
            batch_orig.append(paragraph)
            if len(batch) == batch_size:
                flush_batch()
    flush_batch()

    translated_content = [fix_quotation_marks(p) for p in translated_content]

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n\n'.join(translated_content))

def main():
    # Ensure exactly one argument: the target language code
    if len(sys.argv) != 2:
        sys.exit("Usage: python translation.py <target_lang_code>")

    # Get the target language code
    target_lang_code = sys.argv[1]

    # Determine root directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.abspath(os.path.join(script_dir, ".."))

    # Define input/output directories
    input_dir = os.path.join(root_dir, "lang", "en", "chapters")
    output_dir = os.path.join(root_dir, "lang", target_lang_code, "chapters")
    config_file = os.path.join(root_dir, "lang", target_lang_code, "config.yaml")

    # Validate input directory
    if not os.path.exists(input_dir):
        sys.exit(f"Error: Input directory '{input_dir}' does not exist.")
    
    # Validate config file
    if not os.path.exists(config_file):
        sys.exit(f"Error: Config file '{config_file}' does not exist.")
    
    setup_directories(output_dir)

    # Get all .tex files
    all_files = sorted([f for f in os.listdir(input_dir) if f.endswith(".tex")])
    files_to_translate = [f for f in all_files if not os.path.exists(os.path.join(output_dir, f))]

    total = len(files_to_translate)
    if total == 0:
        print("All files are already translated.")
        return

    # Get the API key from the environment
    claude_api_key = os.environ.get("CLAUDE_API_KEY")
    if not claude_api_key:
        sys.exit("Error: CLAUDE_API_KEY not set in .env file.")

    # Initialize Anthropic client
    client = Anthropic(api_key=claude_api_key)

    print(f"Translating {total} files to '{target_lang_code}'...")

    for i, chapter_file in enumerate(files_to_translate, 1):
        input_file = os.path.join(input_dir, chapter_file)
        output_file = os.path.join(output_dir, chapter_file)

        if os.path.exists(output_file):
            print(f"Skipping '{chapter_file}' (already translated).")
            continue
        
        print(f"[{i}/{total}] Translating '{chapter_file}'...")
        process_latex_file(input_file, output_dir, client)
        print(f"Done: '{chapter_file}'")

    print("Translation complete.")

if __name__ == "__main__":
    main()