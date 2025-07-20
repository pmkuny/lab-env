import pulumi 
import pulumi_aws as aws
from helper import *

class c_KubernetesNetwork(pulumi.ComponentResource):
    def __init__(self, name: str, MY_CIDR: dict, opts: pulumi.ResourceOptions = None):
        super().__init__("custom:networking:KubernetesNetwork", name, {}, opts)

        self.kubernetes_vpc = aws.ec2.Vpc("kubernetes-vpc",
            cidr_block=MY_CIDR["vpc"],
            enable_dns_hostnames=True,
            enable_dns_support=True,
            opts=pulumi.ResourceOptions(parent=self))
        
        # Iterate through subnets in the dictionary, skipping the VPC one, this allows dynamic creation of subnets
        # setattr() is used here because self.k is treated as a string literal, instead of interpolated key,value in loop.
        for k,v in list(MY_CIDR.items())[1:]:
            setattr(self, k, aws.ec2.Subnet(
                k,
                vpc_id=self.kubernetes_vpc.id,
                cidr_block=v,
                opts=pulumi.ResourceOptions(parent=self.kubernetes_vpc)
               )
            )

        # Private Subnet -> NAT GW -> IGW - Traffic egress to Internet

        # IGW
        self.igw = aws.ec2.InternetGateway(
            "public-igw",
            vpc_id=self.kubernetes_vpc.id
        )

        # EIP
        self.eip = aws.ec2.Eip(
            "natgw-eip",
            opts=pulumi.ResourceOptions(parent=self)
        )

        # NAT GW
        self.ngw = aws.ec2.NatGateway(
            "ngw",
            allocation_id=self.eip.id,
            subnet_id=getattr(self, list(MY_CIDR.keys())[1]).id,
            opts=pulumi.ResourceOptions(parent=self)
        )

        # Route Table for routing Internet traffic in private subnets to IGW
        self.nat_route_table = aws.ec2.RouteTable(
            "nat-route-table",
            vpc_id=self.kubernetes_vpc.id,
            routes=[
                aws.ec2.RouteTableRouteArgs(
                    cidr_block="0.0.0.0/0",
                    gateway_id=self.ngw.id
                )
            ],
            opts=pulumi.ResourceOptions(parent=self)
        )