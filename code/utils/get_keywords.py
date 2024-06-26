import boto3
from botocore.exceptions import BotoCoreError, ClientError
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource


def get_keywords_table(dynamodb: DynamoDBServiceResource, table_name: str):
    """
    Retrieves data from a DynamoDB table and stores it in a dictionary.

    Args:
    table_name (str): The name of the DynamoDB table to read.

    Returns:
    dict: A dictionary with the data from the DynamoDB table where the keys are 'entity_name'
          and the values are dictionaries containing 'metric' and 'keywords'.

    Raises:
    Exception: If any error occurs during the DynamoDB operation.
    """
    table = dynamodb.Table(table_name)
    # print(table)
    try:
        # Scan the table
        # print(dynamodb)
        response = table.scan()

        # Initialize dictionary to hold the data
        data_dict = {}

        # Process each item in the response
        for item in response.get("Items", []):
            # print(item)
            entity_name = item["entity_name"]
            metric = item["metric"]
            # Extract keywords from the complex structure
            keywords = [keyword for keyword in item["keywords"]]

            # Store the data in the dictionary
            data_dict[entity_name] = {"metric": metric, "keywords": keywords}

        return data_dict

    except (BotoCoreError, ClientError) as error:
        # Handle potential errors
        raise Exception(f"An error occurred accessing DynamoDB: {error}")


def find_matches_in_keywords(search_string: str, keywords_dict: dict):
    """Searches for a given string in the keywords of each entry in a DynamoDB table and returns matches.

    Args:
        table_name (str): The name of the DynamoDB table.
        search_string (str): The string to search for within the keywords.

    Returns:
        list: A list of dictionaries, where each dictionary contains 'entity_name', 'metric', and 'keyword' that matched the search string.

    Raises:
        Exception: Propagates exceptions from the DynamoDB read operation.
    """

    # List to hold all matches
    matches = []

    # Convert search text to lower case for case insensitive search
    search_text_lower = search_string.lower()
    # Search each keyword in the search text
    for entity_name, details in keywords_dict.items():
        result = None
        for keyword in details["keywords"]:
            if keyword.lower() in search_text_lower:
                # If keyword is found in the text, append the match to the results list
                result = {
                    "entity_name": entity_name,
                    "metric": details["metric"],
                    "keyword": keyword,
                }
            if result:
                matches.append(result)

    return matches


# Usage example
if __name__ == "__main__":
    import logging

    logging.info("Connecting to DynamoDB...")
    KEYWORDS_TABLE_NAME = "quality_luminous_audit_keywords"
    REGION_NAME = "us-east-1"
    dynamodb_: DynamoDBServiceResource = boto3.resource(
        "dynamodb",
        region_name=REGION_NAME,
    )

    logging.info("Getting Keywords Data...")
    keywords_data = get_keywords_table(dynamodb=dynamodb_, table_name=KEYWORDS_TABLE_NAME)
    print(keywords_data)

    logging.info("Find entity matches...")
    paragraph = "A Waukesha L 7042 GSI engine located at Carmen and operated by Eagle Chief Midstream, LLC was tested for emissions of Carbon Monoxide (CO), Oxides of Nitrogen (NOx) and Volatile Organic Compounds (VOCs). The test was conducted on 6/13/2016 by Colton Wood with Great Plains Analytical Services, Inc. All quality assurance and quality control tests were within acceptable tolerances. The engine is a natural gas fired engine rated at 1232 brake horse power (bhp) at 1000 RPM. The engine was operating at 1133 bhp and 920 RPM which is 92% of maximum engine load during the test. The engine was running at the maximum load available at the test site. The fuel flow rate was 10178 scf/hr during the test."
    matches_data = find_matches_in_keywords(
        search_string=paragraph,
        keywords_dict=keywords_data,
    )

    print(matches_data)
