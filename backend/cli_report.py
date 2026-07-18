import sys
import os
import json

# Ensure backend directory is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tools.pdf_reader import extract_text
from agents import proofreader, citation_checker, truth_checker, quality_checker, plagiarism_checker

def main():
    if len(sys.argv) < 2:
        print("Usage: python cli_report.py <path_to_pdf>")
        sys.exit(1)
        
    file_path = sys.argv[1]
    if not os.path.isfile(file_path):
        print(f"File not found: {file_path}")
        sys.exit(1)
        
    print(f"Reading {file_path}...")
    text = extract_text(file_path)
    
    if text.startswith("[Error extracting PDF"):
        print(text)
        sys.exit(1)
        
    print("Running Proofreader...")
    proof_res = proofreader.run(text)
    
    print("Running Citation Checker...")
    cite_res = citation_checker.run(text)
    
    print("Running Plagiarism Checker...")
    plag_res = plagiarism_checker.run(text)
    
    print("Running Truth Checker...")
    truth_res = truth_checker.run(text, proof_res, cite_res)
    
    print("Running Quality Gate...")
    qual_res = quality_checker.run(text, proof_res, cite_res, truth_res, plag_res)
    
    report = {
        "Quality Assessment": qual_res,
        "Citation Verification": cite_res,
        "Plagiarism Scan": plag_res
    }
    
    print("\n" + "="*50)
    print("FINAL CLI REPORT")
    print("="*50)
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
