from dataclasses import dataclass
from troposphere import GetAtt, Ref, Template, ImportValue
from troposphere.ecs import (
    Cluster,
    ContainerDefinition,
    LoadBalancer,
    PortMapping,
    Service,
    TaskDefinition,
    NetworkConfiguration,
    AwsvpcConfiguration,
)
from troposphere.ec2 import SecurityGroup, SecurityGroupRule
from troposphere.iam import Role, PolicyType
from troposphere.elasticloadbalancingv2 import TargetGroup

from constructs.base_construct import BaseConstruct, BaseConstructProps
from utils import tag


@dataclass
class FargateConstructProps(BaseConstructProps):
    vpc: ImportValue
    fargate_subnet: ImportValue
    alb_target_group: TargetGroup
    alb_security_group: SecurityGroup


class FargateConstruct(BaseConstruct):
    def __init__(self, template: Template, props: FargateConstructProps):
        super().__init__(template, props)

    def construct_definition(self):
        cluster = self.template.add_resource(Cluster("TropoCluster"))

        # Create the Task Role
        task_role = self.template.add_resource(
            Role(
                "TaskRole",
                AssumeRolePolicyDocument={
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {"Service": ["ecs-tasks.amazonaws.com"]},
                            "Action": ["sts:AssumeRole"],
                        }
                    ]
                },
            )
        )

        # Create the Task Execution Role
        task_execution_role = self.template.add_resource(
            Role(
                "TaskExecutionRole",
                AssumeRolePolicyDocument={
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {"Service": ["ecs-tasks.amazonaws.com"]},
                            "Action": ["sts:AssumeRole"],
                        }
                    ]
                },
            )
        )

        # Create the Fargate Execution Policy (access to ECR and CW Logs)
        fargate_execution_policy = self.template.add_resource(
            PolicyType(
                "FargateExecutionPolicy",
                PolicyName="fargate-execution",
                PolicyDocument={
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Action": [
                                "ecr:GetAuthorizationToken",
                                "ecr:BatchCheckLayerAvailability",
                                "ecr:GetDownloadUrlForLayer",
                                "ecr:BatchGetImage",
                                "ecr:GetDownloadUrlForLayer",
                                "ecr:PutImage",
                                "ecr:InitiateLayerUpload",
                                "ecr:UploadLayerPart",
                                "ecr:CompleteLayerUpload",
                                "logs:CreateLogStream",
                                "logs:PutLogEvents",
                            ],
                            "Resource": ["*"],
                            "Effect": "Allow",
                        },
                    ],
                },
                Roles=[Ref(task_execution_role)],
            )
        )

        fargate_security_group = self.template.add_resource(
            SecurityGroup(
                "FargateSecurityGroup",
                GroupDescription="Fargate ALB Security Group",
                VpcId=self.props.vpc,
                SecurityGroupIngress=[
                    SecurityGroupRule(
                        IpProtocol="tcp",
                        FromPort="80",
                        ToPort="80",
                        SourceSecurityGroupId=GetAtt(
                            self.props.alb_security_group, "GroupId"
                        ),
                    ),
                ],
            )
        )

        task_definition = self.template.add_resource(
            TaskDefinition(
                "TropoServer",
                RequiresCompatibilities=["FARGATE"],
                Cpu="256",
                Memory="512",
                NetworkMode="awsvpc",
                TaskRoleArn=Ref(task_role),
                ExecutionRoleArn=Ref(task_execution_role),
                ContainerDefinitions=[
                    ContainerDefinition(
                        Name="tropo-app",
                        Image="public.ecr.aws/docker/library/httpd:latest",
                        PortMappings=[PortMapping(ContainerPort=80)],
                        EntryPoint=["sh", "-c"],
                        Command=[
                            "/bin/sh -c \"echo 'Welcome to the Cloud Team' >  /usr/local/apache2/htdocs/index.html && httpd-foreground\""
                        ],
                    )
                ],
                Tags=tag("fargate-task-definition"),
            )
        )

        fargate_service = self.template.add_resource(
            Service(
                "TropoService",
                Cluster=Ref(cluster),
                DesiredCount=1,
                TaskDefinition=Ref(task_definition),
                LaunchType="FARGATE",
                LoadBalancers=[
                    LoadBalancer(
                        ContainerName="tropo-app",
                        ContainerPort=80,
                        TargetGroupArn=Ref(self.props.alb_target_group),
                    )
                ],
                NetworkConfiguration=NetworkConfiguration(
                    AwsvpcConfiguration=AwsvpcConfiguration(
                        AssignPublicIp="ENABLED",
                        Subnets=[self.props.fargate_subnet],
                        SecurityGroups=[Ref(fargate_security_group)],
                    )
                ),
                Tags=tag("fargate-service"),
                DependsOn="FargateListener",
            )
        )
