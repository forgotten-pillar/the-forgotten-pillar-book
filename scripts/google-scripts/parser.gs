function parserStackBased() {
  var doc = DocumentApp.getActiveDocument();
  var selection = doc.getSelection();
  if (!selection) {
    DocumentApp.getUi().alert("No text is selected.");
    return;
  }
  
  var rangeElements = selection.getRangeElements();
  
  // We'll build the final LaTeX for the entire selection in one string:
  var latexOutput = "";

  for (var i = 0; i < rangeElements.length; i++) {
    var element = rangeElements[i].getElement();
    var startOffset = rangeElements[i].getStartOffset();
    var endOffset = rangeElements[i].getEndOffsetInclusive();
    
    // Make sure the element is text we can edit
    if (element.editAsText) {
      var textElement = element.asText();
      latexOutput += convertTextElementUsingStack(textElement, startOffset, endOffset);
    }
  }

  // Show the entire LaTeX
  DocumentApp.getUi().alert(latexOutput);
}


/**
 * Converts a single Text element (from startOffset to endOffset) into LaTeX
 * using a stack-based style parser.
 */
function convertTextElementUsingStack(textElement, startOffset, endOffset) {
  var text = textElement.getText();
  var styleStack = [];
  var result = "";

  // Track previous character's style
  var prevBold = false;
  var prevItal = false;
  var prevUnd = false;

  for (var j = startOffset; j <= endOffset; j++) {
    var curBold = textElement.isBold(j);
    var curItal = textElement.isItalic(j);
    var curUnd  = textElement.isUnderline(j);

    // ---- 1) CLOSE any styles that turned OFF ----------------------------------
    // We'll close in reverse order only for those styles that are no longer on.
    // Because it's LIFO, we pop from the styleStack until the top is a style that remains active.
    // This ensures correct nesting.
    if (prevUnd && !curUnd) {
      popStyleUntil(styleStack, "underline", result);
      result += "}";
    }
    if (prevBold && !curBold) {
      popStyleUntil(styleStack, "bold", result);
      result += "}";
    }
    if (prevItal && !curItal) {
      popStyleUntil(styleStack, "italic", result);
      result += "}";
    }

    // ---- 2) OPEN any styles that turned ON -----------------------------------
    if (!prevItal && curItal) {
      styleStack.push("italic");
      result += "\\textit{";
    }
    if (!prevBold && curBold) {
      styleStack.push("bold");
      result += "\\textbf{";
    }
    if (!prevUnd && curUnd) {
      styleStack.push("underline");
      result += "\\underline{";
    }

    // ---- 3) Append the actual character --------------------------------------
    result += text.charAt(j);

    // ---- 4) Update previous style flags --------------------------------------
    prevBold = curBold;
    prevItal = curItal;
    prevUnd  = curUnd;
  }

  // ---- 5) Close any styles still open ----------------------------------------
  // Pop from the stack in LIFO order and append closing braces
  while (styleStack.length > 0) {
    styleStack.pop(); // we know what style it is, but we just need to close
    result += "}";
  }

  return result;
}


/**
 * Pop from the stack until the top is the style we want to remove,
 * ensuring we don't incorrectly pop multiple styles if there's nested overlap.
 * Then remove that style.
 */
function popStyleUntil(styleStack, target, result) {
  // If the stack is well-formed, the top should be `target`.
  // If there's an out-of-order style toggle, you may need more advanced logic.
  while (styleStack.length > 0) {
    var top = styleStack[styleStack.length - 1];
    if (top === target) {
      styleStack.pop();
      break;
    } else {
      // If the top is a different style, close it too.
      // But that might cause complex re-open logic if toggling is not well-structured.
      // For simplicity, we just pop everything in a pinch:
      styleStack.pop();
      result += "}";
    }
  }
}
