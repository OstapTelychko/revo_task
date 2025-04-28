from __future__ import annotations
from typing import TYPE_CHECKING
import json

from django.test import TestCase
from django.core.management import call_command
from unittest.mock import patch, MagicMock
from requests.exceptions import ConnectionError, RequestException, Timeout, HTTPError

from revo.exceptions import APIException
from revo.management.commands.download_revo_data import Command

# if TYPE_CHECKING:
#     from unittest.mock import MagicMock



class TestDownloadRevoDataCommand(TestCase):
    """Test the download_revo_data command."""

    def setUp(self):
        """Set up the test case."""
        self.command = Command()
        self.valid_data = [
            {"id": 1, "name": "Item 1", "active": True, "tags": ["tag1", "tag2"]},
            {"id": 2, "name": "Item 2", "active": False, "tags": ["tag3"]},
        ]
    
    @patch('revo.management.commands.download_revo_data.requests.get')
    def test_1_connection_error(self, mock_get:MagicMock):
        """Test connection error."""

        mock_get.side_effect = ConnectionError("Connection error")
        with self.assertRaises(APIException, msg="APIException haven't been raised although Connection error occured") as context:
            call_command('download_revo_data')
        self.assertEqual(str(context.exception), "Connection error", "Connection error not raised")
    

    @patch('revo.management.commands.download_revo_data.requests.get')
    def test_2_http_error_status(self, mock_get:MagicMock):
        """Test HTTP error status."""

        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = HTTPError("HTTP error")
        mock_get.return_value = mock_response

        with self.assertRaises(APIException, msg="APIException haven't been raised although HTTP error occured") as context:
            call_command('download_revo_data')
        self.assertEqual(str(context.exception), "HTTP error", "HTTP error not raised")
    

    @patch('revo.management.commands.download_revo_data.requests.get')
    def test_3_invalid_data(self, mock_get:MagicMock):
        """Test invalid data."""

        invalid_data = {"invalid": "data"}

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = invalid_data
        mock_get.return_value = mock_response

        with self.assertRaises(ValueError) as context:
            call_command('download_revo_data')
        self.assertEqual(str(context.exception), f"API response have to be list-like not {type(invalid_data)}", "Invalid data have been sent but exception not raised")
    

    @patch('revo.management.commands.download_revo_data.requests.get')
    def test_4_valid_data(self, mock_get:MagicMock):
        """Test valid data."""

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = self.valid_data
        mock_get.return_value = mock_response

        with patch('revo.management.commands.download_revo_data.logger') as mock_logger:
            call_command('download_revo_data')
            self.assertTrue(mock_logger.info.called, "Logger info was not called")
            for item in self.valid_data:
                mock_logger.info.assert_any_call(json.dumps(item, indent=4))