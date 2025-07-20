import unittest
from unittest.mock import patch, MagicMock, call
import pulumi
from networking import c_KubernetesNetwork


class PulumiMocks(pulumi.runtime.Mocks):
    """Mock implementation for Pulumi runtime testing."""
    
    def new_resource(self, args: pulumi.runtime.MockResourceArgs):
        return [args.name + '_id', args.inputs]
    
    def call(self, args: pulumi.runtime.MockCallArgs):
        return {}


class TestKubernetesNetwork(unittest.TestCase):
    """Test suite for KubernetesNetwork component."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        pulumi.runtime.set_mocks(PulumiMocks())
        self.test_cidr_config = {
            "vpc": "10.0.0.0/21",
            "control-plane-a": "10.0.1.0/27",
            "control-plane-b": "10.0.2.0/27",
            "workers-a": "10.0.3.0/25",
            "workers-b": "10.0.4.0/25"
        }
    
    @patch('pulumi_aws.ec2.RouteTable')
    @patch('pulumi_aws.ec2.NatGateway')
    @patch('pulumi_aws.ec2.Eip')
    @patch('pulumi_aws.ec2.InternetGateway')
    @patch('pulumi_aws.ec2.Subnet')
    @patch('pulumi_aws.ec2.Vpc')
    def test_complete_network_creation(self, mock_vpc, mock_subnet, mock_igw, 
                                     mock_eip, mock_nat_gw, mock_route_table):
        """Test that all network components are created correctly."""
        # Create network
        network = c_KubernetesNetwork("test-network", self.test_cidr_config)
        
        # Verify VPC creation
        mock_vpc.assert_called_once_with(
            "kubernetes-vpc",
            cidr_block="10.0.0.0/21",
            enable_dns_hostnames=True,
            enable_dns_support=True,
            opts=unittest.mock.ANY
        )
        
        # Verify 4 subnets were created (excluding VPC from dict)
        self.assertEqual(mock_subnet.call_count, 4)
        
        # Verify Internet Gateway creation
        mock_igw.assert_called_once()
        
        # Verify EIP creation
        mock_eip.assert_called_once()
        
        # Verify NAT Gateway creation
        mock_nat_gw.assert_called_once()
        
        # Verify Route Table creation
        mock_route_table.assert_called_once()
    
    @patch('pulumi_aws.ec2.Subnet')
    @patch('pulumi_aws.ec2.Vpc')
    def test_subnet_configuration(self, mock_vpc, mock_subnet):
        """Test that subnets are configured with correct CIDR blocks."""
        network = c_KubernetesNetwork("test-network", self.test_cidr_config)
        
        # Expected subnet calls
        expected_calls = [
            call("control-plane-a", vpc_id=unittest.mock.ANY, 
                 cidr_block="10.0.1.0/27", opts=unittest.mock.ANY),
            call("control-plane-b", vpc_id=unittest.mock.ANY, 
                 cidr_block="10.0.2.0/27", opts=unittest.mock.ANY),
            call("workers-a", vpc_id=unittest.mock.ANY, 
                 cidr_block="10.0.3.0/25", opts=unittest.mock.ANY),
            call("workers-b", vpc_id=unittest.mock.ANY, 
                 cidr_block="10.0.4.0/25", opts=unittest.mock.ANY)
        ]
        
        # Verify subnet calls match expected configuration
        mock_subnet.assert_has_calls(expected_calls, any_order=True)
    
    @patch('pulumi_aws.ec2.Vpc')
    def test_vpc_dns_configuration(self, mock_vpc):
        """Test that VPC is configured with proper DNS settings."""
        network = c_KubernetesNetwork("test-network", self.test_cidr_config)
        
        # Verify DNS settings are enabled
        call_args = mock_vpc.call_args
        self.assertTrue(call_args.kwargs['enable_dns_hostnames'])
        self.assertTrue(call_args.kwargs['enable_dns_support'])
    
    def test_minimal_cidr_config(self):
        """Test network creation with minimal CIDR configuration."""
        minimal_config = {
            "vpc": "192.168.0.0/24",
            "subnet-1": "192.168.0.0/26"
        }
        
        with patch('pulumi_aws.ec2.Vpc'), \
             patch('pulumi_aws.ec2.Subnet') as mock_subnet:
            
            network = c_KubernetesNetwork("minimal-network", minimal_config)
            
            # Should create exactly one subnet
            self.assertEqual(mock_subnet.call_count, 1)
    
    def test_dynamic_subnet_attributes(self):
        """Test that subnet attributes are dynamically set on the network object."""
        with patch('pulumi_aws.ec2.Vpc'), \
             patch('pulumi_aws.ec2.Subnet'):
            
            network = c_KubernetesNetwork("test-network", self.test_cidr_config)
            
            # Verify dynamic attributes exist
            self.assertTrue(hasattr(network, 'control-plane-a'))
            self.assertTrue(hasattr(network, 'control-plane-b'))
            self.assertTrue(hasattr(network, 'workers-a'))
            self.assertTrue(hasattr(network, 'workers-b'))
    
    @patch('pulumi_aws.ec2.RouteTable')
    @patch('pulumi_aws.ec2.NatGateway')
    @patch('pulumi_aws.ec2.Eip')
    @patch('pulumi_aws.ec2.InternetGateway')
    @patch('pulumi_aws.ec2.Subnet')
    @patch('pulumi_aws.ec2.Vpc')
    def test_nat_gateway_configuration(self, mock_vpc, mock_subnet, mock_igw,
                                     mock_eip, mock_nat_gw, mock_route_table):
        """Test NAT Gateway is properly configured with first subnet."""
        network = c_KubernetesNetwork("test-network", self.test_cidr_config)
        
        # Verify NAT Gateway uses EIP and first subnet
        mock_nat_gw.assert_called_once_with(
            "ngw",
            allocation_id=unittest.mock.ANY,
            subnet_id=unittest.mock.ANY,
            opts=unittest.mock.ANY
        )
    
    @patch('pulumi_aws.ec2.RouteTable')
    @patch('pulumi_aws.ec2.NatGateway')
    @patch('pulumi_aws.ec2.Eip')
    @patch('pulumi_aws.ec2.InternetGateway')
    @patch('pulumi_aws.ec2.Subnet')
    @patch('pulumi_aws.ec2.Vpc')
    def test_route_table_configuration(self, mock_vpc, mock_subnet, mock_igw,
                                     mock_eip, mock_nat_gw, mock_route_table):
        """Test route table is configured with correct default route."""
        network = c_KubernetesNetwork("test-network", self.test_cidr_config)
        
        # Verify route table configuration
        call_args = mock_route_table.call_args
        self.assertEqual(call_args[0][0], "nat-route-table")
        self.assertIn('routes', call_args.kwargs)


if __name__ == '__main__':
    unittest.main()