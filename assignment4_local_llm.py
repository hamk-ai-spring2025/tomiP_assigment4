import argparse
import fitz  # PyMuPDF
import pytesseract
from pdf2image import convert_from_path
from openai import OpenAI
import os
import requests
from bs4 import BeautifulSoup
import docx
import csv

# OCR path for Windows
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Extract text from PDF using OCR
def extract_text_from_pdf_ocr(filepath):
    text = ""
    try:
        images = convert_from_path(filepath)
        for image in images:
            text += pytesseract.image_to_string(image)
    except Exception as e:
        print(f"Error during OCR: {e}")
    return text

# Extract text from DOCX
def extract_text_from_docx(filepath):
    try:
        doc = docx.Document(filepath)
        return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        print(f"Error reading DOCX: {e}")
        return ""

# Extract text from CSV
def extract_text_from_csv(filepath):
    try:
        text = ""
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                text += ", ".join(row) + "\n"
        return text
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return ""

# Extract text from URL
def extract_text_from_url(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        return soup.get_text()
    except Exception as e:
        print(f"Error fetching URL: {e}")
        return ""

# Extract text from TXT file
def extract_text_from_txt(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"Error reading TXT: {e}")
        return ""

# Parse command line arguments
parser = argparse.ArgumentParser(description="Summarize various file types using local LLM")
parser.add_argument("files", nargs="+", help="Input files or URLs")
parser.add_argument("-q", "--query", type=str, default="Summarize this", help="Prompt for the LLM")
parser.add_argument("-f", "--file", type=str, help="Optional: write output to file")
args = parser.parse_args()

# Combine text from all sources
combined_text = ""
for source in args.files:
    if source.startswith("http"):
        combined_text += extract_text_from_url(source) + "\n"
    elif source.lower().endswith(".pdf"):
        combined_text += extract_text_from_pdf_ocr(source) + "\n"
    elif source.lower().endswith(".docx"):
        combined_text += extract_text_from_docx(source) + "\n"
    elif source.lower().endswith(".csv"):
        combined_text += extract_text_from_csv(source) + "\n"
    elif source.lower().endswith(".txt"):
        combined_text += extract_text_from_txt(source) + "\n"
    else:
        print(f"Unsupported file type: {source}")

if not combined_text.strip():
    print("No readable text found in provided inputs. Try another file or check formatting.")
    exit()

# Send data to local LLM
client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")
print("\nSending data to local LLM...\n")

completion = client.chat.completions.create(
    model="mistral-7b-instruct-v0.1",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": f"{args.query}\n\n{combined_text[:3000]}"}
    ],
    temperature=0.7,
    max_tokens=1000,
    stream=False
)

response = completion.choices[0].message.content

if args.file:
    with open(args.file, "w", encoding="utf-8") as f:
        f.write(response)
    print(f"\nResponse written to {args.file}")
else:
    print("\nLLM Response:\n")
    print(response)
