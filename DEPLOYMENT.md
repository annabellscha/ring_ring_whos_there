# Deployment Guide - Render (Free & Easy)

## Prerequisites
- GitHub account
- Render account (free, no credit card required)
- Your API keys ready (ElevenLabs, Langfuse, Ring credentials)

## Step-by-Step Deployment

### 1. Push Code to GitHub

If you haven't already, create a GitHub repository and push your code:

```bash
# Initialize git (if not already done)
git init
git add .
git commit -m "Ready for deployment"

# Create a new repository on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git branch -M main
git push -u origin main
```

### 2. Deploy to Render

#### Option A: Using render.yaml (Easiest)

1. Go to [render.com](https://render.com) and sign up/login
2. Click **"New +"** → **"Blueprint"**
3. Connect your GitHub repository
4. Render will automatically detect `render.yaml` and configure everything
5. Click **"Apply"**

#### Option B: Manual Setup

1. Go to [render.com](https://render.com) and sign up/login
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Configure:
   - **Name**: `ring-ring-whos-there`
   - **Environment**: `Docker`
   - **Region**: Choose closest to you
   - **Branch**: `main`
   - **Plan**: `Free`

### 3. Configure Environment Variables

In the Render dashboard, add these environment variables:

**Required API Keys:**
- `ELEVENLABS_API_KEY`: Your ElevenLabs API key
- `ELEVENLABS_VOICE_ID`: Your selected voice ID
- `LANGFUSE_PUBLIC_KEY`: Your Langfuse public key
- `LANGFUSE_SECRET_KEY`: Your Langfuse secret key

**Ring Credentials:**
- `RING_USERNAME`: Your Ring account email
- `RING_PASSWORD`: Your Ring account password
- `RING_2FA_TOKEN`: (Optional) If using 2FA

**Application Settings:**
- `PASSWORDS`: `alohomora,mellon,friend,simsalabim`
- `FUZZY_THRESHOLD`: `80`
- `RECORDING_DURATION`: `8`
- `MAX_ATTEMPTS`: `3`
- `ENVIRONMENT`: `production`
- `LOG_LEVEL`: `INFO`
- `LANGFUSE_HOST`: `https://cloud.langfuse.com`

### 4. Deploy!

Click **"Create Web Service"** or **"Apply"**. Render will:
1. Pull your code from GitHub
2. Build the Docker container
3. Deploy your application
4. Give you a public HTTPS URL (e.g., `https://ring-ring-whos-there.onrender.com`)

### 5. Verify Deployment

Once deployed, test your endpoints:

```bash
# Health check
curl https://YOUR_APP_URL.onrender.com/health

# Test complete flow
curl -X POST https://YOUR_APP_URL.onrender.com/test/complete-flow
```

### 6. Configure Ring Webhook

Once deployed, you'll need to configure Ring to send webhook events to your Render URL:

**Webhook URL:** `https://YOUR_APP_URL.onrender.com/webhooks/ring/doorbell`

Note: Ring doesn't have an official webhook API, so you may need to use polling or alternative methods.

## Important Notes

### Free Tier Limitations
- **Spin down**: Service spins down after 15 minutes of inactivity
- **Spin up time**: Takes ~30 seconds to wake up on first request
- **Monthly hours**: 750 hours/month (plenty for testing)

### Upgrading to Paid Plan
If you need:
- Always-on service (no spin down)
- More memory/CPU
- Custom domain

Upgrade to the **Starter plan** ($7/month) in Render dashboard.

## Troubleshooting

### Build Fails
- Check logs in Render dashboard
- Verify Dockerfile syntax
- Ensure all dependencies are in requirements.txt

### Environment Variables Not Working
- Double-check variable names (case-sensitive)
- Ensure no extra spaces in values
- Redeploy after adding new variables

### Application Crashes
- Check logs: Click on your service → "Logs" tab
- Common issues:
  - Missing API keys
  - Invalid credentials
  - Audio file paths

## Auto-Deploy on Push

Render automatically redeploys when you push to GitHub:

```bash
git add .
git commit -m "Update feature"
git push
```

Render will detect the push and redeploy automatically!

## Cost Breakdown

**Free Tier (Recommended for this project):**
- Cost: $0/month
- Limitations: Spins down after inactivity
- Perfect for: Personal projects, testing, demos

**Starter Plan (If you need always-on):**
- Cost: $7/month
- Benefits: No spin down, better performance
- Perfect for: Production use with Ring integration

## Next Steps

1. ✅ Deploy to Render
2. ✅ Test all endpoints
3. ⏳ Set up Ring webhook integration
4. ⏳ Monitor with Langfuse dashboard
5. ⏳ Test with real doorbell

Need help? Check the logs in Render dashboard or the main README.md for testing commands.
