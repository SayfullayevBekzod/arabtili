import pdfplumber

def peek_pdf_plumber(filename):
    with pdfplumber.open(filename) as pdf:
        print(f"Total pages: {len(pdf.pages)}")
        for i in range(min(15, len(pdf.pages))):
            page = pdf.pages[i]
            print(f"--- Page {i+1} ---")
            text = page.extract_text(layout=True)
            print(text)
            print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    peek_pdf_plumber("d:/Work/arab/arabtili.pdf")
