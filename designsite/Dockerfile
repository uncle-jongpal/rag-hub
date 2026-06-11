FROM nginx:alpine

COPY . /usr/share/nginx/html/

RUN printf 'server {\n\
    listen 8502;\n\
    server_name _;\n\
    root /usr/share/nginx/html;\n\
    index index.html;\n\
    charset utf-8;\n\
    gzip on;\n\
    gzip_types text/plain text/css application/javascript text/javascript application/json;\n\
    gzip_min_length 1024;\n\
    types {\n\
        text/html        html htm;\n\
        text/css         css;\n\
        text/javascript  js;\n\
        text/babel       jsx;\n\
        image/png        png;\n\
        image/svg+xml    svg;\n\
        application/json json;\n\
    }\n\
    resolver 127.0.0.11 valid=10s;\n\
    location /api/ {\n\
        set $backend http://backend:8000;\n\
        proxy_pass $backend;\n\
        proxy_set_header Host $host;\n\
        proxy_connect_timeout 10s;\n\
        proxy_read_timeout 300s;\n\
    }\n\
    location / {\n\
        try_files $uri $uri/ /index.html;\n\
    }\n\
}\n' > /etc/nginx/conf.d/default.conf

EXPOSE 8502

HEALTHCHECK --interval=15s --timeout=5s --start-period=8s --retries=3 \
  CMD wget -q --spider http://localhost:8502/ || exit 1
