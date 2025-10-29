"""
Multi-Format Report Summary Generator - Part 3
==============================================

Assignment implementation: A flexible prompt-driven system that integrates Parts 1 & 2
to create multi-format report summaries with configurable body styles.

Features:
- Theme detection and ranking (Part 2 integration)
- Structured summary generation (Part 1 integration)  
- 4 configurable body styles: key_findings, pros_cons, risks_mitigations, metrics_trends
- PDF document processing support
- Flexible parameters for audience, tone, and structure

Requirements:
- pip install google-generativeai python-dotenv PyPDF2
- .env file with GOOGLE_API_KEY=your_api_key_here

Author: Daksana
Date: October 28, 2025
"""

import json
import os
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
from google import genai
from google.genai import types
import PyPDF2

# Load environment variables from .env file
load_dotenv()


# =============================================================================
# PDF PROCESSING
# =============================================================================

def read_pdf_pages(pdf_path: str, num_pages: int = None) -> Optional[str]:
    """Read text content from PDF file."""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            total_pages = len(reader.pages)
            
            if num_pages is None:
                num_pages = total_pages
            
            text = ""
            pages_to_read = min(num_pages, total_pages)
            
            for page_num in range(pages_to_read):
                page_text = reader.pages[page_num].extract_text()
                text += page_text + "\n"
            
            return text
            
    except FileNotFoundError:
        print(f"Error: PDF file not found at {pdf_path}")
        return None
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return None


def process_long_report_intelligently(pdf_path: str) -> str:
    """
    Process long reports with single LLM call using chain-of-thought approach.
    Much more efficient and maintains context better than chunking.
    """
    try:
        # Read entire PDF
        full_text = read_pdf_pages(pdf_path)
        if not full_text:
            return ""
            
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            total_pages = len(reader.pages)
        
        # For short documents, return as-is
        if total_pages <= 10:
            return full_text
            
        print(f"Long document detected ({total_pages} pages). Processing with intelligent extraction...")
        
        client = setup_gemini_client()
        
        # Single comprehensive prompt with chain-of-thought
        extraction_prompt = f"""
        You are an expert document analyst. You need to process this long business report ({total_pages} pages) and extract key points that will be used for further analysis.

        CHAIN OF THOUGHT INSTRUCTIONS:
        1. Read through the ENTIRE document carefully
        2. As you read, mentally organize content by every 5-10 pages
        3. For each section, identify the most critical business points
        4. Focus on: main findings, data/metrics, decisions, issues, strategic information
        5. Maintain document flow and connections between sections
        6. Extract comprehensive key points that preserve the document's narrative

        FULL DOCUMENT:
        <<<
        {full_text}
        >>>

        EXTRACTION GUIDELINES:
        - Keep each key points concise but informative
        - Preserve important numbers, percentages, dates
        - Maintain logical flow and connections
        - Ensure extracted points can stand alone for analysis
        
        CRITICAL CONSTRAINTS:
        - ONLY use information explicitly stated in the document
        - Do NOT add your own knowledge, interpretation, or assumptions

        OUTPUT FORMAT:
        • Key point 1 with context and data
        • Key point 2 with context and data
        [continue for all key points]

        Think step by step through the document and extract the most valuable information.
        """
        
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[extraction_prompt],
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    max_output_tokens=8000,  # More tokens for comprehensive extraction
                ),
            )
            
            extracted_text = response.text
            print(f"Successfully extracted key points from {total_pages} pages.")
            print(f"Original: {len(full_text)} chars → Extracted: {len(extracted_text)} chars")
            
            return extracted_text
            
        except Exception as e:
            print(f"Error in intelligent extraction: {e}")
            print("Falling back to full document...")
            return full_text  # Fallback to full text
            
    except Exception as e:
        print(f"Error processing document: {e}")
        return read_pdf_pages(pdf_path)  # Fallback


def setup_gemini_client(api_key: str = None) -> genai.Client:
    """Initialize Gemini API client."""
    if api_key is None:
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in .env file")
    
    client = genai.Client(api_key=api_key)
    return client


# =============================================================================
# PART 2: THEME ANALYZER
# =============================================================================

def analyze_themes(report_text: str, client: genai.Client) -> Dict[str, Any]:
    """
    Theme detection and ranking.
    """
    theme_analysis_prompt = f"""
    You are an expert document analyst with deep expertise in thematic analysis.
    
    OBJECTIVE: Analyze this document and identify the most significant recurring themes that would be valuable for creating an accurate summary.
    
    ANALYSIS METHODOLOGY:
    1. Read the entire document carefully
    2. Identify patterns, recurring topics, and key areas
    3. Evaluate theme importance based on:
       - Frequency of mention
       - Content significance  
       - Data/metrics associated with the theme
       - Relevance for comprehensive summarization
    4. Rank themes by importance (0.0-1.0 scale)
    5. Generate 3-4 broad subtopic categories suitable for summary
    
    DOCUMENT TO ANALYZE:
    <<<
    {report_text}
    >>>
    
    OUTPUT REQUIREMENTS:
    Return ONLY a valid JSON object in this exact format:
    {{
        "themes": [
            {{
                "name": "Clear Theme Name",
                "importance": 0.95
            }}
        ],
        "suggested_subtopics": ["Subtopic 1", "Subtopic 2", "Subtopic 3"]
    }}
    
    QUALITY CRITERIA:
    - Theme names should be specific and focused
    - Importance scores should reflect content significance in the original document
    - Suggested subtopics should be broad enough for 3 bullet points each
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[theme_analysis_prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2,
                max_output_tokens=4000,
            ),
        )
        
        theme_data = json.loads(response.text)
        return theme_data
        
    except Exception as e:
        print(f"Error in theme analysis: {e}")
        return {
            "themes": [{"name": "General Analysis", "importance": 0.8}],
            "suggested_subtopics": ["Key Points", "Analysis", "Recommendations"]
        }


# =============================================================================
# PART 3: MULTI-FORMAT SUMMARY GENERATOR
# =============================================================================

def generate_multi_format_summary(report_text: str,
                                 audience: str = None,
                                 tone: str = None, 
                                 num_subtopics: int = None,
                                 bullets_per_subtopic: int = None,
                                 suggested_subtopics: list = None,
                                 body_style: str = None) -> str:
    """
    Multi-Format Report Summary Generator
    """
    # Set defaults for any None parameters
    audience = audience or "executives"
    tone = tone or "neutral"
    num_subtopics = num_subtopics or 3
    bullets_per_subtopic = bullets_per_subtopic or 3
    suggested_subtopics = suggested_subtopics or ["Key Points", "Analysis", "Recommendations"]
    body_style = body_style or "key_findings"
    
    # Step 1: Initialize client
    client = setup_gemini_client()
    
    # Step 2: Use the provided subtopics from theme analysis
    subtopics_to_use = suggested_subtopics[:num_subtopics]
    
    # Step 3: Create detailed style instructions
    style_instructions = {
        "key_findings": """
        For key_findings style:
        - Each bullet should follow: Key Insight + Supporting Evidence + Business Implication
        - Focus on actionable insights and strategic value
        - Example: "• Customer retention decreased 15% (Q3 data) → indicating need for enhanced loyalty programs"
        """,
        "pros_cons": """
        For pros_cons style:
        - Alternate between **Pros** and **Cons** with clear justification
        - Present balanced perspective with evidence
        - Example: "• **Pro:** Revenue increased 12% due to new product launch **Con:** Operating costs rose 8% from expanded infrastructure"
        """,
        "risks_mitigations": """
        For risks_mitigations style:
        - Each bullet: Risk Description → Likelihood (High/Medium/Low) → Impact → Specific Mitigation
        - Focus on actionable risk management
        - Example: "• Supply chain disruption → High likelihood → $2M potential loss → Establish secondary supplier agreements"
        """,
        "metrics_trends": """
        For metrics_trends style:
        - Each bullet: Metric Name → Current Value → Change/Trend → Key Driver
        - Include quantitative data and trend analysis
        - Example: "• Customer Acquisition Cost → $150 → 25% increase YoY → driven by competitive digital marketing landscape"
        """
    }
    
    # Get the specific style instruction for the selected body style
    selected_style_instruction = style_instructions.get(body_style, style_instructions["key_findings"])
    
    # Step 4: Create the multi-format prompt template
    prompt_template = f"""
    System:
    You are a meticulous analyst who produces clear, structured summaries from long documents.
    Always generate ALL THREE sections - Introduction, Body, and Conclusion.
    
    
    User:
    Create a comprehensive summary using the identified themes and specified formatting requirements.
    
    Document:
    <<<
    {report_text}
    >>>
    
    Parameters:
    - Audience: {audience}
    - Tone: {tone}
    - Number of subtopics: {num_subtopics}
    - Bullets per subtopic: {bullets_per_subtopic}
    - Subtopics: {subtopics_to_use}
    - Body writing style: {body_style}
    
    WRITING APPROACH:
    - Use the style instructions below as guidance for the type of content and approach
    - Write each bullet as a natural, flowing summary statement (50-80 words)
    - Avoid explicitly stating structural labels or formulaic phrases
    - Focus on delivering substantive insights in a readable, professional manner
    - Ensure each bullet provides complete value and context
    - The Introduction should mention the analytical approach being used in one sentence.
    
    BODY STYLE DETAILED INSTRUCTIONS:
    {selected_style_instruction}
    
    Output Format:
    # Introduction
    (2–3 sentences overview + one sentence explaining the {body_style} analytical approach being used)
    
    # Body
    ## Subtopic 1
    - Bullet 1
    - Bullet 2  
    - Bullet 3
    
    ## Subtopic 2
    - Bullet 1
    - Bullet 2
    - Bullet 3
    
    ## Subtopic 3
    - Bullet 1
    - Bullet 2
    - Bullet 3
    
    # Conclusion
    (2–3 sentences summarizing key implications and main takeaways)
    
    
    Generate the summary now using the {body_style} style as guidance for content approach.
    Write natural, flowing bullet points that capture the essence and insights without explicitly stating labels.
    Maintain correct flow and logical progression in each bullet point.
    Use proper Markdown formatting with headers (#, ##) and bullet points (-).
    
    CRITICAL REQUIREMENTS:
    1. MUST include Introduction with analytical approach explanation
    2. MUST include Body with all specified subtopics and bullets
    3. MUST include Conclusion with key takeaways
    """
    
    # Step 4: Generate summary
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt_template],
            config=types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=6000,
            ),
        )
        
        return response.text
        
    except Exception as e:
        return f"Error generating summary: {str(e)}"





if __name__ == "__main__":
    # Get PDF path from user
    pdf_path = input("Enter PDF file path: ").strip()
    
    if not os.path.exists(pdf_path):
        print(f"Error: File not found - {pdf_path}")
        exit(1)
    
    # Read PDF content with intelligent processing for long reports
    print(f"Processing: {os.path.basename(pdf_path)}")
    report_text = process_long_report_intelligently(pdf_path)
    
    if not report_text:
        print("Error: Could not read PDF file")
        exit(1)
    
    # Get user preferences with clear defaults
    print("\nSelect options for summary generation (press Enter for defaults):")
    
    print("\nAudience options:")
    print("1. management (default)")
    print("2. technical team") 
    print("3. general audience")
    audience_choice = input("Choose audience (1-3): ").strip()
    audience_map = {"1": "management", "2": "technical team", "3": "general audience"}
    audience = audience_map.get(audience_choice, "management")
    
    print("\nTone options:")
    print("1. neutral (default)")
    print("2. formal")
    print("3. concise")
    tone_choice = input("Choose tone (1-3): ").strip()
    tone_map = {"1": "neutral", "2": "formal", "3": "concise"}
    tone = tone_map.get(tone_choice, "neutral")
    
    print("\nBody style options:")
    print("1. key_findings - Key Insight + Evidence + Implication (default)")
    print("2. pros_cons - Alternating Pros/Cons with justification")
    print("3. risks_mitigations - Risk → Likelihood → Impact → Mitigation")
    print("4. metrics_trends - Metric → Current Value → Change → Driver")
    style_choice = input("Choose body style (1-4): ").strip()
    style_map = {"1": "key_findings", "2": "pros_cons", "3": "risks_mitigations", "4": "metrics_trends"}
    body_style = style_map.get(style_choice, "key_findings")
    
    print("\nStructure options:")
    num_subtopics_input = input("Number of subtopics (default: 3): ").strip()
    num_subtopics = int(num_subtopics_input) if num_subtopics_input.isdigit() and int(num_subtopics_input) > 0 else 3
    
    bullets_input = input("Bullets per subtopic (default: 3): ").strip()
    bullets_per_subtopic = int(bullets_input) if bullets_input.isdigit() and int(bullets_input) > 0 else 3

    # Step 1: Analyze themes (Part 2 integration)
    print("\nAnalyzing themes...")
    client = setup_gemini_client()
    theme_analysis = analyze_themes(report_text, client)
    suggested_subtopics = theme_analysis["suggested_subtopics"]

    # Step 2: Generate summary with user choices
    print(f"\nGenerating summary for {audience} with {tone} tone using {body_style} style...")
    print(f"Structure: {num_subtopics} subtopics with {bullets_per_subtopic} bullets each")
    summary = generate_multi_format_summary(
        report_text=report_text,
        audience=audience,
        tone=tone,
        num_subtopics=num_subtopics,
        bullets_per_subtopic=bullets_per_subtopic,
        suggested_subtopics=suggested_subtopics,
        body_style=body_style
    )
    
    print("\n" + "=" * 60)
    print("GENERATED SUMMARY")
    print("=" * 60)
    print(summary)
    
    # Save summary to file automatically (Markdown format as per assignment requirement)
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]  # Get PDF name without extension
    output_filename = f"{pdf_name}_{body_style}_summary.md"
    
    try:
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(f"# Multi-Format Summary Report\n\n")
            f.write(f"**Generated:** {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**Source:** {os.path.basename(pdf_path)}\n\n")
            f.write(f"**Audience:** {audience}\n\n")
            f.write(f"**Tone:** {tone}\n\n")
            f.write(f"**Body Style:** {body_style}\n\n")
            f.write(f"**Structure:** {num_subtopics} subtopics, {bullets_per_subtopic} bullets each\n\n")
            f.write("---\n\n")
            f.write(summary)
        
        print(f"\nSummary saved to: {output_filename}")
        
    except Exception as e:
        print(f"\nError saving file: {e}")