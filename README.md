# webcrawler

# iScraper – Intelligent University Web Crawler

`iScraper` is a Python-based web crawler that extracts structured admission-related data from university websites. It is designed to automate the retrieval of essential information such as admission requirements, application deadlines, available programs, and scholarships.

## Features

- Structured data extraction for:
  - Admission Requirements
  - Application Deadlines
  - Programs and Courses
  - Scholarships and Financial Aid
- Intelligent text processing using NLP (e.g., spaCy or rule-based extractors)
- Website crawling with BeautifulSoup or Selenium
- Data export options: CSV, JSON, or SQLite
- Optional dashboard interface with filtering, pagination, and export features

## Technologies Used

- Python 3.10+
- BeautifulSoup / Selenium
- pandas / numpy
- spaCy / re
- Flask (for web interface)
- SQLite / CSV / JSON (for data storage)

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/iScraper.git
cd iScraper
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the Web Crawler

```bash
python crawler/main.py --url https://www.exampleuniversity.edu
```

To extract a specific section (e.g., admission requirements):

```bash
python crawler/main.py --url https://www.exampleuniversity.edu/admissions --extract requirements
```

## Example Output

### Admission Requirements (CSV Format)

```
Degree,Year,Requirement1,Requirement2,Requirement3,Notes
BSc EEE,2025,Pass in 12th,Minimum 60% in Physics,IELTS 6.5,Math mandatory
```

### Scholarship Details (CSV Format)

```
Degree,Scholarship Name,Amount,Criteria
MSc CS,International Merit,2000 USD,GPA > 3.5
```

## Running the Dashboard (Optional)

If you are using the dashboard frontend:

```bash
cd dashboard/
flask run
```

Access the dashboard at `http://localhost:5000`

## Folder Structure

```
iScraper/
├── crawler/
│   ├── main.py
│   ├── extractors/
│   └── utils/
├── dashboard/
│   └── app.py
├── data/
│   └── output.csv
├── README.md
└── requirements.txt
```

## Future Extensions

- Integrate transformer-based models (e.g., BERT, RoBERTa) for advanced information extraction
- Add multilingual support for non-English university websites
- Incorporate RAG (Retrieval-Augmented Generation) for query-based information extraction
- Deploy crawler as a cloud service with periodic re-crawling and change detection

## License

This project is licensed under the MIT License.

## Contact

For questions, suggestions, or academic collaboration, contact [yourname@domain.edu] or open an issue on GitHub.
