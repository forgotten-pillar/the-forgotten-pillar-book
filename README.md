## Translation Script
Run command:

```
python scripts/translation.py [target-lang] [chapter.tex]
```
For example, running `python scripts/translation.py es chapter30.tex` will translate chapter 30 from English to Spanish and store it in `lang/es/chapters/chapter30.tex`.

- If the given chapter already exists, the script will prevent overwriting unless the third optional parameter `overwrite` is provided.

## Translation with Suggestions Script
Translation with suggestions is useful for already translated content from the first edition of the book. The AI will consult the provided suggestions within the translation and follow them unless there is a discrepancy between the translation and the original English text.

Run command:
```
python scripts/translate-by-suggestions.py [target-lang] [chapter.tex]
```
- Suggestions must exist in `/lang/[target-lang]/suggestions/[chapter.txt]` with a `.txt` extension. If no suggestions are found, the script will exit.
- If the given chapter already exists, the script will prevent overwriting unless the third optional parameter `overwrite` is provided.

## Fix Quotation Script
Claude does not respect opening and closing quotation marks, instead outputting universal quotation marks. These do not look good with the Garamond font, so the quotation marks should be replaced. This is a very tedious manual process, but this script automates the correction.

Run command:
```
python scripts/fix-quotations.py /lang/[target-lang]/chapters/[chapter.tex]
```
If the quotation marks need to be reversed, run:
```
python scripts/fix-quotations-back.py /lang/[target-lang]/chapters/[chapter.tex]
```
## Fix Grammar Script
When a translation is completed, a grammar checker runs to detect possible grammar mistakes.

Run command:
```
python scripts/fix-grammar.py [target-lang] [chapter.tex]
```
- If grammar suggestions for the given chapter already exist, the script will prevent overwriting unless the third optional parameter `overwrite` is provided.

## Create Overleaf Project
There is a free LaTeX setup available at [Overleaf](https://overleaf.com). A script is available to prepare an entire project for Overleaf in the given language.

Run command:
```
python scripts/create-overleaf-project.py [target-lang]
```
- This will output a ZIP file that can be imported into Overleaf.