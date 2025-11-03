import sys
import os
from anthropic import Anthropic

def setup_directories(output_dir):
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

def read_latex_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()
    
def find_suggestions(prompt, client):
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=8192,
        temperature=0,
        messages=[{"role": "user", "content": prompt}]
    )

    image_suggestions = message.content
    if isinstance(image_suggestions, list) and image_suggestions:
        image_suggestions = image_suggestions[0]
    if hasattr(image_suggestions, 'text'):
        image_suggestions = image_suggestions.text

    return image_suggestions
    
def generate_prompt(content):
    return f"""
    I am looking to add images in my book. This is a book about Adventist History. The source of the images should be from Ellen White Estate. I want to give faces to these historic people.
    In the following is the content of the chapter. Please suggest images, keywords which I can search for the book, based on the content, people and events.

    content:
    {content}
    """

def process_latex_file(input_file, output_dir, client):
    content = read_latex_file(input_file)
    output_file = os.path.join(output_dir, os.path.basename(input_file))

    prompt = generate_prompt(content)
    print(f"System prompt: {prompt}")

    suggestions = find_suggestions(prompt, client)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(suggestions)


def main():
    # Ensure the correct number of command-line arguments: 
    if len(sys.argv) not in [2, 3]:
        sys.exit("Usage: python suggest-images.py <chapter_file.tex> [overwrite]")
    
    chapter_file = sys.argv[1]
    overwrite = False
    if len(sys.argv) == 3:
        if sys.argv[2].lower() == "overwrite":
            overwrite = True
        else:
            sys.exit("Usage: python suggest-images.py <chapter_file.tex> [overwrite]")
    
    # Determine the root directory (parent of the 'scripts' folder)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.abspath(os.path.join(script_dir, ".."))

    # Build the input file path.
    input_file = os.path.join(root_dir, "lang", "en", "chapters", chapter_file)
    if not os.path.exists(input_file):
        sys.exit(f"Error: Chapter file '{input_file}' does not exist.")

    # Build the output directory path.
    output_dir = os.path.join(root_dir, "lang", "en", "image-suggestions")
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

    print(f"Processing '{input_file}' for image suggestions...")
    process_latex_file(input_file, output_dir, client)
    print(f"Completed suggestions of '{input_file}'. Output stored in '{output_dir}'.")

if __name__ == "__main__":
    main()