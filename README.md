# API Key Integration for Universal Usage

This guide provides detailed instructions on generating, using, and integrating API keys into your applications or projects, enabling secure and efficient access to the Video Sentiment Analysis API.

---

## Table of Contents
1. **What is an API Key?**
2. **How to Obtain an API Key**
3. **How to Use the API Key**
4. **Integration Examples**
5. **Best Practices for API Key Usage**

---

### 1. What is an API Key?
An API Key is a unique identifier used to authenticate requests associated with your account. It ensures secure communication between your application and the API.

---

### 2. How to Obtain an API Key

1. **Register an Account:**
   - Navigate to the registration page of the application.
   - Provide a valid username, email, and password.
   - Submit the registration form.

2. **Login to Your Account:**
   - Use the username and password created during registration.
   - On successful login, an API Key will be displayed or retrievable via the dashboard.

3. **Generate or Rotate API Key:**
   - Access the "API Key Management" section on your dashboard.
   - Click "Rotate API Key" to generate a new key if necessary.
   - Copy the API Key securely as it will not be shown again.

---

### 3. How to Use the API Key

#### **Including the API Key in Requests**
The API Key must be included in the header of each request for authentication. Below is an example of a request:

```http
GET /api/analysis_history HTTP/1.1
Host: sensiwithme.my.id
Authorization: Bearer <YOUR_API_KEY>
Content-Type: application/json
```

Replace `<YOUR_API_KEY>` with your actual API Key.

#### **Sample Fetch Request in JavaScript**
```javascript
const apiKey = 'YOUR_API_KEY';
fetch('https://sensiwithme.my.id/api/analysis_history', {
  method: 'GET',
  headers: {
    'Authorization': `Bearer ${apiKey}`,
    'Content-Type': 'application/json'
  }
})
  .then(response => response.json())
  .then(data => console.log(data))
  .catch(error => console.error('Error:', error));
```

---

### 4. Integration Examples

#### **Frontend Integration (React)**
```javascript
const apiKey = 'YOUR_API_KEY';
function fetchHistory() {
  return fetch('https://sensiwithme.my.id/api/analysis_history', {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${apiKey}`,
      'Content-Type': 'application/json'
    }
  })
    .then(response => response.json())
    .then(data => console.log('History:', data))
    .catch(err => console.error('Error fetching history:', err));
}
```

#### **Backend Integration (Flask)**
```python
import requests

def fetch_analysis_history(api_key):
    url = 'https://sensiwithme.my.id/api/analysis_history'
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}, {response.text}")
        return None
```

---

### 5. Best Practices for API Key Usage

1. **Keep Your API Key Secure:**
   - Do not hard-code API Keys directly in your source code.
   - Use environment variables to store sensitive information.

2. **Regenerate Keys Regularly:**
   - Rotate API Keys periodically to reduce security risks.

3. **Restrict Key Usage:**
   - Limit API Key permissions to only the required actions.
   - Apply IP restrictions if supported.

4. **Monitor Usage:**
   - Track the usage of your API Key in your dashboard.
   - Be alert to unauthorized or suspicious activity.

5. **Handle Errors Gracefully:**
   - Use error handling mechanisms to manage expired or invalid API Keys.
   - Provide informative error messages to users.

---

With these steps and practices, you can effectively use and integrate API Keys for secure communication with the Video Sentiment Analysis API.

