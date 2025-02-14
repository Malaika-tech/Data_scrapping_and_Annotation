import os
import fitz  # PyMuPDF for extracting text from PDFs
import google.generativeai as genai  # Google's Generative AI package
import mysql.connector
import time

# Define Gemini API Key 
GEMINI_API_KEY = "GEMINI_API_KEY"

# Define paper categories
CATEGORIES = ["Machine Learning", "Computer Vision", "Natural Language Processing", 
              "Robotics", "Data Science"]

# Database connection
db_connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",  
    database="dataScience"
)
cursor = db_connection.cursor()

def is_valid_pdf(pdf_path):
    """Check if the PDF file is valid before processing."""
    try:
        with open(pdf_path, "rb") as f:
            f.seek(-10, 2)  # Read the last 10 bytes of the file
            if b"%%EOF" not in f.read():
                return False
        return True
    except:
        return False

def extract_text_from_pdf(pdf_path):
    """Extracts text (title + abstract) from the first page of a PDF."""
    try:
        doc = fitz.open(pdf_path)
        text = doc[0].get_text("text")  # Extract text from the first page
        doc.close()

        lines = text.split("\n")
        title = lines[0] if len(lines) > 0 else "Unknown Title"
        abstract = " ".join(lines[1:5]) if len(lines) > 4 else "No abstract available"

        return title.strip(), abstract.strip()
    
    except Exception as e:
        print(f"Error processing PDF {pdf_path}: {e}")
        return None, None  # Skip processing this file

def classify_paper(title, abstract):
    """Classifies the paper using Gemini's API."""
    prompt = f"""
    You are an AI model that classifies research papers into one of the following categories:
    {', '.join(CATEGORIES)}.

    Paper Title: {title}
    Abstract: {abstract}

    Classify this paper into one category from the list above and return only the category name.
    """

    try:
        # Initialize Gemini API
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-pro')

        # Enforce API rate limit
        time.sleep(10)  # Delay of 10 seconds to avoid exceeding limits

        response = model.generate_content(prompt)

        if response and response.text:
            return response.text.strip()
        else:
            return "Uncategorized"

    except Exception as e:
        print(f"Gemini API Error: {e}")
        return "Uncategorized"

def paper_exists(title):
    """Check if a paper with the given title already exists in the database."""
    cursor.execute("SELECT COUNT(*) FROM papers WHERE title = %s", (title,))
    result = cursor.fetchone()
    return result[0] > 0  # Returns True if the paper exists

def process_pdfs(pdf_folder):
    """Processes all PDFs in the given folder and classifies them."""
    for filename in os.listdir(pdf_folder):
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(pdf_folder, filename)

            # Skip corrupt or unreadable PDFs
            if not is_valid_pdf(pdf_path):
                print(f"Skipping corrupt PDF: {filename}")
                continue

            title, abstract = extract_text_from_pdf(pdf_path)
            if title is None or abstract is None:
                continue  # Skip if extraction failed

            # Check if the paper already exists in the database
            if paper_exists(title):
                print(f"Skipping duplicate paper: {title}")
                continue

            category = classify_paper(title, abstract)

            if category != "Uncategorized":  # Only insert valid results
                cursor.execute("INSERT INTO papers (title, category) VALUES (%s, %s)", (title, category))
                db_connection.commit()
                print(f"Processed: {title} - {category}")
            else:
                print(f"Skipped: {title} due to classification issue.")

if __name__ == "__main__":
    pdf_folder = r"C:\Users\HP\DataScience\nips_papers_2019"
    process_pdfs(pdf_folder)

    db_connection.close()
    print("Annotation process completed and data saved to the database.")
