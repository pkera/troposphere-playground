import logging
from troposphere import Output, Ref, Export, AWS_REGION, Join, GetAtt
from troposphere.ec2 import (
    Route,
    VPCGatewayAttachment,
    RouteTable,
    VPC,
    EIP,
    NatGateway,
    InternetGateway,
    Subnet,
    SubnetRouteTableAssociation,
    NetworkAclEntry,
    NetworkAcl,
    SubnetNetworkAclAssociation,
)

from constants import VPC_CIDR
from stacks.base_stack import BaseStack
from utils import tag


class VpcStack(BaseStack):
    """The networking stack containing the VPC and other basic network resources"""

    def __init__(self, template_name: str, template_description: str):
        super().__init__(template_name, template_description)

    def synth(self) -> str:
        logging.info(f"Synthesizing {self.template_name} stack...")
        # Create VPC
        vpc = self.template.add_resource(
            VPC(
                "VPC",
                CidrBlock=VPC_CIDR,
                EnableDnsSupport="true",
                EnableDnsHostnames="true",
                Tags=tag("vpc"),
            )
        )
        # Create Internet Gateway
        internet_gateway = self.template.add_resource(
            InternetGateway("InternetGateway", Tags=tag("ig"))
        )
        # Attach Internet Gateway to the VPC
        self.template.add_resource(
            VPCGatewayAttachment(
                "AttachGateway", VpcId=Ref(vpc), InternetGatewayId=Ref(internet_gateway)
            )
        )

        # Public Route Table
        public_route_table = self.template.add_resource(
            RouteTable(
                "MainRouteTable", VpcId=Ref(vpc), Tags=tag("public-route-table-main")
            )
        )
        # Create default route 0.0.0.0/0 in the Public RouteTable
        public_route = self.template.add_resource(
            Route(
                "PublicRoute",
                DependsOn="AttachGateway",
                GatewayId=Ref(internet_gateway),
                DestinationCidrBlock="0.0.0.0/0",
                RouteTableId=Ref(public_route_table),
            )
        )

        # Load Balancer Subnets
        alb_subnet_1 = self.template.add_resource(
            Subnet(
                "LoadBalancer1",
                CidrBlock="10.0.0.0/28",
                VpcId=Ref(vpc),
                Tags=tag("alb-subnet-1"),
                AvailabilityZone=Join("", [Ref(AWS_REGION), "a"]),
            )
        )
        alb_subnet_2 = self.template.add_resource(
            Subnet(
                "LoadBalancer2",
                CidrBlock="10.0.0.16/28",
                VpcId=Ref(vpc),
                Tags=tag("alb-subnet-2"),
                AvailabilityZone=Join("", [Ref(AWS_REGION), "b"]),
            )
        )

        # Private subnet
        fargate_subnet = self.template.add_resource(
            Subnet(
                "FargateSubnet",
                CidrBlock="10.0.0.128/28",
                VpcId=Ref(vpc),
                Tags=tag("fargate-subnet"),
                AvailabilityZone=Join("", [Ref(AWS_REGION), "a"]),
            )
        )

        # NAT
        nat_ip = self.template.add_resource(
            EIP(
                "NatIp",
                Domain="vpc",
            )
        )

        nat_gateway = self.template.add_resource(
            NatGateway(
                "NatGateway",
                AllocationId=GetAtt(nat_ip, "AllocationId"),
                SubnetId=Ref(alb_subnet_1),
            )
        )

        # Private route table
        private_route_table = self.template.add_resource(
            RouteTable(
                "PrivateRouteTable",
                VpcId=Ref(vpc),
            )
        )
        private_nat_route = self.template.add_resource(
            Route(
                "PrivateNatRoute",
                RouteTableId=Ref(private_route_table),
                DestinationCidrBlock="0.0.0.0/0",
                NatGatewayId=Ref(nat_gateway),
            )
        )

        self.template.add_resource(
            SubnetRouteTableAssociation(
                "PrivateRouteTableAssociation",
                SubnetId=Ref(fargate_subnet),
                RouteTableId=Ref(private_route_table),
            )
        )

        # Associate ALB subnets with the public RouteTable
        self.template.add_resource(
            SubnetRouteTableAssociation(
                "AlbSubnet1RouteTableAssociation",
                SubnetId=Ref(alb_subnet_1),
                RouteTableId=Ref(public_route_table),
            )
        )
        self.template.add_resource(
            SubnetRouteTableAssociation(
                "AlbSubnet2RouteTableAssociation",
                SubnetId=Ref(alb_subnet_2),
                RouteTableId=Ref(public_route_table),
            )
        )

        public_network_acl = self.template.add_resource(
            NetworkAcl(
                "PublicNetworkAcl",
                VpcId=Ref(vpc),
                Tags=tag("acl"),
            )
        )

        inbound_public_network_acl_entry = self.template.add_resource(
            NetworkAclEntry(
                "InboundHTTPNetworkAclEntry",
                NetworkAclId=Ref(public_network_acl),
                RuleNumber="100",
                Protocol="-1",
                Egress="false",
                RuleAction="allow",
                CidrBlock="0.0.0.0/0",
            )
        )

        self.template.add_resource(
            SubnetNetworkAclAssociation(
                "PublicSubnet1NetworkAclAssociation",
                SubnetId=Ref(alb_subnet_1),
                NetworkAclId=Ref(public_network_acl),
            )
        )
        self.template.add_resource(
            SubnetNetworkAclAssociation(
                "PublicSubnet2NetworkAclAssociation",
                SubnetId=Ref(alb_subnet_2),
                NetworkAclId=Ref(public_network_acl),
            )
        )

        self.template.add_output(
            [
                Output(
                    "TropoVPC",
                    Description="The Tropo service VPC",
                    Value=Ref(vpc),
                    Export=Export("TropoVPC"),
                ),
                Output(
                    "TropoAlbSubnet1",
                    Description="The Tropo service AlbSubnet1",
                    Value=Ref(alb_subnet_1),
                    Export=Export("TropoAlbSubnet1"),
                ),
                Output(
                    "TropoAlbSubnet2",
                    Description="The Tropo service AlbSubnet1",
                    Value=Ref(alb_subnet_2),
                    Export=Export("TropoAlbSubnet2"),
                ),
                Output(
                    "TropoPrivateSubnet",
                    Description="The Tropo service PrivateSubnet",
                    Value=Ref(fargate_subnet),
                    Export=Export("TropoPrivateSubnet"),
                ),
            ]
        )

        return self.template.to_yaml()
