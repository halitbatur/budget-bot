# Deployment Guide - Google Cloud Run

This guide shows how to deploy the Budget Bot to Google Cloud Run.

## Prerequisites

1. [Google Cloud account](https://cloud.google.com/)
2. [gcloud CLI installed](https://cloud.google.com/sdk/docs/install)
3. Docker installed (optional, for local testing)

## Setup Google Cloud

### 1. Install and Initialize gcloud

```bash
# Install gcloud CLI (if not already installed)
# Visit: https://cloud.google.com/sdk/docs/install

# Initialize gcloud
gcloud init

# Login
gcloud auth login

# Set your project (create one if needed)
gcloud config set project YOUR_PROJECT_ID
```

### 2. Enable Required APIs

```bash
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

## Deployment Methods

### Method 1: Deploy with gcloud (Recommended)

This builds the Docker image in Cloud Build and deploys automatically:

```bash
# Deploy to Cloud Run
gcloud run deploy budget-bot \
  --source . \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars TELEGRAM_BOT_TOKEN=your_token_here,SUPABASE_URL=your_url,SUPABASE_KEY=your_key,ADMIN_USER_ID=your_id
```

**Important:** Replace the environment variables with your actual values.

### Method 2: Build Locally and Deploy

```bash
# 1. Build the Docker image
docker build -t gcr.io/YOUR_PROJECT_ID/budget-bot:latest .

# 2. Test locally (optional)
docker run -p 8080:8080 \
  -e TELEGRAM_BOT_TOKEN=your_token \
  -e SUPABASE_URL=your_url \
  -e SUPABASE_KEY=your_key \
  -e ADMIN_USER_ID=your_id \
  gcr.io/YOUR_PROJECT_ID/budget-bot:latest

# 3. Push to Google Container Registry
docker push gcr.io/YOUR_PROJECT_ID/budget-bot:latest

# 4. Deploy to Cloud Run
gcloud run deploy budget-bot \
  --image gcr.io/YOUR_PROJECT_ID/budget-bot:latest \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated
```

## Setting Environment Variables

### Option A: During Deployment (shown above)

Use `--set-env-vars` flag with comma-separated values.

### Option B: After Deployment via Console

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to Cloud Run → Select your service
3. Click "Edit & Deploy New Revision"
4. Go to "Variables & Secrets" tab
5. Add environment variables:
   - `TELEGRAM_BOT_TOKEN`
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
   - `ADMIN_USER_ID`

### Option C: Using gcloud Command

```bash
gcloud run services update budget-bot \
  --region us-central1 \
  --set-env-vars TELEGRAM_BOT_TOKEN=your_token,SUPABASE_URL=your_url,SUPABASE_KEY=your_key,ADMIN_USER_ID=your_id
```

## Verify Deployment

After deployment:

```bash
# Check service status
gcloud run services describe budget-bot --region us-central1

# View logs
gcloud run services logs read budget-bot --region us-central1
```

Then try messaging your bot on Telegram with `/start`!

## Updating the Bot

To deploy a new version:

```bash
# Method 1: Let gcloud build and deploy
gcloud run deploy budget-bot \
  --source . \
  --region us-central1

# Method 2: Build locally and deploy
docker build -t gcr.io/YOUR_PROJECT_ID/budget-bot:latest .
docker push gcr.io/YOUR_PROJECT_ID/budget-bot:latest
gcloud run deploy budget-bot \
  --image gcr.io/YOUR_PROJECT_ID/budget-bot:latest \
  --region us-central1
```

## Cost Optimization

Cloud Run pricing is based on:
- CPU time (only when bot is processing)
- Memory allocation
- Number of requests

For a personal bot with moderate usage, costs should be **very low** (likely within free tier).

### Optimize Costs:

```bash
# Deploy with minimal resources
gcloud run deploy budget-bot \
  --source . \
  --region us-central1 \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 1 \
  --cpu-throttling
```

**Note:** Telegram bots don't receive HTTP requests like web apps, so Cloud Run's auto-scaling isn't as beneficial. The bot maintains a persistent connection to Telegram.

## Monitoring

### View Logs

```bash
# Stream logs
gcloud run services logs tail budget-bot --region us-central1

# View logs in console
# https://console.cloud.google.com/run
```

### Set Up Alerts

1. Go to Cloud Console → Monitoring
2. Create alerts for:
   - Container crash rate
   - Error rate
   - Memory usage

## Troubleshooting

### Bot Not Starting

```bash
# Check logs
gcloud run services logs read budget-bot --region us-central1

# Common issues:
# - Missing environment variables
# - Invalid Telegram token
# - Supabase connection issues
```

### Update Environment Variables

```bash
gcloud run services update budget-bot \
  --region us-central1 \
  --update-env-vars KEY=value
```

### Restart Service

```bash
gcloud run services update budget-bot \
  --region us-central1 \
  --no-traffic  # This forces a restart
```

## Security Best Practices

1. ✅ **Never commit `.env` file** (already in `.gitignore`)
2. ✅ **Use Secret Manager** for sensitive data (optional but recommended):

```bash
# Store secret
echo -n "your_token" | gcloud secrets create telegram-bot-token --data-file=-

# Use in Cloud Run
gcloud run deploy budget-bot \
  --set-secrets TELEGRAM_BOT_TOKEN=telegram-bot-token:latest
```

3. ✅ **Use service role key** for Supabase (not anon key)
4. ✅ **Enable VPC connector** if you need to restrict Supabase access by IP

## Alternative: Deploy to Other Platforms

The same Docker setup works for:

- **Railway**: https://railway.app/
- **Render**: https://render.com/
- **DigitalOcean App Platform**
- **AWS ECS/Fargate**
- **Azure Container Instances**

## Questions?

Check the logs first:
```bash
gcloud run services logs tail budget-bot --region us-central1
```

Most issues are environment variable related!

