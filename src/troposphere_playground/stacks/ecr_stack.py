import logging
from stacks.base_stack import BaseStack
from troposphere import ImportValue, Join, Ref, AWS_ACCOUNT_ID, AWS_REGION, Output
from troposphere.ecr import Repository


import awacs.ecr as ecr
from awacs.aws import Allow, AWSPrincipal, PolicyDocument, Statement


from constants import ECR_REPO_NAME
from utils import tag


class EcrStack(BaseStack):
    def __init__(self, template_name: str, template_description: str):
        super().__init__(template_name, template_description)

        self.vpc = ImportValue("TropoVPC")
        self.public_subnet_1 = ImportValue("TropoPublicSubnet1")
        self.public_subnet_2 = ImportValue("TropoPublicSubnet2")
        self.private_subnet = ImportValue("TropoPrivateSubnet")

    def synth(self) -> str:
        logging.info(f"Synthesizing {self.template_name} stack...")

        repository = self.template.add_resource(
            Repository(
                "TropoRepository",
                RepositoryName=ECR_REPO_NAME,
                RepositoryPolicyText=PolicyDocument(
                    Version="2008-10-17",
                    Statement=[
                        Statement(
                            Sid="AllowPushPull",
                            Effect=Allow,
                            Principal=AWSPrincipal(
                                [
                                    Join(
                                        "",
                                        [
                                            "arn:aws:iam::",
                                            Ref(AWS_ACCOUNT_ID),
                                            ":root",
                                        ],
                                    )
                                ]
                            ),
                            Action=[
                                ecr.GetDownloadUrlForLayer,
                                ecr.BatchGetImage,
                                ecr.BatchCheckLayerAvailability,
                                ecr.PutImage,
                                ecr.InitiateLayerUpload,
                                ecr.UploadLayerPart,
                                ecr.CompleteLayerUpload,
                            ],
                        ),
                    ],
                ),
                Tags=tag("ecr"),
            )
        )

        # Output ECR repository URL
        self.template.add_output(
            Output(
                "RepositoryURL",
                Description="The docker repository URL",
                Value=Join(
                    "",
                    [
                        Ref(AWS_ACCOUNT_ID),
                        ".dkr.ecr.",
                        Ref(AWS_REGION),
                        ".amazonaws.com/",
                        Ref(repository),
                    ],
                ),
            )
        )

        return self.template.to_yaml()
