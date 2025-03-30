/**
 * Main function: 
 * 1) Gathers the user's selection, grouped by real paragraphs (Enter).
 * 2) For each paragraph, we do a character-by-character parse, 
 *    splitting further on manual line breaks (Shift+Enter).
 * 3) Each final segment becomes its own \egw{...}[ref][link] block, 
 *    preserving bold & underline, and extracting the {EGW,...} reference.
 */
function convertSelectionToEGWs() {
  var doc = DocumentApp.getActiveDocument();
  var selection = doc.getSelection();
  if (!selection) {
    DocumentApp.getUi().alert("No text is selected.");
    return;
  }

  // Step 1: Gather paragraphs from the selection
  var paragraphItems = collectRangeElementsByParagraph(selection);
  
  // We'll store the final LaTeX blocks here
  var allBlocks = [];

  // Step 2: For each paragraph, parse it
  for (var p = 0; p < paragraphItems.length; p++) {
    var rangeElems = paragraphItems[p].rangeElems;
    // This function returns an array of sub‐blocks 
    // if the paragraph has Shift+Enter breaks:
    var blocksFromThisParagraph = parseParagraphWithSubBreaks(rangeElems);
    // Add them to our master list
    allBlocks = allBlocks.concat(blocksFromThisParagraph);
  }

  // Step 3: Join them with two newlines => one blank line in most LaTeX
  var finalOutput = allBlocks.join("\n\n");

  // Step 4: Show in a dialog with a "Copy" button
  showLatexInDialog(finalOutput);
}

/**
 * Collect RangeElements from the selection, grouped by actual 
 * Google Docs paragraphs (created by Enter).
 */
function collectRangeElementsByParagraph(selection) {
  var doc = DocumentApp.getActiveDocument();
  var body = doc.getBody();
  var rangeElements = selection.getRangeElements();
  var paraMap = {};

  for (var i = 0; i < rangeElements.length; i++) {
    var re = rangeElements[i];
    var el = re.getElement();
    if (el.getType() === DocumentApp.ElementType.TEXT) {
      // climb up to paragraph
      var p = el.getParent();
      while (p && p.getType() !== DocumentApp.ElementType.PARAGRAPH) {
        p = p.getParent();
      }
      if (!p) continue;

      var paragraphIndex = body.getChildIndex(p);
      if (!paraMap[paragraphIndex]) {
        paraMap[paragraphIndex] = { paragraph: p, rangeElems: [] };
      }
      paraMap[paragraphIndex].rangeElems.push(re);
    }
  }

  // sort by paragraph index
  var sortedKeys = Object.keys(paraMap).sort(function(a,b){return a-b;});
  var results = [];
  for (var k = 0; k < sortedKeys.length; k++) {
    results.push(paraMap[sortedKeys[k]]);
  }
  return results;
}

/**
 * Parse a single "Doc paragraph" (rangeElements) but also handle SHIFT+Enter 
 * as a separate sub‐paragraph. Returns an array of LaTeX blocks if multiple 
 * SHIFT+Enter breaks appear in the same doc paragraph. 
 */
function parseParagraphWithSubBreaks(rangeElems) {
  // We'll keep track of multiple sub‐paragraphs if SHIFT+Enter is used.
  // Each sub‐paragraph has top-level style runs + reference info.
  var subParagraphs = [];
  var currentPara = createEmptyParagraphData();

  var insideRef = false;
  var refBuffer = "";

  // "currentRun" is the top-level run, grouped by bold vs not bold
  var currentRun = null;

  // flush the current run into currentPara
  function flushRun() {
    if (currentRun && currentRun.chars.length > 0) {
      currentPara.runs.push(currentRun);
    }
    currentRun = null;
  }

  // finalize the current sub‐paragraph
  function finalizeSubParagraph() {
    flushRun();
    // If there's content or reference, store it
    if (currentPara.runs.length > 0 || currentPara.referenceText) {
      subParagraphs.push(currentPara);
    }
    // start a new sub‐paragraph
    currentPara = createEmptyParagraphData();
    insideRef = false;
    refBuffer = "";
  }

  // character‐by‐character
  for (var r = 0; r < rangeElems.length; r++) {
    var re = rangeElems[r];
    var txtEl = re.getElement().asText();
    var start = re.getStartOffset();
    var end   = re.getEndOffsetInclusive();

    for (var i = start; i <= end; i++) {
      var ch = txtEl.getText().charAt(i);

      if (!insideRef) {
        // check for {EGW,...
        if (ch === '{') {
          var ahead = txtEl.getText().substring(i, i+30);
          var m = ahead.match(/^\{\s*EGW,\s*/i);
          if (m) {
            // finalize the current run
            flushRun();
            insideRef = true;
            refBuffer = "";
            continue; // skip '{'
          }
        }
        // check for SHIFT+Enter => '\n'
        if (ch === '\n') {
          // end of this sub‐paragraph
          flushRun();
          finalizeSubParagraph();
          continue;
        }
        // normal char
        var bold = !!txtEl.isBold(i);
        var underline = !!txtEl.isUnderline(i);
        if (!currentRun || currentRun.bold !== bold) {
          flushRun();
          currentRun = { bold: bold, chars: [] };
        }
        currentRun.chars.push({ ch: ch, underline: underline });
      } else {
        // we are inside a {EGW,...} block
        var maybeLink = txtEl.getLinkUrl(i);
        if (maybeLink && !currentPara.referenceLink) {
          currentPara.referenceLink = latexEscapeUrl(maybeLink);
        }
        if (ch === '}') {
          insideRef = false;
          var trimmed = refBuffer.trim().replace(/^EGW,\s*/i, "");
          currentPara.referenceText = trimmed;
          refBuffer = "";
        } else {
          refBuffer += ch;
        }
      }
    }

    // if this RangeElement ends at a doc paragraph boundary
    if (re.isAtParagraphEnd && re.isAtParagraphEnd()) {
      flushRun();
      finalizeSubParagraph();
    }
  }

  // end of paragraph
  flushRun();
  finalizeSubParagraph();

  // Now subParagraphs is an array of data objects. Next, we convert each 
  // sub‐paragraph to a single LaTeX block.
  var blocks = [];
  for (var s = 0; s < subParagraphs.length; s++) {
    var sp = subParagraphs[s];
    var latex = buildLaTeXBlock(sp);
    if (latex.trim()) {
      blocks.push(latex);
    }
  }
  return blocks;
}

/** A helper to create empty sub‐paragraph data */
function createEmptyParagraphData() {
  return {
    runs: [],            // array of { bold:bool, chars:[ {ch, underline:bool} ] }
    referenceText: "",
    referenceLink: ""
  };
}

/**
 * Build a single \egw{...}[reference][link] block from a sub‐paragraph data object.
 */
function buildLaTeXBlock(paraData) {
  var mainQuotation = topRunsToLatex(paraData.runs);
  mainQuotation = stripSurroundingQuotes(mainQuotation);

  var refPart  = paraData.referenceText ? "[" + paraData.referenceText + "]" : "";
  var linkPart = paraData.referenceLink ? "[" + paraData.referenceLink + "]" : "";
  return "\\egw{" + mainQuotation + "}" + refPart + linkPart;
}

/**
 * Convert runs => final text. 
 * Each "run" is grouped by bold vs not bold, 
 * sub‐runs for underline vs not underline.
 */
function topRunsToLatex(topRuns) {
  var out = "";
  for (var i = 0; i < topRuns.length; i++) {
    var run = topRuns[i];
    // sub-runs by underline
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

/**
 * Remove leading/trailing quotes if they wrap the entire string.
 */
function stripSurroundingQuotes(str) {
  var t = str.trim();
  if (t.startsWith("\"") && t.endsWith("\"")) {
    return t.slice(1, -1);
  }
  // curly quotes
  if (
    (t.startsWith("“") && t.endsWith("”")) ||
    (t.startsWith("”") && t.endsWith("“"))
  ) {
    return t.slice(1, -1);
  }
  return t;
}

/**
 * Escape backslash, underscore, and percent in URLs for LaTeX
 */
function latexEscapeUrl(url) {
  return url
    .replace(/\\/g, "\\\\")
    .replace(/_/g, "\\_")
    .replace(/%/g, "\\%");
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

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g,"&amp;")
    .replace(/</g,"&lt;")
    .replace(/>/g,"&gt;");
}
