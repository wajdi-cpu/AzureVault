#!/bin/bash
az network nsg create \
  --resource-group AzureValut \
  --name vault-nsg

# Allow SSH inbound
az network nsg rule create \
  --resource-group AzureValut \
  --nsg-name vault-nsg \
  --name Allow-SSH \
  --priority 1000 \
  --protocol Tcp \
  --destination-port-range 22 \
  --access Allow \
  --direction Inbound

# Allow Flask app port
az network nsg rule create \
  --resource-group AzureValut \
  --nsg-name vault-nsg \
  --name Allow-Flask \
  --priority 1100 \
  --protocol Tcp \
  --destination-port-range 5000 \
  --access Allow \
  --direction Inbound

# Attach NSG to subnet
az network vnet subnet update \
  --resource-group AzureValut \
  --vnet-name vault-vnet \
  --name vault-subnet \
  --network-security-group vault-nsg
echo "[+] NSG created and attached."
