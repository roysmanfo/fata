import logging
from mitmproxy import http


class Inspector:
    """
    Base class for all inspectors.
    """

    def __init__(self, aggressive: bool = False):
        """
        :param aggressive: If true, will also modify the response to remove ads, otherwise just detect them.
        """

        self.name = self.__class__.__name__
        """The name of the inspector."""

        self.url_patterns = []
        """List of URL regex patterns that trigger an inspection from this Inspector."""

        self.current_flow: http.HTTPFlow = None
        """The current flow being inspected."""
        
        self.aggressive = aggressive
        """If true, will also modify the response to remove ads, otherwise just detect them."""

        self.logger = logging.getLogger("fata")

    def inspect_request(self, flow: http.HTTPFlow) -> bool:
        """
        Inspect the given data.

        :param flow: The flow to inspect.
        :return: True if the data contains ads, False otherwise.
        """
        raise NotImplementedError("Subclasses must implement this method.")
