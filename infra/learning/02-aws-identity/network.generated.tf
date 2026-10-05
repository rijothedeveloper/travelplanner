# __generated__ by Terraform
# Please review these resources and move them into your main configuration files.

# __generated__ by Terraform
resource "aws_subnet" "travel-subnet-public-A" {
  provider                                       = aws.adoption
  assign_ipv6_address_on_creation                = false
  availability_zone                              = "us-west-2a"
  cidr_block                                     = "10.0.1.0/24"
  customer_owned_ipv4_pool                       = null
  enable_dns64                                   = false
  enable_resource_name_dns_a_record_on_launch    = false
  enable_resource_name_dns_aaaa_record_on_launch = false
  ipv4_ipam_pool_id                              = null
  ipv4_netmask_length                            = null
  ipv6_ipam_pool_id                              = null
  ipv6_native                                    = false
  ipv6_netmask_length                            = null
  map_public_ip_on_launch                        = false
  outpost_arn                                    = null
  private_dns_hostname_type_on_launch            = "ip-name"
  region                                         = "us-west-2"
  tags = {
    Name = "travel-subnet-public-A"
  }
  tags_all = {
    Name = "travel-subnet-public-A"
  }
  vpc_id = "vpc-00155e20d23ef88fd"
  lifecycle {
    prevent_destroy = true
  }
}

# __generated__ by Terraform
resource "aws_subnet" "travel-subnet-private-A" {
  provider                                       = aws.adoption
  assign_ipv6_address_on_creation                = false
  availability_zone                              = "us-west-2a"
  cidr_block                                     = "10.0.10.0/24"
  customer_owned_ipv4_pool                       = null
  enable_dns64                                   = false
  enable_resource_name_dns_a_record_on_launch    = false
  enable_resource_name_dns_aaaa_record_on_launch = false
  ipv4_ipam_pool_id                              = null
  ipv4_netmask_length                            = null
  ipv6_ipam_pool_id                              = null
  ipv6_native                                    = false
  map_public_ip_on_launch                        = false
  outpost_arn                                    = null
  private_dns_hostname_type_on_launch            = "ip-name"
  region                                         = "us-west-2"
  tags = {
    Name     = "travel-lab-vpc"
    Training = "terraform-managed"
  }
  vpc_id = "vpc-00155e20d23ef88fd"
  lifecycle {
    prevent_destroy = true
  }
}

# __generated__ by Terraform
resource "aws_vpc" "travel_lab" {
  provider                             = aws.adoption
  assign_generated_ipv6_cidr_block     = false
  cidr_block                           = "10.0.0.0/16"
  enable_dns_hostnames                 = false
  enable_dns_support                   = true
  enable_network_address_usage_metrics = false
  instance_tenancy                     = "default"
  ipv4_ipam_pool_id                    = null
  ipv4_netmask_length                  = null
  ipv6_ipam_pool_id                    = null
  region                               = "us-west-2"
  tags = {
    Name     = "travel-lab-vpc"
    Training = "terraform-managed"
  }

  lifecycle {
    prevent_destroy = true
  }
}
