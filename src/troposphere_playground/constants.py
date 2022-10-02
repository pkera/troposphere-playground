from troposphere import Ref

### Stack data
STACK_ID = Ref('AWS::StackId')
STACK_NAME = Ref('AWS::StackName')
REGION = Ref('AWS::Region')

### General
# Resources tag prefix
TAG_PREFIX = "tropo"

### VPC
VPC_CIDR = "10.0.0.0/16"
# Number of AZs per public subnet (1-3)
AZ_PUBLIC_NUMBER = 1
# Number of AZs per private subnet (1-3)
AZ_PRIVATE_NUMBER = 1