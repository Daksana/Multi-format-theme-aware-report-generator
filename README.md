

# Multi-Format Report Summary Generator

An AI-powered tool for generating structured, theme-aware summary reports in Markdown, with flexible body styles.

## Features
- **Configurable Body Styles:** Generates summaries in Markdown with selectable body styles: key findings, pros & cons, risks & mitigations, or metrics & trends
- **Theme Detection:** Automatically analyzes the document to extract and rank major themes, which become subtopics in the summary
- **User-Driven Parameters:** User can set audience, tone, number of subtopics, and bullets per subtopic
- **PDF Support:** Reads and processes PDF reports
- **Consistent Output:** Always produces Introduction, Body (with subtopics), and Conclusion in Markdown

## Techniques Demonstrated
- PDF text extraction and intelligent document processing
- Prompt engineering for LLM-based summarization
- Dynamic prompt templates for flexible summary structure
- Theme analysis and subtopic suggestion
- Markdown report generation with structured sections

## Getting Started

1. **Install dependencies:**
   ```bash
   pip install google-generativeai python-dotenv PyPDF2
   ```
   Create a `.env` file with your Google API key:
   ```
   GOOGLE_API_KEY=your_api_key_here
   ```

2. **Prepare input documents:**
   Place your PDF files in any accessible location.

3. **Run the generator:**
   ```bash
   python multi_format_report_generator_tools.py
   ```
   Follow the prompts to select audience, tone, body style, and structure.

4. **View output:**
   Generated summaries will be saved as Markdown files in the same directory as your input PDF, e.g., `yourfile_key_findings_summary.md`.

## How It Works
- Reads and processes a single PDF report
- Analyzes the text to detect themes and suggest subtopics
- Accepts user input for summary style and structure
- Generates a Markdown summary with Introduction, Body (with subtopics and bullets), and Conclusion
- Supports four body styles: key findings, pros & cons, risks & mitigations, metrics & trends

## Example Outputs
See the `Submission_folder_daksana/Output summaries/` folder for sample summaries in different body styles.


---
Project developed under AI Orchestration Bootcamp by Senzmate IoT Intelligence.
