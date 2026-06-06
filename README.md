# ⚡ InstaScope API & Playground

A modern, lightweight Python FastAPI backend service that scrapes public Instagram profile metadata (followers, following, posts, biography, verified badge, and website links) using public web endpoints. 

It comes with a stunning **glassmorphic playground UI** to test the API right from your browser, plus an **automated keep-alive ping engine** designed for seamless, 24/7 runtime on hobby hosting providers like Railway.

---

## ✨ Features

- **FastAPI JSON Endpoint:** Direct, structured access to user data at `/api/instagram/profile?username=<username>`.
- **CORS Enabled:** Fetch profile information directly from your own frontend websites or mobile apps.
- **Glassmorphic Playground UI:** A modern, visual dashboard with dark mode styling, responsive counters, and interactive syntax-highlighted JSON viewer.
- **Built-in Auto-Ping Service:** Periodically self-requests the server (every 10 minutes) to keep the app active and prevent sleeping on free/hobby tiers.
- **Header & UA Rotation:** Mimics browser requests by rotating modern desktop User-Agents to prevent rapid rate limiting.
- **Proxy Support:** Ready to accept proxy routing (`PROXY_URL`) for scaling and bypassing aggressive IP blocks.

---

## 🚀 Local Setup & Development

To run the project locally on your machine, follow these steps:

### 1. Clone or Copy Files
Ensure all project files are placed in a single directory:
- `main.py`
- `scraper.py`
- `ping_service.py`
- `run.py`
- `requirements.txt`
- `Procfile`
- `templates/index.html`

### 2. Install Dependencies
Run the following command to install the required Python packages:
```bash
pip install -r requirements.txt
```

### 3. Run the Server
Launch the development server:
```bash
python run.py
```
By default, the server runs on `http://localhost:8000`.

- Open **`http://localhost:8000/`** to view the interactive glassmorphic UI playground.
- Open **`http://localhost:8000/docs`** to access the automated OpenAPI / Swagger documentation page.

---

## ☁️ Deploying to Railway

Railway detects the Python configuration and `requirements.txt` automatically. Follow these steps to host your application 24/7:

### 1. Initialize Git & Push to GitHub
If you haven't already, push your code directory to a new repository on GitHub:
```bash
git init
git add .
git commit -m "Initial commit of InstaScope API"
# Create a GitHub repo and link it:
git remote add origin <your-github-repo-url>
git branch -M main
git push -u origin main
```

### 2. Connect to Railway
1. Go to [Railway](https://railway.app) and log into your account.
2. Click **New Project** -> **Deploy from GitHub repo**.
3. Select your repository.
4. Railway will automatically build and deploy the app using the configuration in `Procfile` and `requirements.txt`.

### 3. Configure Keep-Alive Auto-Ping (Crucial for 24/7 Hosting)
By default, hobby servers can go to sleep when they don't receive traffic. To ensure your application runs **24/7**:
1. Go to your service's **Settings** tab in Railway.
2. Under **Networking**, generate a public domain (e.g. `your-app.up.railway.app`).
3. Switch to the **Variables** tab in your Railway project dashboard.
4. Add the following environment variable:
   - **`APP_URL`**: Set this to your generated public domain (e.g. `https://your-app.up.railway.app`).
5. Save the variable. The application will redeploy, and the background keep-alive ping engine will now wake up and request its own `/api/health` endpoint every 10 minutes, preventing the container from sleeping.

### 4. Bypassing Instagram Blocks & Proxy Rotation (Optional)
If your deployed app receives a `429 Too Many Requests` status code from Instagram, it means the hosting IP range (or your single proxy IP) is rate-limited. To solve this, you can configure multiple rotating proxies:
1. Obtain HTTP/HTTPS proxies (e.g., from Webshare, Bright Data, etc.).
2. In Railway, go to the **Variables** tab.
3. Add the following environment variable:
   - **`PROXY_URL`**: A comma-separated list of your formatted proxy URLs.
     *Example:* `http://user:pass@ip1:port,http://user:pass@ip2:port,http://user:pass@ip3:port`
4. The scraper will automatically shuffle this list and choose a random proxy for each request. If a proxy is rate-limited (429) or fails, it will auto-failover and retry the request using a different proxy from the list (up to 5 attempts).

### 5. Using RapidAPI for 100% Reliable Deploys (Highly Recommended)
Alternatively, you can route requests through a managed scraping API on RapidAPI (like the **Instagram 120** API) which handles all proxies and blocks automatically:
1. Subscribe to the **Instagram 120** API on [RapidAPI](https://rapidapi.com/).
2. Copy your API Key (e.g., `2749778088mshd5ef03891355186p1...`).
3. In Railway, go to the **Variables** tab.
4. Add the following environment variable:
   - **`RAPIDAPI_KEY`**: `your_rapidapi_key_here`
5. The application will automatically detect this key and use RapidAPI to fetch profiles. If the key is not set (or your RapidAPI monthly quota is exhausted), the application will automatically fall back to your custom rotating proxy configuration.

---

## 🛠️ API Reference

### Get Instagram Profile

Queries public profile metadata.

- **Endpoint:** `/api/instagram/profile`
- **Method:** `GET`
- **Query Parameters:**
  - `username` (string, required): The target Instagram username.

#### Sample Request:
`GET /api/instagram/profile?username=nasa`

#### Sample Response:
```json
{
  "success": true,
  "username": "nasa",
  "name": "NASA",
  "followers_count": 97800000,
  "following_count": 182,
  "posts_count": 3954,
  "bio": "There is space for everybody. 🚀",
  "website": "nasa.gov",
  "profile_pic_url": "https://instagram.fccu...jpg",
  "profile_pic_url_hd": "https://instagram.fccu...jpg",
  "is_private": false,
  "is_verified": true,
  "id": "528574567"
}
```

#### Error Response:
```json
{
  "success": false,
  "error": "Instagram profile not found",
  "status_code": 404
}
```
