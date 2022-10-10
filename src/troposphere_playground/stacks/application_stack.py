import logging
from troposphere import ImportValue

from stacks.base_stack import BaseStack
from constructs.fargate_construct import FargateConstruct, FargateConstructProps
from constructs.alb_construct import AlbConstruct, AlbConstructProps


class AppStack(BaseStack):
    def __init__(self, template_name: str, template_description: str):
        super().__init__(template_name, template_description)

        self.vpc = ImportValue("TropoVPC")
        self.alb_subnet_1 = ImportValue("TropoAlbSubnet1")
        self.alb_subnet_2 = ImportValue("TropoAlbSubnet2")
        self.private_subnet = ImportValue("TropoPrivateSubnet")

    def synth(self) -> str:
        logging.info(f"Synthesizing {self.template_name} stack...")

        alb = AlbConstruct(
            template=self.template,
            props=AlbConstructProps(
                vpc=self.vpc,
                alb_subnet_1=self.alb_subnet_1,
                alb_subnet_2=self.alb_subnet_2,
            ),
        )

        fargate = FargateConstruct(
            template=self.template,
            props=FargateConstructProps(
                vpc=self.vpc,
                fargate_subnet=self.private_subnet,
                alb_target_group=alb.fargate_target_group,
                alb_security_group=alb.alb_security_group,
            ),
        )

        return self.template.to_yaml()
