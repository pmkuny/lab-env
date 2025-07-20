import ipaddress
import unittest
from itertools import combinations
from networking import c_KubernetesNetwork


class TestNetworkProperties(unittest.TestCase):
    """Test suite for network property validation and CIDR calculations."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.standard_cidr_config = {
            "vpc": "10.0.0.0/21",
            "control-plane-a": "10.0.1.0/27",
            "control-plane-b": "10.0.2.0/27",
            "workers-a": "10.0.3.0/25",
            "workers-b": "10.0.4.0/25"
        }
    
    def test_cidr_validation(self):
        """Test that all CIDR blocks are valid IPv4 networks."""
        for name, cidr in self.standard_cidr_config.items():
            with self.subTest(cidr=cidr, name=name):
                try:
                    network = ipaddress.ip_network(cidr, strict=True)
                    self.assertIsInstance(network, ipaddress.IPv4Network)
                except ValueError as e:
                    self.fail(f"Invalid CIDR block '{cidr}' for {name}: {e}")
    
    def test_private_network_ranges(self):
        """Test that all CIDR blocks use private IP ranges."""
        for name, cidr in self.standard_cidr_config.items():
            with self.subTest(cidr=cidr, name=name):
                network = ipaddress.ip_network(cidr)
                self.assertTrue(
                    network.is_private,
                    f"CIDR block '{cidr}' for {name} is not in private range"
                )
    
    def test_subnet_within_vpc(self):
        """Test that all subnets are within VPC CIDR range."""
        vpc_cidr = ipaddress.ip_network(self.standard_cidr_config["vpc"])
        
        # Test all subnets except VPC itself
        for name, cidr in self.standard_cidr_config.items():
            if name != "vpc":
                with self.subTest(subnet=name, cidr=cidr):
                    subnet = ipaddress.ip_network(cidr)
                    self.assertTrue(
                        subnet.subnet_of(vpc_cidr),
                        f"Subnet '{name}' ({cidr}) is not within VPC range ({vpc_cidr})"
                    )
    
    def test_subnet_non_overlapping(self):
        """Test that subnets do not overlap with each other."""
        subnet_configs = {k: v for k, v in self.standard_cidr_config.items() if k != "vpc"}
        subnet_networks = {name: ipaddress.ip_network(cidr) 
                          for name, cidr in subnet_configs.items()}
        
        # Check all pairs of subnets for overlap
        for (name1, net1), (name2, net2) in combinations(subnet_networks.items(), 2):
            with self.subTest(subnet1=name1, subnet2=name2):
                self.assertFalse(
                    net1.overlaps(net2),
                    f"Subnets '{name1}' ({net1}) and '{name2}' ({net2}) overlap"
                )
    
    def test_subnet_capacity(self):
        """Test that subnets have expected host capacity."""
        expected_capacities = {
            "control-plane-a": 30,  # /27 = 32 - 2 (network/broadcast) = 30
            "control-plane-b": 30,  # /27 = 32 - 2 = 30
            "workers-a": 126,       # /25 = 128 - 2 = 126
            "workers-b": 126        # /25 = 128 - 2 = 126
        }
        
        for name, expected_hosts in expected_capacities.items():
            with self.subTest(subnet=name):
                cidr = self.standard_cidr_config[name]
                network = ipaddress.ip_network(cidr)
                actual_hosts = network.num_addresses - 2  # Subtract network and broadcast
                self.assertEqual(
                    actual_hosts, expected_hosts,
                    f"Subnet '{name}' has {actual_hosts} hosts, expected {expected_hosts}"
                )
    
    def test_vpc_capacity_sufficient(self):
        """Test that VPC has sufficient capacity for all subnets."""
        vpc_network = ipaddress.ip_network(self.standard_cidr_config["vpc"])
        
        # Calculate total subnet addresses needed
        total_subnet_addresses = 0
        for name, cidr in self.standard_cidr_config.items():
            if name != "vpc":
                subnet_network = ipaddress.ip_network(cidr)
                total_subnet_addresses += subnet_network.num_addresses
        
        vpc_available_addresses = vpc_network.num_addresses
        
        self.assertGreaterEqual(
            vpc_available_addresses, total_subnet_addresses,
            f"VPC capacity ({vpc_available_addresses}) insufficient for subnets ({total_subnet_addresses})"
        )
    
    def test_edge_case_minimal_config(self):
        """Test validation with minimal CIDR configuration."""
        minimal_config = {
            "vpc": "192.168.1.0/24",
            "subnet-1": "192.168.1.0/26"
        }
        
        vpc_network = ipaddress.ip_network(minimal_config["vpc"])
        subnet_network = ipaddress.ip_network(minimal_config["subnet-1"])
        
        self.assertTrue(vpc_network.is_private)
        self.assertTrue(subnet_network.is_private)
        self.assertTrue(subnet_network.subnet_of(vpc_network))
    
    def test_edge_case_large_vpc(self):
        """Test validation with large VPC configuration."""
        large_config = {
            "vpc": "10.0.0.0/8",
            "subnet-1": "10.1.0.0/16",
            "subnet-2": "10.2.0.0/16"
        }
        
        vpc_network = ipaddress.ip_network(large_config["vpc"])
        
        for name, cidr in large_config.items():
            if name != "vpc":
                with self.subTest(subnet=name):
                    subnet_network = ipaddress.ip_network(cidr)
                    self.assertTrue(subnet_network.subnet_of(vpc_network))
    
    def test_invalid_cidr_detection(self):
        """Test that invalid CIDR blocks are properly detected."""
        invalid_configs = [
            "10.0.0.0/33",      # Invalid prefix length
            "256.0.0.0/24",     # Invalid IP address
            "10.0.0.1/24",      # Host bits set (not strict network)
            "not-an-ip/24"      # Invalid format
        ]
        
        for invalid_cidr in invalid_configs:
            with self.subTest(cidr=invalid_cidr):
                with self.assertRaises(ValueError):
                    ipaddress.ip_network(invalid_cidr, strict=True)
    
    def test_subnet_utilization_efficiency(self):
        """Test that subnet sizes are efficiently allocated."""
        # Control plane subnets should be smaller than worker subnets
        cp_a_network = ipaddress.ip_network(self.standard_cidr_config["control-plane-a"])
        workers_a_network = ipaddress.ip_network(self.standard_cidr_config["workers-a"])
        
        self.assertLess(
            cp_a_network.num_addresses, workers_a_network.num_addresses,
            "Control plane subnet should be smaller than worker subnet"
        )
        
        # Both control plane subnets should be same size
        cp_b_network = ipaddress.ip_network(self.standard_cidr_config["control-plane-b"])
        self.assertEqual(
            cp_a_network.num_addresses, cp_b_network.num_addresses,
            "Control plane subnets should be same size"
        )
        
        # Both worker subnets should be same size
        workers_b_network = ipaddress.ip_network(self.standard_cidr_config["workers-b"])
        self.assertEqual(
            workers_a_network.num_addresses, workers_b_network.num_addresses,
            "Worker subnets should be same size"
        )


if __name__ == '__main__':
    unittest.main()