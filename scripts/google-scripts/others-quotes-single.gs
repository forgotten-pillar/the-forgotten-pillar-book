function convertSelectionByMultipleReferences() {
  var doc = DocumentApp.getActiveDocument();
  var selection = doc.getSelection();
  if (!selection) {
    DocumentApp.getUi().alert("No text is selected.");
    return;
  }

  var blocks = [];    // array of "Block" objects
  var currentBlock = createEmptyBlock();  // the block we are building right now
  var insideRef = false;
  var refBuffer = "";

  function flushTopRun() {
    if (currentBlock.currentRun && currentBlock.currentRun.chars.length > 0) {
      currentBlock.runs.push(currentBlock.currentRun);
    }
    currentBlock.currentRun = null;
  }

  function finalizeBlock() {
    // End the current top-level run
    flushTopRun();
    // If there's any content or reference, push it into blocks
    if (currentBlock.runs.length > 0 || currentBlock.referenceText) {
      blocks.push(currentBlock);
    }
    currentBlock = createEmptyBlock();
  }

  var rangeElems = selection.getRangeElements();
  for (var r = 0; r < rangeElems.length; r++) {
    var re = rangeElems[r];
    var el = re.getElement();

    if (el.getType() === DocumentApp.ElementType.TEXT) {
      var txt = el.asText();
      var start = re.getStartOffset();
      var end   = re.getEndOffsetInclusive();

      for (var i = start; i <= end; i++) {
        var ch = txt.getText().charAt(i);

        if (!insideRef) {
          // Check if this is the start of a reference block { ... }
          if (ch === '{') {
            // flush current text run
            flushTopRun();
            insideRef = true;
            refBuffer = "";
            // skip adding '{' to main text
            continue;
          }

          // Normal text
          var isBold = !!txt.isBold(i);
          var isUnderline = !!txt.isUnderline(i);
          if (!currentBlock.currentRun || currentBlock.currentRun.bold !== isBold) {
            flushTopRun();
            currentBlock.currentRun = { bold: isBold, chars: [] };
          }
          currentBlock.currentRun.chars.push({ ch: ch, underline: isUnderline });

        } else {
          // We are inside a { ... } reference
          var maybeLink = txt.getLinkUrl(i);
          if (maybeLink && !currentBlock.referenceLink) {
            currentBlock.referenceLink = latexEscapeUrl(maybeLink);
          }
          if (ch === '}') {
            // end of reference
            insideRef = false;
            var trimmed = refBuffer.trim();
            currentBlock.referenceText = trimmed;
            refBuffer = "";
            // finalize the block now that we've closed } 
            finalizeBlock();
          } else {
            refBuffer += ch;
          }
        }
      }
    }
  }

  // finalize any text that remains after the last reference block
  flushTopRun();
  if (currentBlock.runs.length > 0) {
    blocks.push(currentBlock);
  }

  // Convert each block to \othersQuote{...}[ref][link].
  var finalOutputArr = [];
  for (var b = 0; b < blocks.length; b++) {
    var block = blocks[b];
    var latex = buildOthersQuoteBlock(block);
    if (latex.trim()) {
      finalOutputArr.push(latex);
    }
  }

  var finalOutput = finalOutputArr.join("\n\n");
  showLatexInDialog(finalOutput);
}

function createEmptyBlock() {
  return {
    runs: [],
    currentRun: null,
    referenceText: "",
    referenceLink: ""
  };
}

// Build \othersQuote{ ... }[reference][link]
function buildOthersQuoteBlock(block) {
  if (block.currentRun && block.currentRun.chars.length > 0) {
    block.runs.push(block.currentRun);
  }

  var mainQuotation = topRunsToLatex(block.runs);
  mainQuotation = stripSurroundingQuotes(mainQuotation);

  var refPart = block.referenceText ? "[" + block.referenceText + "]" : "";
  var linkPart = block.referenceLink ? "[" + block.referenceLink + "]" : "";

  return "\\othersQuote{" + mainQuotation + "}" + refPart + linkPart;
}

/** Builds a LaTeX string from an array of runs = { bold, chars: [ {ch, underline}, ... ]}. */
function topRunsToLatex(runs) {
  var out = "";
  for (var i = 0; i < runs.length; i++) {
    var run = runs[i];
    // break into sub-runs by underline
    var subRuns = [];
    var currentSub = null;

    for (var j = 0; j < run.chars.length; j++) {
      var cObj = run.chars[j];
      if (!currentSub || currentSub.underline !== cObj.underline) {
        if (currentSub) {
          subRuns.push(currentSub);
        }
        currentSub = { underline: cObj.underline, text: "" };
      }
      currentSub.text += cObj.ch;
    }
    if (currentSub) subRuns.push(currentSub);

    // build run text
    var runText = "";
    for (var s = 0; s < subRuns.length; s++) {
      var sr = subRuns[s];
      if (sr.underline) {
        runText += "\\underline{" + sr.text + "}";
      } else {
        runText += sr.text;
      }
    }

    if (run.bold) {
      out += "\\textbf{" + runText + "}";
    } else {
      out += runText;
    }
  }
  return out;
}

/** Remove surrounding quotes if they wrap the entire text. */
function stripSurroundingQuotes(str) {
  var t = str.trim();
  if (
    (t.startsWith("\"") && t.endsWith("\"")) ||
    (t.startsWith("“") && t.endsWith("”")) ||
    (t.startsWith("”") && t.endsWith("“"))
  ) {
    return t.slice(1, -1);
  }
  return t;
}

/** Escape LaTeX‐special chars in a URL. */
function latexEscapeUrl(url) {
  return url
    .replace(/\\/g, "\\\\")
    .replace(/_/g, "\\_")
    .replace(/%/g, "\\%");
}

/** Show a dialog with finalOutput, plus a "Copy" button. */
function showLatexInDialog(finalOutput) {
  var ui = DocumentApp.getUi();
  var content = `
    <html>
      <body>
        <p><b>Multiple references => multiple blocks</b></p>
        <textarea id="latexArea" style="width:100%; height:200px;">${escapeHtml(finalOutput)}</textarea>
        <br><br>
        <button onclick="copyLatex()">Copy</button>
        <script>
          function copyLatex() {
            var text = document.getElementById("latexArea").value;
            navigator.clipboard.writeText(text)
              .then(() => { alert("Copied!"); })
              .catch(err => { alert("Copy failed: " + err); });
          }
        </script>
      </body>
    </html>
  `;
  var html = HtmlService.createHtmlOutput(content)
    .setWidth(600)
    .setHeight(400);
  ui.showModalDialog(html, "Other Quotes by Multiple References");
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g,"&amp;")
    .replace(/</g,"&lt;")
    .replace(/>/g,"&gt;");
}
