import json
from dataclasses import dataclass, field
from typing import List, Dict, Union

@dataclass
class Metric:
    # As metrics are dynamic and change their keys, we will use a dictionary to represent them
    # TODO: replace metrics by values directly
    metric: Dict[str, Union[str, float, int]]

@dataclass
class Entity:
    paragraph_table_number: str
    entity_name: str
    entity_text: str
    metrics: List[Metric]

@dataclass
class PageNumber:
    # The key here would represents the page number in the file
    entities: Dict[str, List[Entity]]

@dataclass
class Document:
    timestamp: str
    response: List[PageNumber]

@dataclass
class AuditRetrieval:
    documents: Dict[str, Document]
