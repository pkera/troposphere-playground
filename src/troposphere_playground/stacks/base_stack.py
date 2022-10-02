import logging
from troposphere import Template

from utils import export_cf_template_to_file


class BaseStack:
    """The base stack to be used as a boilerplate
    """
    def __init__(self, template_name, template_description) -> None:
        self.template_name = template_name
        self.template = Template()
        self.template.set_version('2010-09-09')
        self.template.set_description(template_description)

    def synth(self) -> str:
        """Synthesizes the YAML CF template's contents using Troposphere

        Returns:
            str: the YAML template as a string
        """
        pass

    def export(self):
        """Exports the YAML CF template content to a file, named after the template's name
        """
        logging.info(f"Exporting {self.template_name} stack...")
        pathname = export_cf_template_to_file(
            template_content=self.synth(),
            template_filename=f"{self.template_name}.yaml",
        )
        logging.info(f"Exported {self.template_name} stack to {pathname}")
