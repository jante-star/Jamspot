# Retell AI Setup Guide — Jamspot

## Prerequisites
- Retell AI account at [retellai.com](https://retellai.com)
- Jamspot deployed to Fly.io (get the public URL first)
- All environment variables set in Fly.io secrets

## Step 1 — Create the Agent

1. Log into Retell dashboard
2. Create a new **LLM Agent**
3. Set the **System Prompt** from `retell/master_prompt.md`
4. Choose voice: **Lily** or **Aria** (warm, friendly tone)
5. Set response latency: **Normal**
6. Enable **End of turn detection**

## Step 2 — Register the 4 Custom Tools

For each entry in `retell/tools.json`:

1. Go to **Tools** → **Add Tool** → **Custom Tool**
2. Fill in the fields exactly as in `tools.json`
3. Replace `{{PUBLIC_BASE_URL}}` with your Fly.io URL (e.g. `https://jamspot.fly.dev`)

Tools to register:
- `get_listing` — POST `/api/retell/tools/get_listing`
- `check_availability` — POST `/api/retell/tools/check_availability`
- `create_booking` — POST `/api/retell/tools/create_booking`
- `transfer_to_host` — POST `/api/retell/tools/transfer_to_host`

## Step 3 — Configure Webhook

1. In your Retell agent settings → **Webhook**
2. Set URL: `https://your-app.fly.dev/api/retell/events`
3. Copy the **Webhook Secret** and set it as `RETELL_WEBHOOK_SECRET` in Fly.io secrets

## Step 4 — Set Environment Variables

```bash
fly secrets set RETELL_API_KEY=your_retell_api_key
fly secrets set RETELL_AGENT_ID=your_agent_id
fly secrets set RETELL_WEBHOOK_SECRET=your_webhook_secret
```

## Step 5 — Test

```bash
# Check the tools respond correctly
curl -X POST https://your-app.fly.dev/api/retell/tools/get_listing \
  -H 'Content-Type: application/json' \
  -d '{"args": {"name": "test", "city": "kingston"}, "call": {}}'
```

## Step 6 — Embed the Web Call Widget

Add to any listing page where you want the AI concierge button:

```html
<script src="https://cdn.retellai.com/retell-client-js-sdk.min.js"></script>
<button onclick="startJamiCall()">Talk to Jami</button>

<script>
async function startJamiCall() {
  const res = await fetch('/api/bookings/ai/start-call', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({
      listing_id: 'LISTING_ID_HERE',
      listing_type: 'listing'
    })
  });
  const { access_token } = await res.json();
  const retell = new RetellWebClient();
  await retell.startCall({ accessToken: access_token });
}
</script>
```

## Knowledge Base Sync (optional)

To keep Retell's knowledge base in sync with your Firestore listings, run:

```bash
python -c "from app.services.retell_kb_service import sync_all; sync_all()"
```

Or set up a scheduled task on Fly.io to run this nightly.
