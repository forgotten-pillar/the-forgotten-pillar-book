import sys
import os
import yaml
from anthropic import Anthropic

def fix_grammar(prompt, client):

    message = client.messages.create(
        model="claude-3-7-sonnet-20250219",
        max_tokens=8192,
        temperature=0,
        messages=[{"role": "user", "content": prompt}]
    )

    grammar_list = message.content
    if isinstance(grammar_list, list) and grammar_list:
        grammar_list = grammar_list[0]
    if hasattr(grammar_list, 'text'):
        grammar_list = grammar_list.text

    return grammar_list

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

def generate_prompt(language, content):
    prompt = f"""You are a grammar assistant tasked with examining {language} text.
    For given {language} text, fix grammar, if there are any grammar mistakes.
    The text given is LaTeX-formatted text.

    Key rules to follow:
    1. **Ignore the following LaTeX directives**
    \\egw{{}}[][], \\egwnogap{{}}[][], \\othersnogap{{}}[][], \\othersQuote{{}}[][], \\othersQuoteNoGap{{}}[][], \\normalText{{}}[][], \\bible{{}}[]
    These directives represent quotations, so they are not something which needs to be fixed.

    2. **OUTPUT FORMAT**
    Plear output fixes as a list in the following format for an item:
    ```
    # [explain the change made]
    [old expression/sentence] 
    ->
    [new expression/sentence]
    ---------
    ```
    For example:
    ```
    # Removed word 'that'
    ["This great \\underline{{disappointment can be compared}} to the one that Jesus' disciples had"]
    ->
    ["This great \\underline{{disappointment can be compared}} to the one Jesus' disciples had"]
    ---------
    
    In the list, always preserve LaTeX formatting (e.g. \\underline{{}}, \\texfbf{{}}, \\textit{{}}, \\emcap{{}}) and do not change it.

    Do not include any additional formatting, numbering, or separators between items.

    Text to correct:
    {content}
    """
    return prompt

def setup_directories(output_dir):
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

def read_latex_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def process_latex_file(input_file, output_dir, client):
    content = read_latex_file(input_file)
    output_file = os.path.join(output_dir, os.path.basename(input_file))
    # Assume config.yaml is in the target language directory (i.e. one level up from output_dir)
    system_prompt_config_file = os.path.join(os.path.dirname(output_dir), "config.yaml")
    target_lang = get_config_value(system_prompt_config_file, "language")
    prompt = generate_prompt(target_lang, content)
    print(f"System prompt: {prompt}")

    grammar_list = fix_grammar(prompt, client)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(grammar_list)

def main():
     # Ensure the correct number of command-line arguments: 
    # either 2 arguments (target_lang_code and chapter file) OR
    # 3 arguments (with the third being "overwrite")
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python translation.py <target_lang_code> <chapter_file.tex> [overwrite]")
    
    # Get command-line arguments.
    target_lang_code = sys.argv[1]
    chapter_file = sys.argv[2]
    overwrite = False
    if len(sys.argv) == 4:
        if sys.argv[3].lower() == "overwrite":
            overwrite = True
        else:
            sys.exit("Usage: python translation.py <target_lang_code> <chapter_file.tex> [overwrite]")
    
    # Determine the root directory (parent of the 'scripts' folder)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.abspath(os.path.join(script_dir, ".."))

    input_file = os.path.join(root_dir, "lang", target_lang_code, "chapters", chapter_file)
    if not os.path.exists(input_file):
        sys.exit(f"Error: Chapter file '{input_file}' does not exist.")

    # Build the output directory path.
    output_dir = os.path.join(root_dir, "lang", target_lang_code, "grammar")
    setup_directories(output_dir)

    # Check if the output file already exists.
    output_file = os.path.join(output_dir, chapter_file)
    if os.path.exists(output_file) and not overwrite:
        sys.exit(f"Error: Output file '{output_file}' already exists. To overwrite, run the script with the 'overwrite' parameter.")

    # Get the API key from the environment (.env file).
    claude_api_key = os.environ.get("CLAUDE_API_KEY")
    if not claude_api_key:
        sys.exit("Error: CLAUDE_API_KEY not set in .env file.")

    # Initialize Anthropic client.
    client = Anthropic(api_key=claude_api_key)

    print(f"Processing '{input_file}' for target language '{target_lang_code}'...")
    process_latex_file(input_file, output_dir, client)
    print(f"Completed translation of '{input_file}'. Output stored in '{output_dir}'.")

if __name__ == "__main__":
    main()