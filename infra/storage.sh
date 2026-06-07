#!/bin/bash
# Primary storage account
az storage account create \
  --resource-group AzureValut \
  --name avvault32585 \
  --location francecentral \
  --sku Standard_LRS

# Create blob container
az storage container create \
  --account-name avvault32585 \
  --name vault \
  --auth-mode login
echo "[+] Storage account and container created."
