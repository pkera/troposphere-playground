"""Synthesizes YAML Cloudformation templates for each stack
"""

import logging
from constants import TAG_PREFIX
from stacks.alb_stack import AlbStack

from utils import export_cf_template_to_file


def synthesize_stacks():
    vpc_stack = AlbStack(
        template_name=f"{TAG_PREFIX}-vpc",
        template_description="Base network infrastructure"
    )
    vpc_stack.export()

def main():
    """Entry point for the application
    """
    logging.basicConfig(level=logging.DEBUG)
    try:
        synthesize_stacks()
    except Exception as e:
        logging.exception(f"Stack YAML generation failed: {e}")


if __name__ == "__main__":
    main()
