# The Forgotten Pillar Book Project

## Project Overview

A flexible LaTeX project for the Forgotten Pillar Book designed to support multiple languages and layouts with ease. This repository provides a comprehensive framework for book production, translation, and distribution.

## Features

### Flexible Layouts
The project supports 7 different layout variants:
1. Book Print (`book-print`)
2. ISO A4 (`iso-a4`)
3. ISO A5 (`iso-a5`)
4. Mobile Format (`mobile`)
5. US Letter (`us-letter`)
6. US Letter Half (`us-letter-half`)
7. EPUB Converter (`epub`)

### Multi-Language Support
- Currently supports languages: English (en), Croatian (hr), Polish (pl), French (fr), Swahili (sw), Spanish (es), Arabic (ar)
- Easy language switching through configuration

## Prerequisites

### LaTeX Requirements
- TeXLive (recommended) or MacTeX
- `tex4ebook` for EPUB conversion
- `latexmk` for PDF compilation
- LaTeX Workshp VS extension (optional)

### Python Scripts Requirements
- Python 3.8+
- `anthropic` library
- `pyyaml`
- `python-dotenv`
- A Claude AI API key for translation scripts

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/your-organization/forgotten-pillar.git
cd forgotten-pillar
```

### 2. Install LaTeX Dependencies
- Install TeXLive from [https://tug.org/texlive/](https://tug.org/texlive/)
- Ensure `tex4ebook` is installed (usually part of TeXLive)

### 3. Install Python Dependencies
```bash
pip install anthropic pyyaml python-dotenv
```

## Configuration and Usage

### Changing Language and Layout
In `main.tex`, you can easily switch language and layout:

```latex
\def\currentlang{en}     % Language code
\def\currentlayout{book-print}  % Layout variant
```

### PDF Compilation
```bash
latexmk main.tex  # Compile PDF
```

### EPUB Conversion
```bash
tex4ebook -B epub/output -d epub -c epub/config.cfg main.tex
```

## Translation Workflow

### Automatic Translation
Use the provided Python scripts in the `scripts/` directory to:
- Create Overleaf projects
- Translate chapters using AI
- Manage translation suggestions

### Translation Script Usage
```bash
# Translate a chapter to a specific language
python scripts/translation.py pl chapter01.tex
```

## Project Structure
- `lang/`: Language-specific content
- `latex-setup/`: LaTeX configuration and styles
- `scripts/`: Utility scripts for project management
- `images/`: Project images and graphics
- `epub/`: EPUB conversion configuration

## Contribution Guidelines
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push and create a pull request

## License
[Specify your project's license]

## Contact
Michael Presecan
- Website: [forgottenpillar.com](https://forgottenpillar.com)
- GitHub: [@forgotten-pillar](https://github.com/forgotten-pillar)

## Notes
- Ensure you have an active Claude AI API key for translation scripts
- Always test compilations in different layouts and languages