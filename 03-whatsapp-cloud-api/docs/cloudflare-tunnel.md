# Cloudflare Tunnel Setup

You need a public HTTPS URL for Meta to POST webhooks to. Meta will not accept `http://`, `localhost`, or self-signed certs. Cloudflare Tunnel gives you a working `https://…trycloudflare.com` URL in about a minute, no signup needed for a quick tunnel.

## Install cloudflared

macOS:
```bash
brew install cloudflared
```

Linux (Debian/Ubuntu):
```bash
curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared.deb
```

Windows: download the `.exe` from https://github.com/cloudflare/cloudflared/releases.

## Start a quick tunnel

Assuming n8n is running on port 5678:

```bash
cloudflared tunnel --url http://localhost:5678
```

Within a few seconds you'll see output like:

```
Your quick Tunnel has been created! Visit it at (it may take some time to be reachable):
https://friendly-otter-12-example.trycloudflare.com
```

This is your public URL. Full webhook URL for n8n = that URL + `/webhook/whatsapp`.

## Important: keep the terminal open

Quick tunnels die when you close the terminal or your machine sleeps. For the duration of the demo, keep the tunnel running. If you record the video and then start a new tunnel, the URL will change and Meta's config will need updating.

## If the URL keeps changing between sessions

Two options:

**Option A — Named tunnel (stable URL, free with a Cloudflare account and any domain).** 
Requires you to own a domain routed through Cloudflare. Documented at https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/. Adds ~15 min setup but gives you `wa.yourdomain.com` forever.

**Option B — Just start a new quick tunnel and update Meta.** For a 48-hour assessment this is fine. Update the Callback URL in Meta app → WhatsApp → Configuration and click **Verify and save**. Takes 30 seconds.

## Sanity check the tunnel

Before pointing Meta at it, curl your own tunnel:

```bash
curl "https://<your-subdomain>.trycloudflare.com/webhook/whatsapp?hub.mode=subscribe&hub.verify_token=YOUR_TOKEN&hub.challenge=1234"
```

You should get back `1234` (the challenge, echoed). If you get an n8n error page or a 404, the workflow isn't active or the path is wrong.

## Alternatives (if Cloudflare Tunnel is blocked in your region)

- **ngrok**: `ngrok http 5678` — same idea, requires a free signup for a stable-ish URL, otherwise randomised each restart.
- **Serveo**: `ssh -R 80:localhost:5678 serveo.net` — no install, but sometimes flaky.
- **localhost.run**: `ssh -R 80:localhost:5678 nokey@localhost.run` — similar.

The Meta side doesn't care which tunnel you use, as long as the URL is HTTPS and reachable.
