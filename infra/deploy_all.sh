#!/bin/bash
set -e
bash infra/resource_group.sh
bash infra/vnet.sh
bash infra/nsg.sh
bash infra/vm.sh
bash infra/bastion.sh
bash infra/storage.sh
echo "[+] AzureVault infrastructure deployed."
