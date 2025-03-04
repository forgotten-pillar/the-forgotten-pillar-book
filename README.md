## Tranlsation Script
Run command:
```
python scripts/trasnlation.py [target-lang] [chapter.tex]
```

In example: `python scripts/translation.py es chapter30.tex` will translate chapter 30 from English to Spanish, and will store it to `lang/es/chapters/chapter30.tex`.

- if the given chapter already exists, it will prevent overwriting, unless the third optional parameter `overwrite` is submitted.

## Translation with suggestions Script
Translation with suggestions is useful for already translated content from the first edition of the book. The AI would consult the suggestions within the translation and it will follow it, unless there is discrepency with the translation and the original English text.

Run command:

```
python scripts/translate-by-suggestions.py [target-lang] [chapter.tex]
```
- There must be suggestions in your `/lang/[target-lang]/suggestions/[chapter.txt]` with `*.txt` extension. If non existant, then the script will bail out.
- if the given chapter already exists, it will prevent overwriting, unless the third optional parameter `overwrite` is submitted.

## Fix quotation Script
Claude does not respect opening and closing quotation marks, instead it outputs universal quotation marks. Those do not look good with Garammond font, so the quotation marks should be changed. This is a very tideous manual process, but luckily this script will fix it automatically.

Run command:

```
python scripts/fix-quotations.py /lang/[target-lang]/chapters/[chpater.tex]
```
In case that the quotation marks should be reversed run:
```
python scripts/fix-quotations-back.py /lang/[target-lang]/chapters/[chapter.tex]
```

## Fix grammar Script
When translated, there is a grammar checker which will find possible grammar mistakes in the translation.

Run command:
```
python scripts/fix-grammar.py [target-lang] [chapter.tex]
```
- if the given grammar suggestion for the given chapter already exists, it will prevent overwriting, unless the third optional parameter `overwrite` is submitted.

## Create Overleaf Project
There is a free LaTeX setup - ![overleaf.com](https://overleaf.com). There is a script which prepares entire project for OverLeaf for the given language

Run command:
```
python scripts/create-overleaf-project.py [target-lang]
```
- this will outout zip file which can be imported in overleaf