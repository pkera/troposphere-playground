from pathlib import Path

EXPORT_FOLDER = "dist"

def export_cf_template_to_file(template_filename: str, template_content: str) -> str:
    """Creates a YAML CF template file in the EXPORT_FOLDER folder

    Args:
        template_filename (str): the template filename
        template_content (str): the template content from the synthesization

    Returns:
        str: the template absolute filepath
    """
    template_file = Path().cwd() / Path(EXPORT_FOLDER) / Path(template_filename)
    if not template_file.exists():
        template_file.touch()
    
    template_file.write_text(template_content)
    return template_file
    