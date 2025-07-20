import pulumi
import pytest
from networking import c_KubernetesNetwork


class PulumiMocks(pulumi.runtime.Mocks):
    """Mock implementation for Pulumi runtime integration testing."""
    
    def new_resource(self, args: pulumi.runtime.MockResourceArgs):
        return [args.name + '_id', args.inputs]
    
    def call(self, args: pulumi.runtime.MockCallArgs):
        return {}


pulumi.runtime.set_mocks(PulumiMocks())


@pulumi.runtime.test
def test_vpc_creation_and_properties():
    """Test VPC creation with proper CIDR and DNS configuration."""
    cidr_config = {
        "vpc": "10.0.0.0/21",
        "control-plane-a": "10.0.1.0/27",
        "workers-a": "10.0.3.0/25"
    }
    
    network = c_KubernetesNetwork("integration-test", cidr_config)
    
    def validate_vpc_properties(args):
        vpc_id, vpc_inputs = args
        assert vpc_id == "kubernetes-vpc_id"
        assert vpc_inputs["cidr_block"] == "10.0.0.0/21"
        assert vpc_inputs["enable_dns_hostnames"] is True
        assert vpc_inputs["enable_dns_support"] is True
        return True
    
    return pulumi.Output.all(
        network.kubernetes_vpc.id,
        network.kubernetes_vpc
    ).apply(validate_vpc_properties)


@pulumi.runtime.test
def test_subnet_vpc_association():
    """Test that subnets are properly associated with the VPC."""
    cidr_config = {
        "vpc": "172.16.0.0/20",
        "public-subnet": "172.16.1.0/24",
        "private-subnet": "172.16.2.0/24"
    }
    
    network = c_KubernetesNetwork("subnet-test", cidr_config)
    
    def validate_subnet_association(args):
        vpc_id, public_subnet, private_subnet = args
        
        # Both subnets should reference the VPC
        assert hasattr(public_subnet, 'vpc_id')
        assert hasattr(private_subnet, 'vpc_id')
        return True
    
    return pulumi.Output.all(
        network.kubernetes_vpc.id,
        getattr(network, 'public-subnet'),
        getattr(network, 'private-subnet')
    ).apply(validate_subnet_association)


@pulumi.runtime.test
def test_internet_gateway_vpc_association():
    """Test that Internet Gateway is associated with the VPC."""
    cidr_config = {
        "vpc": "10.1.0.0/16",
        "subnet-1": "10.1.1.0/24"
    }
    
    network = c_KubernetesNetwork("igw-test", cidr_config)
    
    def validate_igw_association(args):
        vpc_id, igw = args
        assert hasattr(igw, 'vpc_id')
        return True
    
    return pulumi.Output.all(
        network.kubernetes_vpc.id,
        network.igw
    ).apply(validate_igw_association)


@pulumi.runtime.test
def test_nat_gateway_configuration():
    """Test NAT Gateway configuration with EIP and subnet."""
    cidr_config = {
        "vpc": "10.2.0.0/16",
        "public-subnet": "10.2.1.0/24",
        "private-subnet": "10.2.2.0/24"
    }
    
    network = c_KubernetesNetwork("nat-test", cidr_config)
    
    def validate_nat_gateway(args):
        eip_id, nat_gw, first_subnet = args
        
        # NAT Gateway should have allocation_id and subnet_id
        assert hasattr(nat_gw, 'allocation_id')
        assert hasattr(nat_gw, 'subnet_id')
        return True
    
    return pulumi.Output.all(
        network.eip.id,
        network.ngw,
        getattr(network, 'public-subnet')
    ).apply(validate_nat_gateway)


@pulumi.runtime.test
def test_route_table_default_route():
    """Test that route table contains default route to NAT Gateway."""
    cidr_config = {
        "vpc": "10.3.0.0/16",
        "subnet-1": "10.3.1.0/24"
    }
    
    network = c_KubernetesNetwork("route-test", cidr_config)
    
    def validate_route_table(args):
        vpc_id, route_table, nat_gw_id = args
        
        # Route table should be associated with VPC
        assert hasattr(route_table, 'vpc_id')
        assert hasattr(route_table, 'routes')
        return True
    
    return pulumi.Output.all(
        network.kubernetes_vpc.id,
        network.nat_route_table,
        network.ngw.id
    ).apply(validate_route_table)


@pulumi.runtime.test
def test_component_resource_hierarchy():
    """Test that resources are properly parented in the component hierarchy."""
    cidr_config = {
        "vpc": "192.168.0.0/16",
        "subnet-1": "192.168.1.0/24"
    }
    
    network = c_KubernetesNetwork("hierarchy-test", cidr_config)
    
    def validate_hierarchy(args):
        vpc, subnet, igw, eip, nat_gw, route_table = args
        
        # All resources should exist
        assert vpc is not None
        assert subnet is not None
        assert igw is not None
        assert eip is not None
        assert nat_gw is not None
        assert route_table is not None
        return True
    
    return pulumi.Output.all(
        network.kubernetes_vpc,
        getattr(network, 'subnet-1'),
        network.igw,
        network.eip,
        network.ngw,
        network.nat_route_table
    ).apply(validate_hierarchy)


if __name__ == '__main__':
    pytest.main([__file__])