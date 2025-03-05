import requests
import sys
import os
import re
import yaml

def setup_directories(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        return output_dir

def get_redirected_url(original_url):
    """
    Get the redirected URL for EGW Writings links.
    
    Args:
        original_url (str): The original URL with 'ref' parameter
    
    Returns:
        str: The redirected URL with 'read' parameter
    
    Raises:
        requests.RequestException: If there's an error during the request
    """
    try:
        # Send a GET request, allowing redirects
        response = requests.get(original_url, allow_redirects=True)
        
        # Return the final URL after any redirects
        return response.url
    
    except requests.RequestException as e:
        print(f"An error occurred: {e}")
        return None

def read_latex_file(file_path):
    """
    Read the contents of a LaTeX file.
    
    Args:
        file_path (str): Path to the LaTeX file
    
    Returns:
        str: Contents of the file
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def write_latex_file(file_path, content):
    """
    Write content to a LaTeX file.
    
    Args:
        file_path (str): Path to the LaTeX file
        content (str): Content to write to the file
    """
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)

def unescape_latex_url(escaped_url):
    """
    Unescape LaTeX URL by removing unnecessary backslashes.
    
    Args:
        escaped_url (str): URL with LaTeX escape characters
    
    Returns:
        str: Unescaped URL
    """
    # Remove escaped underscores within the URL
    return escaped_url.replace(r'\_', '_')

def load_yaml_links(yaml_path):
    """
    Load links from a YAML file.
    
    Args:
        yaml_path (str): Path to the YAML file
    
    Returns:
        dict: Dictionary of links from YAML
    """
    try:
        with open(yaml_path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file) or {}
    except FileNotFoundError:
        print(f"Warning: YAML file not found at {yaml_path}")
        return {}
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file: {e}")
        return {}

def fix_egw_links(chapter_content, yaml_links):
    """
    Find and replace EGW Writings links with 'ref' to 'read' URLs.
    
    Args:
        chapter_content (str): Content of the LaTeX file
        yaml_links (dict): Manually mapped links from YAML
    
    Returns:
        tuple: Updated content and number of links updated
    """
    # Regex to find full EGW Writings URLs with 'ref' and optional 'para' parameters, 
    # within square brackets and including LaTeX escaped versions
    egw_link_pattern = r'\[((https://egwwritings\.org/\?ref=[^&\s\)"\]]+)(&para=[^&\s\)"\]]+)?)\]'
    
    # Counter for updated links
    links_updated = 0
    missing_links = []
    
    def replace_link(match):
        nonlocal links_updated, missing_links
        full_match = match.group(0)  # Entire match including brackets
        original_url = match.group(1)  # URL without brackets
        ref_url = match.group(2)  # URL with ref parameter
        para_param = match.group(3)  # Optional para parameter
        
        # Unescape the URL
        unescaped_url = unescape_latex_url(ref_url)
        
        try:
            # First, check if the link exists in the YAML mapping
            if unescaped_url in yaml_links:
                # If the link is in the YAML, use the mapped URL
                new_url = yaml_links[unescaped_url]
                
                # If the original had escaped underscores, re-escape the new URL
                if '\_' in original_url:
                    new_url = new_url.replace('_', r'\_')
                
                links_updated += 1
                print(f"Mapped: {original_url} -> {new_url}")
                return f'[{new_url}]'
            
            # If no para parameter, log as a missing link
            if not para_param:
                missing_links.append(original_url)
                return full_match
            
            # Get the redirected URL
            redirected_url = get_redirected_url(unescaped_url + para_param)
            
            # If redirection successful, return the new URL
            if redirected_url:
                # Compare unescaped URLs
                if unescape_latex_url(original_url) != redirected_url:
                    links_updated += 1
                    print(f"Replaced: {original_url} -> {redirected_url}")
                    
                    # Check if we need to re-escape for LaTeX
                    if '\_' in original_url:
                        redirected_url = redirected_url.replace('_', r'\_')
                    
                    # Return the new URL within brackets
                    return f'[{redirected_url}]'
            
            # If no redirection or URLs are the same, return original full match
            return full_match
        
        except Exception as e:
            print(f"Error processing URL {original_url}: {e}")
            return full_match
    
    # Replace all matching URLs
    updated_content = re.sub(egw_link_pattern, replace_link, chapter_content)
    
    # Print out any missing links
    if missing_links:
        print("\nWARNING: The following links were not found in the YAML mapping and lacked 'para' parameter:")
        for link in missing_links:
            print(link)
    
    return updated_content, links_updated

def main():
    # Check for correct number of arguments
    if len(sys.argv) < 3:
        sys.exit("Usage: python fix-links.py <target_Lang_code> <chapter_file.tex>")

    # Get command-line arguments
    target_lang_code = sys.argv[1]
    chapter_filename = sys.argv[2]

    # Determine the root directory (parent of the 'scripts' folder)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.abspath(os.path.join(script_dir, ".."))
        
    # Build the chapter file path using the target language code
    chapter_file = os.path.join(root_dir, "lang", target_lang_code, "chapters", chapter_filename)
    if not os.path.exists(chapter_file):
        sys.exit(f"Error: Chapter file '{chapter_file}' does not exist.")
    
    # Path to links.yaml file (assumed to be in the same directory as the script)
    links_yaml_path = os.path.join(script_dir, "links.yaml")
    
    # Load links from YAML
    yaml_links = load_yaml_links(links_yaml_path)

    # Read the chapter file
    chapter_content = read_latex_file(chapter_file)

    # Fix EGW links
    updated_content, num_links_updated = fix_egw_links(chapter_content, yaml_links)

    # Write the updated content back to the same file
    write_latex_file(chapter_file, updated_content)
    
    # Print the number of links updated
    print(f"Successfully processed links in {chapter_filename}")
    print(f"Total links updated: {num_links_updated}")

if __name__ == "__main__":
    main()