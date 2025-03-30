FROM nginx:1.25

ENV WORKER_COUNT=8

RUN apt-get update && apt-get install -y bash && rm -rf /var/lib/apt/lists/*

COPY <<'EOF' /docker-entrypoint.d/30-generate-nginx-config.sh
#!/bin/bash

WORKER_COUNT=${WORKER_COUNT:-8}

cat > /etc/nginx/conf.d/default.conf << CONFEND
upstream gunicorn_cluster {
    # Use ip_hash to ensure clients are consistently routed to the same server
    ip_hash;
    
CONFEND

for (( i=1; i<=$WORKER_COUNT; i++ ))
do
    echo "    server backend${i}:5000;" >> /etc/nginx/conf.d/default.conf
done

cat >> /etc/nginx/conf.d/default.conf << CONFEND
}

server {
    listen 80;
    server_name _;

    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log;

    proxy_set_header Host \$host;
    proxy_set_header X-Real-IP \$remote_addr;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto \$scheme;

    proxy_connect_timeout 75s;
    proxy_read_timeout 300s;

    location / {
        proxy_pass http://gunicorn_cluster;
    }
}
CONFEND

EOF

RUN chmod +x /docker-entrypoint.d/30-generate-nginx-config.sh

EXPOSE 80
