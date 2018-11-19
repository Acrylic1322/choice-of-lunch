import random
import logging

import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError

from data_store import DataStore
from data_operation_error import DataOperationError

TABLE_NAME = "Lunch"
KEY_LUNCH_NAME = "name"
NUM_SUGGESTION = 3

RETURN_TEXT = {
    "ALREADY_REGISTERED": "The place is registered already"
}


class DynamoDB(DataStore):
    """
    Datastore which has eating places
    """

    def __init__(self):
        self.dynamo_db = boto3.resource("dynamodb")
        self.table = self.dynamo_db.Table(TABLE_NAME)
        self.logger = logging.getLogger()

    def add_eating_place(self, place_name):
        """
        Args:
            place_name (str): The name of eating place which will be tried to add.
        Returns:
            bool
        """
        try:
            if self.is_place_exists(place_name):
                raise DataOperationError("")

            self.table.put_item(
                Item={
                    KEY_LUNCH_NAME: place_name
                }
            )

        except ClientError as error:
            self.logger.error(error)
            raise DataOperationError("")

        return True

    def del_eating_place(self, place_name):
        """
        Args:
            place_name (str): The name of eating place which will be tried to delete.
        Returns:
            bool
        """
        try:
            if not self.is_place_exists(place_name):
                raise DataOperationError("")

            self.table.delete_item(
                Key={
                    KEY_LUNCH_NAME: place_name
                }
            )
        except ClientError as error:
            self.logger.error(error)
            raise DataOperationError("")
        return True

    def get_list_of_eating_place(self):
        """
        Returns:
            Array
        """
        try:
            response = self.table.scan()
            places = []
            for item in response["Items"]:
                places.append(item[KEY_LUNCH_NAME])
        except ClientError as error:
            self.logger.error(error)
            raise DataOperationError("")
        return places

    def get_suggestion(self):
        """
        Returns:
            array: list of suggested eating place.
        """
        eating_places = self.get_list_of_eating_place()
        suggestions = []
        for i in range(NUM_SUGGESTION):
            if not eating_places:
                break
            index = random.randrange(len(eating_places))
            suggestions.append(eating_places[index])
            del eating_places[index]
        return suggestions

    def is_place_exists(self, place_name):
        """
        Args:
            place_name (str): The name of eating place which will be tried to search.
        Returns:
            bool: if the place_name is in the table, return true
        """

        response = self.table.get_item(
            Key={
                KEY_LUNCH_NAME: place_name
            }
        )

        if "Item" in response:
            return True
        return False
