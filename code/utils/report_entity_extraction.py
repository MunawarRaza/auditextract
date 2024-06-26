import boto3
import spacy
from dataclasses import dataclass, field
from datetime import datetime
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource
from spacy.language import Language
from utils.get_keywords import find_matches_in_keywords, get_keywords_table


@dataclass
class ReportEntityExtraction:
    data: dict
    nlp_model: Language
    keywords_dict: dict
    report_name: str = "Report_entity_extraction"

    def extract_entities(self, content: str) -> str:
        """Process a string and extracts general entities

        Args:
            content (str): The input text to process.

        Returns:
            str: The processed text.
        """

        entities_full = self.nlp_model(content)

        return entities_full

    def transform_data(self) -> dict:
        """Transforms a dictionary of pages with paragraphs into a new structured format.

        Returns:
            dict: A JSON dictionary of the transformed data structure.
        """
        transformed_data = {}
        try:
            page_dict = {"timestamp": datetime.now().isoformat(), "response": []}
            for page_id, page_content in self.data.items():
                for paragraph in page_content["paragraphs"]:
                    # Extract Entities from Paragraph
                    matches_dict = find_matches_in_keywords(
                        search_string=str(paragraph["text"]), keywords_dict=self.keywords_dict
                    )

                    if len(matches_dict) > 0:
                        # Update with found entities
                        for entities in matches_dict:
                            paragraph_info = {
                                "page_id": page_content["page_id"],
                                "paragraph_table_number": paragraph["id"],
                                "entity_name": entities["entity_name"],
                                "entity_text": entities["keyword"],
                                "metrics": [{entities["metric"]: entities["keyword"]}],
                            }
                        # paragraph_info['entity_text'] = self.extract_entities(paragraph['text'])
                        page_dict["response"].append(paragraph_info)

            transformed_data[f"{self.report_name}"] = page_dict
        except Exception as e:
            print(f"Error occurred while transforming data: {e}")
        return transformed_data


if __name__ == "__main__":
    import logging

    logging.info("Connecting to DynamoDB...")
    KEYWORDS_TABLE_NAME = "quality_luminous_audit_keywords"
    REGION_NAME = "us-east-1"
    dynamodb_: DynamoDBServiceResource = boto3.resource(
        "dynamodb",
        region_name=REGION_NAME,
    )

    data = {
        "51": {
            "page_id": 51,
            "tables": {
                "T-1": '{"0":{"0":"\\"Part Number:\\"","1":"\\"Cylinder Number:\\"","2":"\\"Laboratory:\\"","3":"\\"Analysis Date:\\"","4":"\\"Lot Number:\\""},"1":{"0":"\\"X03NI93P15AC062\\"","1":"\\"CC310187\\"","2":"\\"ASG Chicago IL\\"","3":"\\"Dec 10, 2015\\"","4":"\\"54-124528151-1\\""}}',
                "T-2": '{"0":{"0":"\\"Reference Number:\\"","1":"\\"Cylinder Volume:\\"","2":"\\"Cylinder Pressure:\\"","3":"\\"Valve Outlet:\\""},"1":{"0":"\\"54-124528151-1\\"","1":"\\"144.9 CF\\"","2":"\\"2015 PSIG\\"","3":"\\"590\\""}}',
                "T-3": '{"0":{"0":"\\"Component\\"","1":"\\"ETHYLENE\\"","2":"\\"OXYGEN NITROGEN\\""},"1":{"0":"\\"Requested Concentration\\"","1":"\\"100.0 PPM\\"","2":"\\"6.000 % Balance\\""},"2":{"0":"\\"Actual Concentration (Mole %)\\"","1":"\\"101.2 PPM\\"","2":"\\"5.990 %\\""},"3":{"0":"\\"Analytical Uncertainty\\"","1":"\\"+\\/-1%\\"","2":"\\"+\\/-0.02% abs\\""}}',
            },
            "paragraphs": [
                {
                    "id": "P-1",
                    "text": "A Waukesha L 7042 GSI engine located at Carmen and operated by Eagle Chief Midstream, LLC was tested for emissions of Carbon Monoxide (CO), Oxides of Nitrogen (NOx) and Volatile Organic Compounds (VOCs). The test was conducted on 6/13/2016 by Colton Wood with Great Plains Analytical Services, Inc. All quality assurance and quality control tests were within acceptable tolerances. The engine is a natural gas fired engine rated at 1232 brake horse power (bhp) at 1000 RPM. The engine was operating at 1133 bhp and 920 RPM which is 92% of maximum engine load during the test. The engine was running at the maximum load available at the test site. The fuel flow rate was 10178 scf/hr during the test.",
                },
                {"id": "P-2", "text": "Grade of Product: PRIMARY STANDARD"},
            ],
        }
    }
    nlp = spacy.load("en_core_web_sm")

    logging.info("Getting Keywords Data...")
    keywords_data = get_keywords_table(dynamodb=dynamodb_, table_name=KEYWORDS_TABLE_NAME)
    print(keywords_data)

    # Creating an instance of DataTransformer and using it to transform data
    transformer = ReportEntityExtraction(data=data, nlp_model=nlp, keywords_dict=keywords_data)
    json_output = transformer.transform_data()
    print(json_output)
