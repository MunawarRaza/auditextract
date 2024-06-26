from dataclasses import dataclass, field
import pandas as pd
import json

@dataclass
class PageContent:
    """Represents the content of a single page in the PDF."""
    page_id: int
    tables: dict = field(default_factory=dict)
    paragraphs: list = field(default_factory=list)

    def add_paragraph(self, paragraph_text: str):
        """Adds a paragraph to the page."""
        self.paragraphs.append({'id': f'P-{len(self.paragraphs) + 1}', 'text': paragraph_text})

    def add_table(self, table_id: int, table_data: pd.DataFrame):
        """Serializes and adds a table to the page."""
        self.tables[f'T-{table_id + 1}'] = table_data.to_json()

@dataclass
class ReportProcessor:
    """Processes Page content from a dictionary."""
    original_content: str

    def process_content(self) -> dict:
        """Processes the extracted content from the PDF."""
        output = {}
        content = json.loads(self.original_content)
        for page_number, page_data in content.items():
            try:
                page_id = page_data['page_id']
                page_content = PageContent(page_id)
                # Process tables
                for table in page_data.get('tables', []):
                    df = pd.DataFrame([x.split(';') for x in table['records']])
                    page_content.add_table(table['table_id'], df)
                # Process lines into paragraphs
                paragraph = ""
                for line in page_data['lines']:
                    if len(line) < 100 and not line.endswith('.'):
                        if paragraph:  # Save previous paragraph if exists
                            page_content.add_paragraph(paragraph)
                            paragraph = ""
                        page_content.add_paragraph(line)
                    else:
                        paragraph += " " + line if paragraph else line
                if paragraph:  # Catch any remaining paragraph text
                    page_content.add_paragraph(paragraph)
                output[page_id] = {"page_id": page_id, "tables": page_content.tables, "paragraphs": page_content.paragraphs}
            except Exception as e:
                print(f"Error processing page {page_number}: {e}")
        return output

# Usage Example         
if __name__ == "__main__":
    
    from report_s3_utils import get_report_from_s3
    from pydantic import BaseModel
     
    # Get file from S3
    class AuditReportRequest(BaseModel):
        bucket_name: str
        organization_id: str
        file_key: str
        
    request = AuditReportRequest(
        bucket_name='luminous-files',
        organization_id='1',
        file_key='Eagle Chief Midstream, LLC Carmen 1.2 JJJJ 6-14-16.pdf.json'
    )
    
    report_object_dict = get_report_from_s3(request)
    
    # Process File
    report_processor = ReportProcessor(original_content=report_object_dict["data"])
    processed_data = report_processor.process_content()
    
    print(len(processed_data))