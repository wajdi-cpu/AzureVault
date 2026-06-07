#!/bin/bash
# Create public IP for Bastion
az network public-ip create \
  --resource-group AzureValut \
  --name vault-bastion-ip \
  --sku Standard \
  --location francecentral

# Deploy Bastion (Standard SKU)
az network bastion create \
  --resource-group AzureValut \
  --name vault-bastion \
  --vnet-name vault-vnet \
  --public-ip-address vault-bastion-ip \
  --sku Standard \
  --location francecentral
echo "[+] Bastion deployed."
