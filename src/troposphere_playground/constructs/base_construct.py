from dataclasses import dataclass
from troposphere import Template


@dataclass
class BaseConstructProps:
    pass


class BaseConstruct:
    """The base construct to be used as a boilerplate"""

    def __init__(self, template: Template, props: BaseConstructProps) -> None:
        """The constructor

        Args:
            template (Template): the troposphere template object
        """
        self.props = props
        self.template = template
        self.construct_definition()

    def construct_definition():
        pass
