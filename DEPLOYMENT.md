# CodeForge AI Deployment Guide

This guide outlines how to deploy the CodeForge AI stack with the backend hosted on **Render** and the frontend hosted on **Vercel**.

---

## 1. Backend Deployment (Render)

Render's Web Services are ideal for hosting the FastAPI backend. If using Render's **Free Tier**, please note the **Cold Start Behavior** described below.

### Steps to Deploy:
1. Connect your GitHub repository to your Render account.
2. Click **New +** and select **Web Service**.
3. Choose your repository and configure the following settings:
   - **Runtime**: `Python`
   - **Build Command**: `pip install -r requirements.txt` (or if you have a custom script)
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Expand the **Advanced** section and add the following **Environment Variables**:

| Variable | Description |
|---|---|
| `DATABASE_URL` | Your PostgreSQL connection string (`postgresql://username:password@host:port/database`). |
| `JWT_SECRET` | A secure, random secret key used for signing JWT tokens. (Can also be set as `JWT_SECRET_KEY`). |
| `GROQ_API_KEY` | Your Groq Cloud API Key used to run the orchestration models. |
| `ALLOWED_ORIGIN` | The deployed Vercel frontend URL (e.g., `https://codeforge-ai.vercel.app`). This restricts CORS access strictly to your frontend domain. |

> [!WARNING]
> **Render Free Tier Cold Starts**:
> Render free instances will automatically spin down (sleep) after 15 minutes of inactivity. When a new request arrives, Render will trigger a "cold start" to spin the container back up. This process can take between **50 seconds to 2 minutes**.
>
> **Frontend Mitigation Recommendation**:
> The frontend should detect if the backend is slow to respond or returns a connection timeout. It should render a user-friendly **"Server is waking up..."** loading spinner or notification to explain the delay rather than showing a generic connection error.

---

## 2. Frontend Deployment (Vercel)

Vercel is the recommended hosting platform for the Next.js frontend.

### Steps to Deploy:
1. Import your GitHub repository into your Vercel dashboard.
2. Select the `frontend` folder as the root directory of the Vercel project.
3. Under the **Environment Variables** tab, add the following configuration:

| Variable | Value | Description |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `https://your-backend.onrender.com` | Points all Next.js API requests to your deployed Render FastAPI service (no trailing slash). |

4. Click **Deploy**. Vercel will build and assign a production URL (e.g., `https://codeforge-ai.vercel.app`).
5. Copy this URL, return to Render's environment variables dashboard, and set it as the `ALLOWED_ORIGIN` variable to allow secure CORS requests.

---

## 3. Database Migration

After the Render web service is live, run your database migrations:
1. Connect to the Render database instance.
2. Run `alembic upgrade head` from Render's shell or deploy pipeline step to ensure your PostgreSQL database is updated to the latest schema containing the `generated_files` column.
