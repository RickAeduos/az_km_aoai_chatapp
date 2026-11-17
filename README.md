# Simple ChatGPT client

A Streamlit chat app for Azure OpenAI `gpt-4.1-mini`, hosted on Azure App Service. It uses the Azure OpenAI v1 Chat Completions API and Microsoft Entra authentication.

## 1. Create an Azure Web App and grant access

Create a Linux Web App with Python 3.12. Enable its system-assigned managed identity on the **Identity** page. In **Access control (IAM)** on the Azure OpenAI resource that hosts your `gpt-4.1-mini` deployment, give the Web App identity the **Cognitive Services OpenAI User** role.

To restrict access to the chat page, configure Microsoft Entra sign-in under the Web App's **Authentication** settings. [App Service authentication guide](https://learn.microsoft.com/azure/app-service/scenario-secure-app-authentication-app-service)

## 2. Configure the Web App

Under **Settings → Environment variables → App settings**, add these settings and apply the changes.

| Name | Value |
| --- | --- |
| `OPENAI_API_ENDPOINT` | The Azure OpenAI resource URL, such as `https://<resource>.openai.azure.com`. The full v1 base URL ending in `/openai/v1/` also works. |
| `OPENAI_DEPLOYMENT` | The model's **deployment name** in Foundry. The default is `gpt-4.1-mini`. Set this to the actual deployment name if you picked a different one, such as `chat-mini`. |
| `SCM_DO_BUILD_DURING_DEPLOYMENT` | `true` for installing Python dependencies during ZIP deployment. |

The v1 API uses the endpoint path for versioning. You can remove the old `OPENAI_API_VERSION` setting.

## 3. Deploy the application

Clone this fork and run the following from its root in Bash. Sign in with `az login` first, and substitute your resource group and Web App name.

```bash
RG='rg-simple-chatgpt'
APP='your-web-app-name'

az webapp config set -g "$RG" -n "$APP" \
  --startup-file 'python -m streamlit run app.py --server.port 8000 --server.address 0.0.0.0'

python -m zipfile -c chatapp.zip app.py requirements.txt
az webapp deploy -g "$RG" -n "$APP" --src-path chatapp.zip --type zip
```

Open the **Default domain** on the Web App's **Overview** page. Send an initial question and then a follow-up to verify the conversation history.
