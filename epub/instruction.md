## Steps to create epub

1. In main.tex define language and for layout choose "print-book"

2. in config.cfg change language path for the cover image

3: Run:

```
tex4ebook -B epub/output -d epub -c epub/config.cfg main.tex
```

## Notice:
- \ccby in copyright should be removed from the epub output. QR code as well. See English version of `copyrightpage.tex`