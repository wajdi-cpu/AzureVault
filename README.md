# AzureVault

A cloud file storage web application built with Flask and Azure Blob Storage, deployed on a secure Azure infrastructure with no public VM exposure.

---

## Overview

AzureVault lets you upload, download, and delete files through a web interface. All files are stored in Azure Blob Storage. The VM running the app is isolated inside a VNet with no public IP — access is only through Azure Bastion.

---

## warning

⚠️ Not all Azure regions support every resource (Bastion Standard SKU, certain VM sizes, etc.). If deployment fails, check Azure Products by Region and switch to a region where all required services are available — this project uses francecentral for full compatibility.

## Features

- Upload files to Azure Blob Storage
- Download and delete files from the web interface
- Secure infrastructure: VM has no public IP
- Azure Bastion (Standard SKU) for SSH access
- NSG rules restricting inbound traffic

---

## Architecture

```js
Browser
│
▼
Azure Bastion ──► vault-vm (Ubuntu 22.04, no public IP)
│
▼
Flask app (port 5000)
│
▼
Azure Blob Storage (avvault32585)
```

**Infrastructure:**
- Region: `francecentral`
- Resource Group: `AzureValut`
- VNet: `vault-vnet` (10.0.0.0/16)
- Subnet: `vault-subnet` (10.0.1.0/24)
- Bastion Subnet: `AzureBastionSubnet` (10.0.2.0/27)
- VM: `vault-vm` — Standard_B1s, Ubuntu 22.04
- Storage: `avvault32585` — Standard LRS

---

## Project 

```js
AzureVault
├── app.py
├── infra
│   ├── bastion.sh
│   ├── deploy_all.sh
│   ├── nsg.sh
│   ├── resource_group.sh
│   ├── storage.sh
│   ├── vm.sh
│   └── vnet.sh
├── README.md
├── requirements.txt
├── screenshots
│   ├── python_app.png
│   ├── region_error.png
│   └── resource_group.png
└── templates
    └── index.html
```
---

## Setup

### Prerequisites

- Azure CLI installed and logged in (`az login`)
- Python 3.10+
- An active Azure subscription

### 1. Deploy Infrastructure

```bash
cd AzureVault
bash infra/deploy_all.sh
```

### 2. Configure Environment

```bash
cp .env.example .env
# Fill in your Azure storage connection string and container name
```

### 3. Install Dependencies

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Run the App

```bash
python app.py
```

Access at `http://localhost:5000`

---

## Environment Variables

Create a `.env` file (never commit this):