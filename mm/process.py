from typing import List, Optional
from .data_sample import DataSample

def _data_sample_construction_decorator(func):
    """Decorator that handles the convertion of process output to DataSample."""

    def wrapper(*args, **kwargs):
        
        # Detecting the input data sample latest's timestamp
        timestamps = [x.time for x in args[1:]]
        latest_timestamp = max(timestamps)

        # Apply the forward function of the process
        rt = func(*args, **kwargs)

        # Only if there is a return item do we enclose it in a DataSample
        if type(rt) != type(None):

            # Construct a data sample around the results
            data_sample = DataSample(
                args[0].name, # the class is the first argument
                latest_timestamp,
                rt
            )

            # Return the sample instead of the results
            return data_sample
    return wrapper

class MetaProcess(type):
    """

    Information: https://stackoverflow.com/questions/57104276/python-subclass-method-to-inherit-decorator-from-superclass-method
    """

    def __new__(cls, name, bases, attr):
        # Replace each function with
        # a print statement of the function name
        # followed by running the computation with the provided args and returning the computation result
        attr["forward"] = _data_sample_construction_decorator(attr["forward"])

        return super(MetaProcess, cls).__new__(cls, name, bases, attr)

class Process(metaclass=MetaProcess):
    """Generic class that compartmentalizes computational steps for a datastream."""

    def __init__(self, name: str, inputs: List[str]):
        self.name = name
        self.inputs = inputs

    def __repr__(self):
        return f"{self.name}"
    
    def forward(self, x: DataSample): 
        """A step where an data sample is used as input for the process.

        Args:
            x: a sample (of any type) in to the process.

        Raises:
            NotImplementedError: forward method needs to be overwritten.
        """
        raise NotImplementedError("forward method needs to be implemented.")

