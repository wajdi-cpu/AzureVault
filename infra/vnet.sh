#!/bin/bash
az network vnet create \
  --resource-group AzureValut \
  --name vault-vnet \
  --address-prefix 10.0.0.0/16 \
  --subnet-name vault-subnet \
  --subnet-prefix 10.0.1.0/24

# Bastion requires its own dedicated subnet named exactly AzureBastionSubnet
az network vnet subnet create \
  --resource-group AzureValut \
  --vnet-name vault-vnet \
  --name AzureBastionSubnet \
  --address-prefix 10.0.2.0/27
echo "[+] VNet and subnets created."
