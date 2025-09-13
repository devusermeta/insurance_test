# Azure Communication Services Email Domain Setup

## 🚨 Issue Found: Domain Not Linked

The email sending is failing because the Azure Communication Services domain is not properly configured.

**Error:** `DomainNotLinked - The specified sender domain has not been linked.`

## 🔧 Solution: Configure Email Domain in Azure

### Step 1: Access Azure Communication Services
1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to your Communication Services resource: `claim-assist`
3. In the left menu, click on **"Email"** under **"Communication"**

### Step 2: Set Up Email Domain
You have two options:

#### Option A: Use Azure Managed Domain (Recommended for Testing)
1. In the Email section, click **"Add domain"**
2. Select **"Azure managed domain"**
3. This will give you a domain like: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx.azurecomm.net`
4. Copy the sender email address provided

#### Option B: Use Custom Domain (For Production)
1. Click **"Add domain"**  
2. Select **"Custom domain"**
3. Enter your custom domain (you need to own it)
4. Follow DNS verification steps

### Step 3: Update Environment Variables
After setting up the domain, update your `.env` file:

```env
AZURE_COMMUNICATION_SENDER_EMAIL=DoNotReply@[YOUR-NEW-DOMAIN].azurecomm.net
```

### Step 4: Test Email Sending
Run the test again after updating the domain configuration.

## 🎯 Quick Fix Steps

1. **Go to Azure Portal → Communication Services → claim-assist → Email**
2. **Add an Azure managed domain**
3. **Copy the new sender email address**
4. **Update .env file with the new sender email**
5. **Restart Communication Agent**
6. **Run email test again**

## 📧 Expected Result
After proper domain configuration, you should receive an email at `purohitabhinav2001@gmail.com` with:
- Subject: "Insurance Claim REAL-EMAIL-TEST-001 - Approved"
- Formatted HTML content with claim details
- Professional insurance notification styling

## 🔍 Current Configuration Status
- ✅ Azure Communication Services resource created
- ✅ Connection string configured  
- ❌ Email domain not properly linked
- ✅ Communication Agent code working correctly

The code is perfect - we just need to fix the Azure domain configuration!