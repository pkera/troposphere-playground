"""Synthesizes YAML Cloudformation templates for each stack
"""

import logging
from constants import TAG_PREFIX
from stacks.vpc_stack import VpcStack
from stacks.base_stack import BaseStack
from stacks.application_stack import AppStack
from stacks.ecr_stack import EcrStack


STACKS: BaseStack = [
    VpcStack(
        template_name=f"{TAG_PREFIX}-vpc",
        template_description="Base network infrastructure",
    ),
    EcrStack(template_name=f"{TAG_PREFIX}-ecr", template_description="ECR Repository"),
    AppStack(
        template_name=f"{TAG_PREFIX}-app",
        template_description="Application infrastructure",
    ),
]


def synthesize_stacks():
    for stack in STACKS:
        stack.export()


def main():
    """Entry point for the application"""
    logging.basicConfig(level=logging.DEBUG)
    try:
        synthesize_stacks()
    except Exception as e:
        logging.exception(f"Stack YAML generation failed: {e}")


if __name__ == "__main__":
    main()
