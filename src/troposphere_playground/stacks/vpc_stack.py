import logging
from troposphere import Ref, Template, Tags, GetAtt
from troposphere.ec2 import Route, VPCGatewayAttachment, SubnetRouteTableAssociation, \
    Subnet, RouteTable, VPC, SubnetNetworkAclAssociation, EIP, InternetGateway

from constants import AZ_PUBLIC_NUMBER, REGION, STACK_ID, TAG_PREFIX, VPC_CIDR
from stacks.base_stack import BaseStack


class VpcStack(BaseStack):
    """The networking stack containing the VPC and other basic network resources
    """
    def __init__(self, template_name: str, template_description: str):
        """The constructor

        Args:
            template_name (str): the name of the template that will be used for the output filename
            template_description (str): a short description
        """
        super().__init__(template_name, template_description)

    def synth(self) -> str:
        logging.info(f"Synthesizing {self.template_name} stack...")
        # Create VPC
        vpc = self.template.add_resource(
            VPC(
                'VPC',
                CidrBlock=VPC_CIDR,
                Tags=Tags(
                    Application=STACK_ID,
                    Name=f"{TAG_PREFIX}-vpc"
                )))
        # Create Internet Gateway
        internetGateway = self.template.add_resource(
            InternetGateway(
                'InternetGateway',
                Tags=Tags(
                    Application=STACK_ID,
                    Name=f"{TAG_PREFIX}-ig"
                )))
        # Attach Internet Gateway to the VPC
        gatewayAttachment = self.template.add_resource(
            VPCGatewayAttachment(
                'AttachGateway',
                VpcId=Ref(vpc),
                InternetGatewayId=Ref(internetGateway)))
        # Create default Main Public RouteTable
        mainRouteTable = self.template.add_resource(
            RouteTable(
                'MainRouteTable',
                VpcId=Ref(vpc),
                Tags=Tags(
                    Application=STACK_ID,
                    Name=f"{TAG_PREFIX}-PublicRouteTable-Main"
                )))
        # Create default route 0.0.0.0/0 in the Public RouteTable
        route = self.template.add_resource(
            Route(
                'Route',
                DependsOn='AttachGateway',
                GatewayId=Ref(internetGateway),
                DestinationCidrBlock='0.0.0.0/0',
                RouteTableId=Ref(mainRouteTable),
            ))

        return self.template.to_yaml()
