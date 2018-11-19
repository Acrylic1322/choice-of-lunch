import abc


class DataStore(metaclass=abc.ABCMeta):
    """
    Datastore which has eating places
    """

    @abc.abstractmethod
    def add_eating_place(self, place_name):
        pass

    @abc.abstractmethod
    def del_eating_place(self, place_name):
        pass

    @abc.abstractmethod
    def get_list_of_eating_place(self):
        pass

    @abc.abstractmethod
    def get_suggestion(self):
        pass

    @abc.abstractmethod
    def is_place_exists(self, place_name):
        pass
