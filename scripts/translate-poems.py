import os
import yaml
import sys
from anthropic import Anthropic
from pathlib import Path
from dotenv import load_dotenv

def translate_poem_dummy(prompt, client):
    return prompt

def translate_poem(prompt, client):
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=8192,
        temperature=0,
        messages=[{"role": "user", "content": prompt}]
    )

    translated_poem = message.content
    if isinstance(translated_poem, list) and translated_poem:
        translated_poem = translated_poem[0]
    if hasattr(translated_poem, 'text'):
        translated_poem = translated_poem.text

    return translated_poem

def generate_prompt(chapter_file, english_poem, target_lang, number_of_poems):
    return f"""
    Please write me {number_of_poems} {"different" if number_of_poems > 1 else ""} short poem{"s" if number_of_poems > 1 else ""} based on the provided text in {target_lang} language. The rhyme should be in pares one after another (AABB form), not intemixed. The poem has to be concise drawing the main point from the given text. Notice, God's nature and the personality of God are not one and the same thing. Here is the LaTeX text, by which you can make a poem (notice \\egw{{}}[][] and \\egwnogap{{}}[][] and \\egwinline{{}}[][] are quotations of Ellen White):

    Text:
    {chapter_file}
    ---
    Please output the poem in the LaTeX format as an example shown below:

    {english_poem}

    ---
    Remember rhyme should be in AABB form. Poems should be in {target_lang} language.
    {"You can write multiple poems one after another." if number_of_poems > 1 else ""}
    THE RYME SHOULD BE IN THE SPIRIT OF {target_lang.upper()} LANGUAGE.
    """

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

def process_latex_file(chapter_file, english_poem, output_dir, client, chapter, target_lang_code, number_of_poems):
    chapter_content = read_latex_file(chapter_file)
    english_poem_content = read_latex_file(english_poem)
    output_file = os.path.join(output_dir, os.path.basename(chapter_file))
    # Assume config.yaml is in the target language directory (i.e. one level up from output_dir)
    system_prompt_config_file = os.path.join(os.path.dirname(output_dir), "config.yaml")
    target_lang = get_config_value(system_prompt_config_file, "language")
    prompt = generate_prompt(chapter_content, english_poem_content, target_lang, number_of_poems)
    
    print(f"Prompt: {prompt}")

    translated_poem = translate_poem(prompt, client)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(translated_poem)

    # Check if \input{lang/target_lang_code} exists in chapter_content
    if rf"\input{{lang/{target_lang_code}/poems/{chapter}}}" not in chapter_content and rf"\input{{lang/{target_lang_code}/poems/{chapter.replace('.tex', '')}}}" not in chapter_content:
        new_content = chapter_content.strip() + "\n\n" + rf"\input{{lang/{target_lang_code}/poems/{chapter.replace('.tex', '')}}}"

        # Save the updated content back to chapter_file
        with open(chapter_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
    

def setup_directories(output_dir):
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

def read_latex_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def main():
    # Ensure the correct number of command-line arguments: 
    # either 2 arguments (target_lang_code and chapter file) OR
    # 3 arguments (with the third being "overwrite")
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python translate-poems.py <target_lang_code> <chapter_file.tex> [overwrite]")
    
    # Get command-line arguments.
    target_lang_code = sys.argv[1]
    chapter = sys.argv[2]
    overwrite = False
    number_of_poems = 1
    if len(sys.argv) == 4:
        if sys.argv[3].lower() == "overwrite":
            overwrite = True
        elif sys.argv[3].isdigit():
            number_of_poems = int(sys.argv[3])
            overwrite = True
        else:
            sys.exit("Usage: python translate-poems.py <target_lang_code> <chapter_file.tex> [overwrite]")
    
    # Determine the root directory (parent of the 'scripts' folder)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.abspath(os.path.join(script_dir, ".."))
    
    # Build the input file path.
    chapter_file = os.path.join(root_dir, "lang", target_lang_code, "chapters", chapter)
    if not os.path.exists(chapter_file):
        sys.exit(f"Error: Chapter file '{chapter_file}' does not exist.")

    english_poem = os.path.join(root_dir, "lang", "en", "poems", chapter)
    if not os.path.exists(english_poem):
        sys.exit(f"Error: English poem '{chapter_file}' does not exist.")

    # Check config script
    config_file = os.path.join(root_dir, "lang", target_lang_code, "config.yaml")
    if not os.path.exists(config_file):
        sys.exit(f"Error: Config file '{config_file}' does not exist.")

    # Build the output directory path.
    output_dir = os.path.join(root_dir, "lang", target_lang_code, "poems")
    setup_directories(output_dir)
    
    # Check if the output file already exists.
    output_file = os.path.join(output_dir, chapter)
    
    if os.path.exists(output_file) and not overwrite:
        sys.exit(f"Error: Output file '{output_file}' already exists. To overwrite, run the script with the 'overwrite' parameter.")

    # Get the API key from the environment (.env file).
    claude_api_key = os.environ.get("CLAUDE_API_KEY")
    if not claude_api_key:
        sys.exit("Error: CLAUDE_API_KEY not set in .env file.")

    # Initialize Anthropic client.
    client = Anthropic(api_key=claude_api_key)

    print(f"Processing '{chapter_file}' for target language '{target_lang_code}'...")
    process_latex_file(chapter_file, english_poem, output_dir, client, chapter, target_lang_code, number_of_poems)
    print(f"Completed translation of '{chapter_file}'. Output stored in '{output_dir}'.")

if __name__ == "__main__":
    main()