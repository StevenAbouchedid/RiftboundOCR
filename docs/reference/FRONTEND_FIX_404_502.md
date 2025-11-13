# 🔧 Fix 404 and 502 Errors - Frontend Update Required

## ⚠️ Current Problem

Your frontend is calling the **wrong URL**, causing 404 errors:

**❌ Wrong (Current):**
```
POST /process
```

**✅ Correct (Need to update to):**
```
POST /api/v1/process
```

---

## 🛠️ How to Fix

### Step 1: Find Your OCR Service Configuration

Look for where you configure the OCR service URL in your frontend code. Common locations:
- `.env` file
- `config.js` or `config.ts`
- API service file (e.g., `api/ocr.js`)
- Component that handles image upload

### Step 2: Update the Base URL

**If you have a base URL constant:**

```javascript
// ❌ WRONG - Current code
const OCR_SERVICE_URL = 'https://riftboundocr-production.up.railway.app';

// When making request
fetch(`${OCR_SERVICE_URL}/process`, ...)  // Results in /process (404!)
```

**✅ CORRECT - Update to:**

```javascript
const OCR_SERVICE_URL = 'https://riftboundocr-production.up.railway.app/api/v1';

// When making request
fetch(`${OCR_SERVICE_URL}/process`, ...)  // Results in /api/v1/process (works!)
```

### Step 3: Or Update the Full URL

**If you're using the full URL directly:**

```javascript
// ❌ WRONG
fetch('https://riftboundocr-production.up.railway.app/process', {
  method: 'POST',
  body: formData
})

// ✅ CORRECT
fetch('https://riftboundocr-production.up.railway.app/api/v1/process', {
  method: 'POST',
  body: formData
})
```

---

## 📝 Complete Working Example

### Using Fetch API

```javascript
const uploadImage = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  try {
    const response = await fetch(
      'https://riftboundocr-production.up.railway.app/api/v1/process',
      {
        method: 'POST',
        body: formData,
        signal: AbortSignal.timeout(120000)  // 2 minutes timeout
      }
    );
    
    if (!response.ok) {
      throw new Error(`Upload failed: ${response.status}`);
    }
    
    const result = await response.json();
    console.log('OCR Result:', result);
    return result;
    
  } catch (error) {
    console.error('OCR Error:', error);
    throw error;
  }
};
```

### Using Axios

```javascript
import axios from 'axios';

const uploadImage = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  try {
    const response = await axios.post(
      'https://riftboundocr-production.up.railway.app/api/v1/process',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        timeout: 120000  // 2 minutes
      }
    );
    
    console.log('OCR Result:', response.data);
    return response.data;
    
  } catch (error) {
    console.error('OCR Error:', error);
    throw error;
  }
};
```

---

## ⏱️ Important: Set Proper Timeout

OCR processing takes **30-90 seconds per image**! 

**Make sure your timeout is at least 2 minutes:**

```javascript
// Fetch API
signal: AbortSignal.timeout(120000)  // 2 minutes

// Axios
timeout: 120000  // 2 minutes

// jQuery
timeout: 120000  // 2 minutes
```

---

## ✅ Testing Your Fix

### 1. Update the code
Add `/api/v1` to your URL

### 2. Rebuild/restart your frontend
```bash
npm run build
# or
npm run dev
```

### 3. Test on browser
Open browser console and check:
- Network tab should show: `POST /api/v1/process` (not `/process`)
- Status should be `200 OK` (not `404`)
- Response should have JSON with decklist data

### 4. If still errors:
- Clear browser cache
- Hard refresh (Ctrl+Shift+R or Cmd+Shift+R)
- Check you updated the correct file
- Verify your build process picked up the changes

---

## 🎯 Quick Checklist

- [ ] Found where OCR URL is configured in frontend
- [ ] Added `/api/v1` to the base URL
- [ ] Set timeout to 120 seconds (2 minutes)
- [ ] Rebuilt/restarted frontend
- [ ] Tested on browser - Network tab shows `/api/v1/process`
- [ ] Tested on phone (if mobile app)
- [ ] Verified 200 OK response (not 404)
- [ ] Confirmed JSON response with decklist data

---

## 🐛 Troubleshooting

### Still Getting 404?
- Double-check the URL includes `/api/v1`
- Verify you saved the file
- Rebuild your frontend
- Clear browser cache

### Getting 502?
- Wait 2-3 minutes for Railway deployment to complete
- First request after deployment may take 90 seconds (OCR models loading)
- Check service is healthy: `https://riftboundocr-production.up.railway.app/health`

### Getting CORS errors?
- Should be fixed in latest deployment
- Clear browser cache
- Wait for Railway deployment to finish

### Timeout errors?
- Increase timeout to 120 seconds
- OCR processing is slow, be patient!

---

## 📚 More Documentation

- **Quick Examples**: `FRONTEND_QUICK_START.md`
- **Complete Guide**: `FRONTEND_INTEGRATION.md`
- **All Endpoints**: Visit `https://riftboundocr-production.up.railway.app/docs`

---

## ✨ Summary

**The fix is simple:**

Change `/process` → `/api/v1/process`

That's it! Just add `/api/v1` before `/process` in your code.

