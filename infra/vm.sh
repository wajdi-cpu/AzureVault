#!/bin/bash
az vm create \
  --resource-group AzureValut \
  --name vault-vm \
  --image Ubuntu2204 \
  --size Standard_B1s \
  --admin-username vault \
  --ssh-key-values ~/.ssh/rsa_id.pem \
  --vnet-name vault-vnet \
  --subnet vault-subnet \
  --nsg vault-nsg \
  --public-ip-address "" \
  --no-wait
echo "[+] VM creation initiated."
