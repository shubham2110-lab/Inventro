# DigitalOcean Functions Python handler signature
# Deploy with: doctl serverless deploy serverless/project.yml
import os, json, urllib.request

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
TO_EMAILS = os.getenv("ALERT_EMAILS", "")  # "ops@example.com,owner@example.com"
FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "no-reply@inventro.local")

def main(args):
    sku = args.get("sku")
    name = args.get("name")
    in_stock = args.get("in_stock")
    if not (SENDGRID_API_KEY and TO_EMAILS and sku and name):
        return {"statusCode": 200, "body": {"ok": True, "skipped": True}}

    subject = f"[Inventro] Low stock: {name} (SKU {sku})"
    content = f"Item {name} (SKU {sku}) is low on stock. Remaining: {in_stock}"

    data = {
      "personalizations": [{"to": [{"email": e.strip()} for e in TO_EMAILS.split(",") if e.strip()]}],
      "from": {"email": FROM_EMAIL},
      "subject": subject,
      "content": [{"type": "text/plain", "value": content}]
    }

    req = urllib.request.Request(
        "https://api.sendgrid.com/v3/mail/send",
        data=json.dumps(data).encode("utf-8"),
        headers={"Authorization": f"Bearer {SENDGRID_API_KEY}",
                 "Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as _:
            return {"statusCode": 200, "body": {"ok": True}}
    except Exception as e:
        return {"statusCode": 200, "body": {"ok": False, "error": str(e)}}
