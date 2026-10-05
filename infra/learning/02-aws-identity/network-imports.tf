import {
  provider = aws.adoption
  to       = aws_vpc.travel_lab
  id       = "vpc-00155e20d23ef88fd"
}

import {
  provider = aws.adoption
  to       = aws_subnet.travel-subnet-public-A
  id       = "subnet-05a6224e39c6ff187"
}

import {
  provider = aws.adoption
  to       = aws_subnet.travel-subnet-private-A
  id       = "subnet-0f9ec153af2a73710"
}