# Static site: serve the prebuilt site/ folder with Caddy.
FROM caddy:2.8-alpine
COPY Caddyfile /etc/caddy/Caddyfile
COPY site/ /srv/
