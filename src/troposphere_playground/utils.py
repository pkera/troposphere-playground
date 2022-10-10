from pathlib import Path

from constants import EXPORT_FOLDER
from troposphere import Tags, AWS_STACK_ID, Ref
from constants import TAG_PREFIX


def export_cf_template_to_file(template_filename: str, template_content: str) -> str:
    """Creates a YAML CF template file in the EXPORT_FOLDER folder

    Args:
        template_filename (str): the template filename
        template_content (str): the template content from the synthesization

    Returns:
        str: the template absolute filepath
    """
    (Path().cwd() / Path(EXPORT_FOLDER)).mkdir(parents=True, exist_ok=True)
    template_file = Path().cwd() / EXPORT_FOLDER / Path(template_filename)
    if not template_file.exists():
        template_file.touch()

    template_file.write_text(template_content)
    return template_file


def tag(tag_name: str) -> Tags:
    return Tags(Application=Ref(AWS_STACK_ID), Name=f"{TAG_PREFIX}-{tag_name}")
