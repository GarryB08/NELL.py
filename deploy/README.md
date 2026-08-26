# HTTPS deployment

1. Copy `.env.example` to `.env` and set strong values for `AILYN_ADMIN_PASSWORD` and `AILYN_UPDATE_SIGNING_KEY`.
2. Replace `your-domain.example` in `nginx.conf` with the real DNS name.
3. Put a Let's Encrypt certificate at `certbot/live/<domain>/` or mount the generated `/etc/letsencrypt` directory.
4. Start the app with `docker compose up -d --build`.
5. Keep the `/app` volume backed up; it contains the SQLite database, ledgers, and receipts.

The Nginx proxy terminates HTTPS and forwards Streamlit's WebSocket connection to the app container.
