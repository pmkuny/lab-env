import pulumi
from networking import c_KubernetesNetwork
from helper import *

# Variables separated by underscore
# Constants CAPITALIZED
# Pulumi Components prepended by c_

logger = config_logging()

'''
Dictionary Order is important for networking creation
0 - VPC 
1 - Public Subnet for NAT GW
2-* - Remaining needed subnets
'''
KUBERNETES_NETWORK_CIDR= {
    "vpc": "10.0.0.0/21",
    "public_subnet_1": "10.0.5.0/28",
    "control_plane_a": "10.0.1.0/27",
    "control_plane_b": "10.0.2.0/27",
    "worker_plane_a": "10.0.3.0/25",
    "worker_plane_b": "10.0.4.0/25"
}

config = pulumi.Config()
print(logger.info(f'Global Tags: {get_global_tags()}'))

kubernetes_network = c_KubernetesNetwork("dev-cluster-network",KUBERNETES_NETWORK_CIDR)

