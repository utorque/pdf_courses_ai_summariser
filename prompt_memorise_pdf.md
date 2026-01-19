Here's a detailed prompt you can reuse:

---

## Prompt Template for Memorization-Focused Exam Summary

```
I have course notes for [COURSE NAME] that I need to transform into a memorization-focused exam summary PDF (LaTeX/Overleaf).

I'm already familiar with the technical/practical aspects of [DOMAIN]. I need to focus on what I must learn BY HEART for the exam.

Please create a document with the following structure:

---

## 1. ALL MNEMONICS IN ONE PLACE
Create a table with:
- Mnemonic acronym (highlighted)
- What it stands for
- What concept it covers

If the course doesn't have explicit mnemonics, CREATE memorable ones for key lists and frameworks.

## 2. QUICK RECALL PHRASES
Short memorable phrases for key concepts (e.g., "Philosophy, not technology", "X causes Y", etc.)

## 3. THE CORE CONCEPT DEEP DIVE
Identify the ONE most important/tricky concept in this course (the thing exam questions will definitely test). Create:
- A comparison table if there are similar concepts to distinguish
- Clear examples for each case
- Detection/identification methods if applicable

## 4. TRADE-OFFS SECTION
For every technique/method/approach in the course, create tables with:
- What you GAIN
- What you LOSE
Group by category (e.g., optimization techniques, strategies, infrastructure choices, etc.)

## 5. COMMON EXAM TRAPS
Create a "What works / What doesn't" table for common misconceptions, formatted as:
- Method | Yes/No | Why
Use color coding (green for yes, red for no)
Include a memorable mantra if possible.

## 6. DECISION TREES (Visual)
Create 2-4 flowchart decision trees using TikZ for the main "when to use what" decisions in the course. Format:
- Diamond = decision point (question)
- Rectangle = answer/choice
- Clear Yes/No paths

## 7. QUICK DECISION TABLE
A single table mapping "If you have X situation → Use Y approach" for rapid lookup.

## 8. KEY FRAMEWORKS SIDE-BY-SIDE
If there are multiple frameworks/methodologies, put them in a comparison table showing parallels and differences.

## 9. FACTS TO MEMORIZE
True/False table for statements that commonly appear in exams.

## 10. FINAL SELF-TEST CHECKLIST
Numbered list of 10-15 questions I should be able to answer from memory before the exam, with brief answers in italics.

---

## Style requirements:
- Readable 11pt font, comfortable margins (this is for LEARNING, not a cheat sheet)
- Use highlighting/color boxes for key terms
- Tables should be clean with booktabs
- Decision trees should be visual (TikZ flowcharts)
- End with all mnemonics listed together as a final reminder

## DO NOT include:
- Basic technical knowledge I already have as a [ROLE]
- Long explanations or theory
- Anything I don't need to memorize

Here are my course notes:

[PASTE NOTES HERE]
```

---

## Example filled in:

```
I have course notes for Distributed Systems that I need to transform into a memorization-focused exam summary PDF (LaTeX/Overleaf).

I'm already familiar with the technical/practical aspects of distributed computing. I need to focus on what I must learn BY HEART for the exam.

[... rest of template ...]

DO NOT include:
- Basic technical knowledge I already have as a software engineer
- Code examples
- Implementation details

Here are my course notes:

[PASTE NOTES]
```

---

**Tips for best results:**
1. Mention your background so I skip what you know
2. If you know specific exam topics, mention them
3. If the course has specific tricky distinctions (like concept vs data drift), mention those
4. Upload the notes as a file rather than pasting if they're long
