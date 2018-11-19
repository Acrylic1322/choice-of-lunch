import abc


class DataStore(metaclass=abc.ABCMeta):
    """
    Datastore which has eating places
    """

    @abc.abstractmethod
    def add_eating_place(self, place_name):
        """
        Args:
            place_name (str): The name of eating place which will be tried to add.
        Returns:
        """
        pass

    @abc.abstractmethod
    def del_eating_place(self, place_name):
        """
        Args:
            place_name (str): The name of eating place which will be tried to delete.
        Returns:
        """
        pass

    @abc.abstractmethod
    def get_list_of_eating_place(self):
        """
        Returns:
            array: list of registered eating place.
        """
        pass

    @abc.abstractmethod
    def get_suggestion(self):
        """
        Returns:
        """
        pass

    @abc.abstractmethod
    def is_place_exists(self, place_name):
        """
        Args:
            place_name (str): The name of eating place which will be tried to search.
        Returns:
            bool: if the place_name is in the table, return true
        """
