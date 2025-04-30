from __future__ import annotations
from typing import TypeAlias, List, Dict, Sequence, Mapping
import logging
import json

from django.core.management.base import BaseCommand
import requests
from requests.exceptions import ConnectionError, RequestException, Timeout, HTTPError

from revo.exceptions import APIException


CommandArgs = Sequence[str]  # Positional arguments in Django commands are strings
CommandKwargs = Mapping[str, str|bool|int|None]

ID: TypeAlias = int
NAME: TypeAlias = str
ACTIVE: TypeAlias = bool
TAGS: TypeAlias = List[str]
REVO_DATA: TypeAlias = List[Dict[str, ID|NAME|ACTIVE|TAGS]]

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    """Command to download Revo data."""

    help = "Download Revo data"
    api_url = "https://api.revo.com/data"


    @staticmethod
    def validate_data(data:REVO_DATA) -> None:
        """Validate the data structure.

            Arguments
            ---------
                data (List[Dict[str, ID|NAME|ACTIVE|TAGS]]): The data to validate.
        """

        errors:list[Exception] = []

        if not isinstance(data, List):
            raise ValueError(f"API response have to be list-like not {type(data)}")
                
        for item in data:
            if not isinstance(item, Dict):
                errors.append(ValueError(f"API response item must be a dict-like not {type(item)}"))

            required_fields = ["id", "name", "active", "tags"]
            missing_fields = [field for field in required_fields if field not in item]
            if missing_fields:
                errors.append(ValueError(f"Missing fields in API response item {', '.join(missing_fields)}"))
            
            if not isinstance(item["id"], ID):
                errors.append(ValueError(f"Field 'id' must be of type {ID} not {type(item['id'])}"))
            
            if not isinstance(item["name"], NAME):
                errors.append(ValueError(f"Field 'name' must be of type {NAME} not {type(item['name'])}"))
            
            if not isinstance(item["active"], ACTIVE):
                errors.append(ValueError(f"Field 'active' must be of type {ACTIVE} not {type(item['active'])}"))
            
            if not isinstance(item["tags"], List):
                errors.append(ValueError(f"Field 'tags' must be list-like not {type(item['tags'])}"))
            
            if not all(isinstance(tag, str) for tag in item["tags"]): #type:ignore[union-attr] #I already check if item["tags"] is a list
                errors.append(ValueError(f"Field 'tags' must be a list of strings not {[type(tag) for tag in item['tags']]}")) #type:ignore[union-attr] #I already check if item["tags"] is a list

            if errors:
                raise ExceptionGroup("API response validation errors", errors)


    def handle(self, *args:CommandArgs, **kwargs:CommandKwargs)-> str:
        "Handle the command."

        try:
            logger.info(f"Starting download of Revo data url {self.api_url}")
            response = requests.get(self.api_url, timeout=10)
            response.raise_for_status() 

            data = response.json()
            self.validate_data(data)

            logger.info("Successfully downloaded Revo data:")
            for item in data:
                logger.info(json.dumps(item, indent=4))
            return str(data)

        except ConnectionError as e:
            logger.error(f"Connection error: {e}")
            raise APIException("Connection error") from e
        
        except Timeout as e:
            logger.error(f"Timeout error: {e}")
            raise APIException("Timeout error") from e
        
        except HTTPError as e:
            logger.error(f"HTTP error: {e}")
            raise APIException("HTTP error") from e

        except RequestException as e:
            logger.error(f"Request error: {e}")
            raise APIException("Request error") from e

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            raise APIException("JSON decode error") from e

