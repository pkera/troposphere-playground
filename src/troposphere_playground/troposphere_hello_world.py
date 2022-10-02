import troposphere.ec2 as ec2
from troposphere import Ref, Template, Tags, GetAtt
from troposphere.ec2 import Route, VPCGatewayAttachment, SubnetRouteTableAssociation, \
    Subnet, RouteTable, VPC, SubnetNetworkAclAssociation, EIP, InternetGateway

from src.constants import AZ_PUBLIC_NUMBER, REGION, TAG_PREFIX, VPC_CIDR


cf_template = Template()
cf_template.set_version('2010-09-09')
cf_template.set_description('AWS CloudFormation VPC Custom Template')

ref_stack_id = Ref('AWS::StackId')
ref_region = Ref('AWS::Region')
ref_stack_name = Ref('AWS::StackName')



# Create VPC
VPC = cf_template.add_resource(
    VPC(
        'VPC',
        CidrBlock=VPC_CIDR,
        Tags=Tags(
            Application=ref_stack_id,
            Name=f"{TAG_PREFIX}-vpc"
        )))
# Create Internet Gateway
internetGateway = cf_template.add_resource(
    InternetGateway(
        'InternetGateway',
        Tags=Tags(
            Application=ref_stack_id,
            Name=f"{TAG_PREFIX}-ig"
        )))
# Attach Internet Gateway to the VPC
gatewayAttachment = cf_template.add_resource(
    VPCGatewayAttachment(
        'AttachGateway',
        VpcId=Ref(VPC),
        InternetGatewayId=Ref(internetGateway)))
# Create default Main Public RouteTable
mainRouteTable = cf_template.add_resource(
    RouteTable(
        'MainRouteTable',
        VpcId=Ref(VPC),
        Tags=Tags(
            Application=ref_stack_id,
            Name=f"{TAG_PREFIX}-PublicRouteTable-Main"
        )))
# Create default route 0.0.0.0/0 in the Public RouteTable
route = cf_template.add_resource(
    Route(
        'Route',
        DependsOn='AttachGateway',
        GatewayId=Ref('InternetGateway'),
        DestinationCidrBlock='0.0.0.0/0',
        RouteTableId=Ref(mainRouteTable),
    ))

# Create Public Subnets and associate them with MainRouteTable
for i in range(AZ_PUBLIC_NUMBER):
    if i == 0:
        AZ = f"{REGION}"+'a'
    elif i == 1:
        AZ = input_aws_region+'b'
    elif i == 2:
        AZ = input_aws_region+'c'
    input_number_of_public_subnets = int(input(
        'How many PUBLIC subnets in ' + AZ + ' AZ you need?: '))  # user input request
    while input_number_of_public_subnets > 0:
        subnet_logical_id = 'PubSubnet' + \
            str(input_number_of_public_subnets) + AZ.replace("-", "")
        input_number_of_public_subnets -= 1
        input_pub_subnet_cidr = input(
            'Public Subnet ' + subnet_logical_id + ' desired CIDR (ex. 10.0.1.0/24): ')  # user input request

        # Create Public Subnet
        subnet = cf_template.add_resource(
            Subnet(
                subnet_logical_id,
                CidrBlock=input_pub_subnet_cidr,
                VpcId=Ref(VPC),
                AvailabilityZone=AZ,
                Tags=Tags(
                    Application=ref_stack_id,
                    Name=input_tag + '-' + subnet_logical_id
                )))

        # Create RouteTable Association (MAIN)
        UniqueSubnetRouteTableAssociation = 'SubnetRouteTableAssociation' + subnet_logical_id
        subnetRouteTableAssociation = cf_template.add_resource(
            SubnetRouteTableAssociation(
                UniqueSubnetRouteTableAssociation,
                SubnetId=Ref(subnet),
                RouteTableId=Ref(mainRouteTable),
            ))

# user input request
input_nat_gateway_option = int(input('''Please choose option "1" or "2".
    - Option#1: create only one NAT Gateway per each AZ
    - Option#2: create a separate NAT Gateway for each private subnet: '''))

# Create Private Subnets
for i in range(input_pri_az_amount):
    if i == 0:
        AZ = input_aws_region+'a'
    elif i == 1:
        AZ = input_aws_region+'b'
    elif i == 2:
        AZ = input_aws_region+'c'
    # Create Public Subnet for NATGateway
    subnet_logical_id = 'PubSubnetNAT' + AZ.replace("-", "")
    input_pub_subnet_cidr = input('Public Subnet ' + subnet_logical_id +
                                  ' desired CIDR (ex. 10.0.100.0/28): ')  # user input request
    public_nat_net = cf_template.add_resource(
        Subnet(
            subnet_logical_id,
            CidrBlock=input_pub_subnet_cidr,
            VpcId=Ref(VPC),
            AvailabilityZone=AZ,
            Tags=Tags(
                Application=ref_stack_id,
                Name=input_tag + '-' + subnet_logical_id
            )))

    # Create RouteTable Association (MAIN)
    UniqueSubnetRouteTableAssociation = 'SubnetRouteTableAssociation' + subnet_logical_id
    subnetRouteTableAssociation = cf_template.add_resource(
        SubnetRouteTableAssociation(
            UniqueSubnetRouteTableAssociation,
            SubnetId=Ref(public_nat_net),
            RouteTableId=Ref(mainRouteTable),
        ))

    # Create NAT Gateway - one per each AZ
    if input_nat_gateway_option == 1:

        # Allocate EIP
        UniqueNatEipName = 'NatEip' + AZ.replace("-", "")
        nat_eip = cf_template.add_resource(ec2.EIP(
            UniqueNatEipName,
            Domain="vpc",
        ))

        # Create NAT Gateway
        UniqueNatGatewayName = 'NAT' + AZ.replace("-", "")
        nat = cf_template.add_resource(ec2.NatGateway(
            UniqueNatGatewayName,
            AllocationId=GetAtt(nat_eip, 'AllocationId'),
            SubnetId=Ref(public_nat_net),
            Tags=Tags(
                Application=ref_stack_id,
                Name=input_tag + '-' + UniqueNatGatewayName
            )))

    input_number_of_private_subnets = int(input(
        'How many PRIVATE subnets in ' + AZ + ' AZ you need?: '))  # user input request

    while input_number_of_private_subnets > 0:
        subnet_logical_id = 'PriSubnet' + \
            str(input_number_of_private_subnets) + AZ.replace("-", "")
        input_number_of_private_subnets -= 1
        input_pri_subnet_cidr = input(
            'Private Subnet ' + subnet_logical_id + ' desired CIDR (ex. 10.0.10.0/24): ')

        # Create Private Subnet
        subnet = cf_template.add_resource(
            Subnet(
                subnet_logical_id,
                CidrBlock=input_pri_subnet_cidr,
                VpcId=Ref(VPC),
                AvailabilityZone=AZ,
                Tags=Tags(
                    Application=ref_stack_id,
                    Name=input_tag + '-' + subnet_logical_id
                )))

        # Create RouteTable for each private subnet
        UniqueRouteTableName = 'PrivateRouteTable' + subnet_logical_id
        privateRouteTable = cf_template.add_resource(
            RouteTable(
                UniqueRouteTableName,
                VpcId=Ref(VPC),
                Tags=Tags(
                    Application=ref_stack_id,
                    Name=input_tag + '-' + UniqueRouteTableName
                )))

        # Create RouteTable Association for each private subnet
        UniqueSubnetRouteTableAssociation = 'SubnetRouteTableAssociation' + subnet_logical_id
        subnetRouteTableAssociation = cf_template.add_resource(
            SubnetRouteTableAssociation(
                UniqueSubnetRouteTableAssociation,
                SubnetId=Ref(subnet),
                RouteTableId=Ref(privateRouteTable),
            ))

        if input_nat_gateway_option == 1:

            # Add default route NAT
            UniqueNatRouteName = 'NATRoute' + subnet_logical_id
            route = cf_template.add_resource(
                Route(
                    UniqueNatRouteName,
                    DependsOn=UniqueNatGatewayName,
                    NatGatewayId=Ref(UniqueNatGatewayName),
                    DestinationCidrBlock='0.0.0.0/0',
                    RouteTableId=Ref(UniqueRouteTableName),
                ))

        elif input_nat_gateway_option == 2:

            # Allocate EIP for new NAT Gateway
            UniqueNatEipName = 'NatEip' + subnet_logical_id
            nat_eip = cf_template.add_resource(ec2.EIP(
                UniqueNatEipName,
                Domain="vpc",
            ))

            # Create NAT Gateway for each private subnet
            UniqueNatGatewayName = 'NATGateway' + subnet_logical_id
            nat = cf_template.add_resource(ec2.NatGateway(
                UniqueNatGatewayName,
                AllocationId=GetAtt(nat_eip, 'AllocationId'),
                SubnetId=Ref(public_nat_net),
                Tags=Tags(
                    Application=ref_stack_id,
                    Name=input_tag + '-' + UniqueNatGatewayName
                )))

            # Add default route NAT
            UniqueNatRouteName = 'NATRoute' + subnet_logical_id
            route = cf_template.add_resource(
                Route(
                    UniqueNatRouteName,
                    DependsOn=UniqueNatGatewayName,
                    NatGatewayId=Ref(UniqueNatGatewayName),
                    DestinationCidrBlock='0.0.0.0/0',
                    RouteTableId=Ref(UniqueRouteTableName),
                ))

# Finally, write the template to a file
with open('learncf-ec2.yaml', 'w') as f:
    f.write(cf_template.to_yaml())
