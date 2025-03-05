import requests
import sys
import os
import re

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

def fix_egw_links(chapter_content, update_links_manual):
    """
    Find and replace EGW Writings links with 'ref' to 'read' URLs.
    
    Args:
        chapter_content (str): Content of the LaTeX file
        update_links_manual (str): Name of the chapter file which will be used to log links without 'para' parameter
    
    Returns:
        tuple: Updated content and number of links updated
    """
    # Regex to find full EGW Writings URLs with 'ref' and optional 'para' parameters, 
    # within square brackets and including LaTeX escaped versions
    egw_link_pattern = r'\[((https://egwwritings\.org/\?ref=[^&\s\)"\]]+)(&para=[^&\s\)"\]]+)?)\]'
    
    # Counter for updated links
    links_updated = 0
    
    # Clear previous log file
    open(update_links_manual, 'w').close()
    
    def replace_link(match):
        nonlocal links_updated
        full_match = match.group(0)  # Entire match including brackets
        original_url = match.group(1)  # URL without brackets
        ref_url = match.group(2)  # URL with ref parameter
        para_param = match.group(3)  # Optional para parameter
        
        # Unescape the URL
        unescaped_url = unescape_latex_url(ref_url)
        
        try:
            # If no para parameter, log the link
            if not para_param:
                with open(update_links_manual, 'a') as log_file:
                    log_file.write(f"{original_url}\n")
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

    # Read the chapter file
    chapter_content = read_latex_file(chapter_file)

    # Build the output directory path.
    links_dir = os.path.join(root_dir, "lang", target_lang_code, "links")
    setup_directories(links_dir)
    update_links_manual = os.path.join(links_dir, chapter_filename)

    # Fix EGW links
    updated_content, num_links_updated = fix_egw_links(chapter_content, update_links_manual)

    # Write the updated content back to the same file
    write_latex_file(chapter_file, updated_content)
    
    # Print the number of links updated
    print(f"Successfully processed links in {chapter_filename}")
    print(f"Total links updated: {num_links_updated}")
    print(f"Links without 'para' parameter logged in: {chapter_filename}_links_without_para.log")

if __name__ == "__main__":
    main()