/**
 * Main entry point:
 *  - Parses the selected text in the Google Doc.
 *  - Shows an alert with the final LaTeX output.
 */
function parserStackBased() {
  var doc = DocumentApp.getActiveDocument();
  var selection = doc.getSelection();
  if (!selection) {
    DocumentApp.getUi().alert("No text is selected.");
    return;
  }

  var rangeElements = selection.getRangeElements();
  var finalOutput = "";

  // Because Google Docs can split user selection into multiple RangeElements,
  // we track a "pendingQuoteLaTeX" in case a quote ended in one chunk but
  // the reference is typed in the next chunk (in normal mode).
  var pendingQuoteLaTeX = "";

  for (var i = 0; i < rangeElements.length; i++) {
    var element = rangeElements[i].getElement();
    if (!element.editAsText) {
      continue; // skip non-text, e.g. images
    }

    var textElement = element.asText();
    var startOffset = rangeElements[i].getStartOffset();
    var endOffset = rangeElements[i].getEndOffsetInclusive();

    // parseTextRun returns an object with {textOutput, pendingQuoteLaTeX}
    var parseResult = parseTextRun(
      textElement,
      startOffset,
      endOffset,
      pendingQuoteLaTeX
    );

    finalOutput += parseResult.textOutput;
    pendingQuoteLaTeX = parseResult.pendingQuoteLaTeX;
  }

  // If there's still a leftover quote at the end (no reference found),
  // finalize it now:
  if (pendingQuoteLaTeX) {
    finalOutput += pendingQuoteLaTeX;
  }

  // Final step: Remove any extra quotes around a single LaTeX command
  // in normal text (e.g. “\egw{something}” => \egw{something}).
  finalOutput = removeQuotesAroundSingleCommand(finalOutput);

  showLatexInDialog(finalOutput);
}


/**
 * parseTextRun():
 *  - Does a single pass (startOffset..endOffset) in the Text.
 *  - Normal mode: track bold/italic/underline via a stack.
 *  - Quote mode: track bold/underline only, ignoring italic (EGW or Others color).
 *  - If a reference is found (in curly braces), attach it as [ref][link].
 *  - If the quote color ends, we store the command as "justEndedQuote",
 *    and see if the reference is typed in normal mode next.
 *
 *  Returns:
 *    {
 *      textOutput: "...",       // The normal text + completed quotes
 *      pendingQuoteLaTeX: "..." // A leftover quote waiting for references in the next run
 *    }
 */
function parseTextRun(textElement, startOffset, endOffset, pendingQuoteLaTeX) {
  var text = textElement.getText();
  var textOutput = "";

  // Normal-mode style stack
  var normalStack = [];
  var prevBoldN = false, prevItalN = false, prevUndN = false;

  // Quote-mode style stack
  var quoteStack = [];
  var prevBoldQ = false, prevUndQ = false;

  // Are we in "quote color" (#82011A, #351C75, #7030A0)?
  var inQuoteMode = false;
  var quoteColorGroup = "";   // "EGW" or "OTHERS"
  var quoteBuffer = "";
  var foundReference = false;
  var foundFootnote = false;  // if parseReference sets isFootnote = true
  var referenceText = "";
  var referenceLink = "";
  var justEndedQuote = "";

  //
  // 1) Attempt to attach a reference to any leftover "pending quote" from prior chunk
  //
  if (pendingQuoteLaTeX) {
    // Try to parse a reference immediately at startOffset
    var refStart = tryParseReferenceAt(textElement, startOffset, endOffset);
    if (refStart.found) {
      // We found a {EGW, ...} or {someRef; link}, so attach it
      pendingQuoteLaTeX = appendReferenceToQuote(
        pendingQuoteLaTeX,
        refStart.refText,
        refStart.refLink
      );
      textOutput += pendingQuoteLaTeX;
      pendingQuoteLaTeX = "";
      startOffset = refStart.nextIndex; // skip past the reference block
    } else {
      // No reference => finalize the pending quote
      textOutput += pendingQuoteLaTeX;
      pendingQuoteLaTeX = "";
    }
  }

  //
  // 2) Main pass: parse from startOffset..endOffset
  //
  var i = startOffset;
  for (; i <= endOffset; i++) {
    var ch = text.charAt(i);
    var curBold = textElement.isBold(i) || false;
    var curItal = textElement.isItalic(i) || false;
    var curUnd  = textElement.isUnderline(i) || false;
    var color   = textElement.getForegroundColor(i) || "";
    var colorNorm = color.replace(/\s/g, "").toUpperCase();

    // Detect if it's EGW color or Others color
    var isEGW = (colorNorm === "#82011A");
    var isOthers = (colorNorm === "#351C75" || colorNorm === "#7030A0");
    var charInQuote = (isEGW || isOthers);

    // A) Normal => Quote
    if (!inQuoteMode && charInQuote) {
      // close normal styles
      while (normalStack.length > 0) {
        normalStack.pop();
        textOutput += "}";
      }
      inQuoteMode = true;
      quoteStack = [];
      quoteBuffer = "";
      quoteColorGroup = isEGW ? "EGW" : "OTHERS";
      prevBoldQ = false; 
      prevUndQ  = false;
    }
    // B) Quote => Normal
    else if (inQuoteMode && !charInQuote) {
      // close quote styles
      while (quoteStack.length > 0) {
        quoteStack.pop();
        quoteBuffer += "}";
      }
      // remove “…” around the entire buffer
      quoteBuffer = removeOuterQuotes(quoteBuffer);

      // pick command
      var baseCmd = pickBaseCommand(quoteColorGroup, foundReference, foundFootnote);
      justEndedQuote = baseCmd + "{" + quoteBuffer + "}";
      // if we found {ref} inside the quote color
      if (foundReference) {
        justEndedQuote = appendReferenceToQuote(justEndedQuote, referenceText, referenceLink);
      }

      // reset quote state
      inQuoteMode = false;
      quoteColorGroup = "";
      quoteBuffer = "";
      foundReference = false;
      foundFootnote = false;
      referenceText = "";
      referenceLink = "";

      // normal style flags
      prevBoldN = false;
      prevItalN = false;
      prevUndN  = false;
    }

    // If we are in quote mode now
    if (inQuoteMode) {
      // handle bold/underline stack
      if (prevBoldQ && !curBold) {
        popStyle(quoteStack, "bold", function(){ quoteBuffer += "}"; });
      }
      if (prevUndQ && !curUnd) {
        popStyle(quoteStack, "underline", function(){ quoteBuffer += "}"; });
      }
      if (!prevBoldQ && curBold) {
        quoteStack.push("bold");
        quoteBuffer += "\\textbf{";
      }
      if (!prevUndQ && curUnd) {
        quoteStack.push("underline");
        quoteBuffer += "\\underline{";
      }

      // Check if this char is '{' => might be an inline reference
      if (ch === '{') {
        var closeIndex = text.indexOf('}', i+1);
        if (closeIndex > i) {
          var insideRef = text.substring(i+1, closeIndex);
          var refObj = parseReference(insideRef);
          if (refObj.refString) {
            foundReference = true;
            referenceText = refObj.refString;
            referenceLink = refObj.link;
            if (refObj.isFootnote) {
              foundFootnote = true;
            }
            i = closeIndex;
            prevBoldQ = curBold;
            prevUndQ  = curUnd;
            continue; // skip normal char append
          }
        }
      }

      // else append char to quote buffer
      quoteBuffer += ch;
      prevBoldQ = curBold;
      prevUndQ  = curUnd;
    }
    else {
      // Normal mode
      // If we have a justEndedQuote, see if next text is {ref} in normal color
      if (justEndedQuote) {
        var refNow = tryParseReferenceAt(textElement, i, endOffset);
        if (refNow.found) {
          justEndedQuote = appendReferenceToQuote(justEndedQuote, refNow.refText, refNow.refLink);
          textOutput += justEndedQuote;
          justEndedQuote = "";
          i = refNow.nextIndex - 1;
          continue;
        } else {
          // No reference => finalize quote
          textOutput += justEndedQuote;
          justEndedQuote = "";
        }
      }

      // handle normal bold/italic/underline
      if (prevBoldN && !curBold) {
        popStyle(normalStack, "bold", function(){ textOutput += "}"; });
      }
      if (prevItalN && !curItal) {
        popStyle(normalStack, "italic", function(){ textOutput += "}"; });
      }
      if (prevUndN && !curUnd) {
        popStyle(normalStack, "underline", function(){ textOutput += "}"; });
      }
      if (!prevBoldN && curBold) {
        normalStack.push("bold");
        textOutput += "\\textbf{";
      }
      if (!prevItalN && curItal) {
        normalStack.push("italic");
        textOutput += "\\textit{";
      }
      if (!prevUndN && curUnd) {
        normalStack.push("underline");
        textOutput += "\\underline{";
      }
      textOutput += ch;

      prevBoldN = curBold;
      prevItalN = curItal;
      prevUndN  = curUnd;
    }
  }

  // End of this run
  // If we ended in quote mode => finalize
  if (inQuoteMode) {
    while (quoteStack.length > 0) {
      quoteStack.pop();
      quoteBuffer += "}";
    }
    quoteBuffer = removeOuterQuotes(quoteBuffer);
    var baseCmd2 = pickBaseCommand(quoteColorGroup, foundReference, foundFootnote);
    justEndedQuote = baseCmd2 + "{" + quoteBuffer + "}";
    if (foundReference) {
      justEndedQuote = appendReferenceToQuote(justEndedQuote, referenceText, referenceLink);
    }
    inQuoteMode = false;
  }

  // close any remaining normal styles
  while (normalStack.length > 0) {
    normalStack.pop();
    textOutput += "}";
  }

  // If we ended exactly with a quote, store it as pending
  var newPendingQuoteLaTeX = justEndedQuote;

  return {
    textOutput: textOutput,
    pendingQuoteLaTeX: newPendingQuoteLaTeX
  };
}


/**
 * Decide which command to use, given color group and reference/footnote presence.
 */
function pickBaseCommand(colorGroup, foundReference, foundFootnote) {
  if (colorGroup === "EGW") {
    if (foundFootnote) {
      return "\\egwinline";
    }
    return "\\egw";
  } else {
    // OTHERS
    if (foundReference) {
      return "\\othersQuote";
    }
    return "\\others";
  }
}


/**
 * Removes leading/trailing quotes ( " “ ‘ ) around the entire text,
 * used for the text inside the quote color region only.
 */
function removeOuterQuotes(str) {
  str = str.trim();
  var openQuotes  = ["\"", "“", "‘", "«"];
  var closeQuotes = ["\"", "”", "’", "»"];

  while (str.length > 1) {
    var first = str.charAt(0);
    var last  = str.charAt(str.length - 1);
    if (openQuotes.indexOf(first) >= 0 && closeQuotes.indexOf(last) >= 0) {
      str = str.substring(1, str.length - 1).trim();
    } else {
      break;
    }
  }
  return str;
}


/**
 * Attempt to parse a reference block {EGW, ref; link} starting at or after startIndex.
 */
function tryParseReferenceAt(textElement, startIndex, endIndex) {
  var text = textElement.getText();
  var i = startIndex;

  // skip whitespace
  while (i <= endIndex && /\s/.test(text.charAt(i))) {
    i++;
  }
  if (i > endIndex) {
    return {found: false};
  }

  if (text.charAt(i) !== '{') {
    return {found: false};
  }

  var openIdx = i;
  var closeIdx = text.indexOf('}', openIdx+1);
  if (closeIdx < 0 || closeIdx > endIndex) {
    return {found: false};
  }

  var inside = text.substring(openIdx+1, closeIdx);
  var refObj = parseReference(inside);
  if (!refObj.refString) {
    return {found: false};
  }

  return {
    found: true,
    refText: refObj.refString,
    refLink: refObj.link,
    nextIndex: closeIdx + 1
  };
}


/**
 * parseReference(inside): e.g. "EGW, Ed 132.2; 1903; https://link"
 * returns { refString: "Ed 132.2; 1903", link: "", isFootnote: false }
 */
function parseReference(inside) {
  var trimmed = inside.trim();
  if (!trimmed) {
    return { refString: "", link: "", isFootnote: false };
  }

  var link = "";
  var parts = trimmed.split(";").map(function(x){ return x.trim(); });
  // If last part is a URL
  if (parts.length > 1) {
    var last = parts[parts.length - 1];
    if (/^https?:\/\//i.test(last)) {
      link = last;
      parts.pop();
      trimmed = parts.join("; ");
    }
  }

  // remove "EGW" prefix if present
  if (/^EGW/i.test(trimmed)) {
    var idx = trimmed.indexOf(" ");
    if (idx > 0) {
      trimmed = trimmed.substring(idx).trim();
    } else {
      trimmed = trimmed.replace(/^EGW[,]?/i, "").trim();
    }
  }
  if (!trimmed) {
    return { refString: "", link: "", isFootnote: false };
  }

  // If you detect footnotes by a pattern, set isFootnote = true
  return { refString: trimmed, link: link, isFootnote: false };
}


/**
 * Append reference to a quote command.
 * e.g. "\egw{text}" + "Ed 132.2" => "\egw{text}[Ed 132.2]"
 * If link is present => "[Ed 132.2][link]"
 */
function appendReferenceToQuote(quoteLaTeX, refText, link) {
  if (!refText) return quoteLaTeX;
  if (link) {
    return quoteLaTeX + "[" + refText + "][" + link + "]";
  }
  return quoteLaTeX + "[" + refText + "]";
}


/**
 * Typical stack-based "popStyle": 
 *   we pop until we find `target`.
 *   On each pop, call onPop() to close braces, e.g. "}".
 */
function popStyle(stack, target, onPop) {
  while (stack.length > 0) {
    var top = stack.pop();
    if (onPop) onPop();
    if (top === target) {
      break;
    }
  }
}


/**
 * Final post-processing:
 *  Remove any extra quotes around a single LaTeX command, if the entire
 *  content between the quotes is just "\egw{...}[...][...]" or similar.
 *
 *  e.g. “\others{\textbf{...}}” => \others{\textbf{...}}
 */
function removeQuotesAroundSingleCommand(str) {
  var oldStr;
  do {
    oldStr = str;
    // Regex pattern:
    // (["“]) => open quote
    // \s* => optional spaces
    // (\\(egw|egwinline|others|othersQuote)\S+) => backslash + one of the commands + some non-space text (handles {..} etc.)
    // \s*
    // (["”]) => close quote
    //
    // Replace with just the LaTeX command part (capture group 2).
    //
    // You can tweak if your doc uses different curly quotes. For instance:
    // you might add single quotes ' or other glyphs.
    var pattern = /(["“])\s*(\\(?:egw|egwinline|others|othersQuote)\S+)\s*(["”])/g;
    str = str.replace(pattern, "$2");
  } while (str !== oldStr);

  return str;
}


/**
 * Displays final text in a dialog with a "Copy" button
 */
function showLatexInDialog(finalOutput) {
  var ui = DocumentApp.getUi();
  var html = `
  <html>
  <body>
    <p><b>EGW Multi-Paragraph / SHIFT+Enter:</b></p>
    <textarea id="latexArea" style="width:100%; height:200px;">
${escapeHtml(finalOutput)}</textarea>
    <br><br>
    <button onclick="copyLatex()">Copy</button>
    <script>
      function copyLatex(){
        var text = document.getElementById("latexArea").value;
        navigator.clipboard.writeText(text)
          .then(()=>{alert("Copied!");})
          .catch(err=>{alert("Copy failed: "+err);});
      }
    </script>
  </body>
  </html>
  `;
  var dlg = HtmlService.createHtmlOutput(html)
    .setWidth(600)
    .setHeight(400);
  ui.showModalDialog(dlg, "EGW Output");
}