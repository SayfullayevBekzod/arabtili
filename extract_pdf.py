from pypdf import PdfReader

def extract_to_file(pdf_path, output_path):
    reader = PdfReader(pdf_path)
    with open(output_path, 'w', encoding='utf-8') as f:
        for page in reader.pages:
            f.write(page.extract_text())
            f.write("\n\n" + "="*50 + "\n\n")

if __name__ == "__main__":
    extract_to_file("d:/Work/arab/arabtili.pdf", "d:/Work/arab/extracted_pdf.txt")
