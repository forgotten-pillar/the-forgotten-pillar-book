import os
import sys
import yaml

def process_links_files(target_lang_code):
    """
    Process all link files in the specified language directory.
    
    Args:
        target_lang_code (str): Target language code
    
    Returns:
        set: Unique links found across all files
    """
    # Determine the root directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.abspath(os.path.join(script_dir, ".."))
    
    # Path to the links directory
    links_dir = os.path.join(root_dir, "lang", target_lang_code, "links")
    
    # Ensure links directory exists
    if not os.path.exists(links_dir):
        print(f"Error: Links directory {links_dir} does not exist.")
        return set()
    
    # Set to store unique links
    unique_links = set()
    
    # Process all files in the links directory
    for filename in os.listdir(links_dir):
        # Skip the final links.yaml file if it exists
        if filename == "links.yaml":
            continue
        
        file_path = os.path.join(links_dir, filename)
        
        # Skip if not a file
        if not os.path.isfile(file_path):
            continue
        
        # Read links from the file
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                links = file.read().splitlines()
                # Remove empty lines and strip whitespace
                links = [link.strip() for link in links if link.strip()]
                unique_links.update(links)
        except Exception as e:
            print(f"Error reading file {filename}: {e}")
    
    return unique_links

def save_links_to_yaml(target_lang_code, unique_links):
    """
    Save unique links to a YAML file with empty tuples.
    
    Args:
        target_lang_code (str): Target language code
        unique_links (set): Set of unique links
    """
    # Determine the root directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.abspath(os.path.join(script_dir, ".."))
    
    # Path to the links.yaml file
    yaml_file_path = os.path.join(root_dir, "lang", target_lang_code, "links", "links.yaml")
    
    # Create a dictionary with links as keys and empty tuples as values
    links_dict = {link: () for link in sorted(unique_links)}
    
    # Write to YAML file
    with open(yaml_file_path, 'w', encoding='utf-8') as file:
        yaml.safe_dump(links_dict, file, default_flow_style=False, sort_keys=False)
    
    print(f"Unique links saved to {yaml_file_path}")
    print(f"Total unique links: {len(unique_links)}")

def main():
    # Check for correct number of arguments
    if len(sys.argv) < 2:
        sys.exit("Usage: python process_links.py <target_lang_code>")

    # Get command-line argument
    target_lang_code = sys.argv[1]

    # Process links files and get unique links
    unique_links = process_links_files(target_lang_code)

    # Save unique links to YAML file
    save_links_to_yaml(target_lang_code, unique_links)

if __name__ == "__main__":
    main()