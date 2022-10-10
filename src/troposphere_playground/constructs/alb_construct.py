from dataclasses import dataclass
from troposphere import Join, Ref, Template, ImportValue, GetAtt, Output
from troposphere.ec2 import SecurityGroupRule, SecurityGroup
import troposphere.elasticloadbalancingv2 as elb

from constructs.base_construct import BaseConstruct, BaseConstructProps
from utils import tag


@dataclass
class AlbConstructProps(BaseConstructProps):
    vpc: ImportValue
    alb_subnet_1: ImportValue
    alb_subnet_2: ImportValue


class AlbConstruct(BaseConstruct):
    def __init__(self, template: Template, props: AlbConstructProps):
        super().__init__(template, props)

    def construct_definition(self):
        self.alb_security_group = self.template.add_resource(
            SecurityGroup(
                "ALBSecurityGroup",
                GroupDescription="ALB Security Group",
                VpcId=self.props.vpc,
                SecurityGroupIngress=[
                    SecurityGroupRule(
                        IpProtocol="tcp",
                        FromPort="80",
                        ToPort="80",
                        CidrIp="0.0.0.0/0",
                    ),
                ],
            )
        )

        self.alb = self.template.add_resource(
            elb.LoadBalancer(
                "ApplicationLB",
                Name="ApplicationLB",
                Scheme="internet-facing",
                Subnets=[self.props.alb_subnet_1, self.props.alb_subnet_2],
                SecurityGroups=[Ref(self.alb_security_group)],
                Tags=tag("alb"),
            )
        )

        self.fargate_target_group = self.template.add_resource(
            elb.TargetGroup(
                "FargateTargetGroup",
                HealthCheckIntervalSeconds="30",
                HealthCheckProtocol="HTTP",
                HealthCheckPath="/",
                HealthCheckTimeoutSeconds="10",
                HealthyThresholdCount="4",
                Matcher=elb.Matcher(HttpCode="200"),
                Name="FargateTarget",
                Port="80",
                Protocol="HTTP",
                UnhealthyThresholdCount="3",
                TargetType="ip",
                VpcId=self.props.vpc,
                DependsOn="ApplicationLB",
            )
        )

        Listener = self.template.add_resource(
            elb.Listener(
                "FargateListener",
                Port="80",
                Protocol="HTTP",
                LoadBalancerArn=Ref(self.alb),
                DefaultActions=[
                    elb.Action(
                        Type="forward", TargetGroupArn=Ref(self.fargate_target_group)
                    )
                ],
                DependsOn="ApplicationLB",
            )
        )

        self.template.add_output(
            Output(
                "AlbDns",
                Description="ALB DNS",
                Value=Join("", ["http://", GetAtt(self.alb, "DNSName")]),
            )
        )
