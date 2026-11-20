# Zernio inbox webhook

The public webhook endpoint is:

```text
https://<your-api-host>/api/messages/webhooks/zernio/
```

Configure these environment variables on the backend:

- `ZERNIO_API_KEY`: Zernio API key used to register the endpoint.
- `ZERNIO_WEBHOOK_URL`: the public HTTPS URL above.
- `ZERNIO_WEBHOOK_SECRET`: a private signing secret shared with Zernio.

Apply the messaging migrations and register the endpoint with Zernio:

```sh
python manage.py migrate messaging
python manage.py register_zernio_webhook
```

The registration subscribes to `message.received`. The endpoint checks
`X-Zernio-Signature` against the raw request body, deduplicates on the event ID,
and saves Instagram and Facebook messages, conversation details, and attachments.
Other platform message events are acknowledged and ignored.
