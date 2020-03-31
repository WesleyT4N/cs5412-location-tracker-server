import pprint

class BaseModel:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __repr__(self):
        return "<{}: \n {}\n>".format(
            self.__class__.__name__,
            pprint.pformat(self.__dict__),
        )
