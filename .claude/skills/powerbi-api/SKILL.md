# Power BI REST API Skill

## Description
Expert in Power BI REST API for managing workspaces, datasets, reports,
and refresh operations programmatically. Load this skill when the user asks
about automating Power BI, REST API calls, dataset refresh, workspace
management, or embedding.

---

## Authentication
Power BI uses Azure AD OAuth2. You need:
- Tenant ID
- Client ID (App registration)
- Client Secret or Certificate

```python
import msal

def get_powerbi_token(tenant_id, client_id, client_secret):
    authority = f"https://login.microsoftonline.com/{tenant_id}"
    app = msal.ConfidentialClientApplication(
        client_id,
        authority=authority,
        client_credential=client_secret
    )
    result = app.acquire_token_for_client(
        scopes=["https://analysis.windows.net/powerbi/api/.default"]
    )
    return result["access_token"]
```

---

## Key Endpoints

### Workspaces (Groups)
```
GET  /v1.0/myorg/groups                          # List workspaces
GET  /v1.0/myorg/groups/{groupId}               # Get workspace
POST /v1.0/myorg/groups                          # Create workspace
```

### Datasets
```
GET  /v1.0/myorg/groups/{groupId}/datasets       # List datasets
POST /v1.0/myorg/groups/{groupId}/datasets/{id}/refreshes  # Trigger refresh
GET  /v1.0/myorg/groups/{groupId}/datasets/{id}/refreshes  # Get refresh history
```

### Reports
```
GET  /v1.0/myorg/groups/{groupId}/reports        # List reports
GET  /v1.0/myorg/groups/{groupId}/reports/{id}   # Get report
POST /v1.0/myorg/groups/{groupId}/reports/{reportId}/ExportTo  # Export report
```

### Row-Level Security
```
GET  /v1.0/myorg/groups/{groupId}/datasets/{id}/users   # Get RLS users
POST /v1.0/myorg/generateToken                           # Generate embed token
```

---

## Common Operations

### Trigger Dataset Refresh
```python
import requests

def refresh_dataset(token, workspace_id, dataset_id):
    url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}/refreshes"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(url, headers=headers)
    return response.status_code == 202  # 202 = Accepted
```

### Check Refresh Status
```python
def get_refresh_history(token, workspace_id, dataset_id):
    url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}/refreshes"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    return response.json()["value"][0]  # Most recent refresh
```
