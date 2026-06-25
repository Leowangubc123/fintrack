#!/bin/sh
set -e

DNS_SERVER=$(awk '/^nameserver/ {print $2; exit}' /etc/resolv.conf)
PORT=${PORT:-80}

# nginx resolver 指令要求 IPv6 地址用方括号包裹
if echo "$DNS_SERVER" | grep -q ':'; then
    DNS_SERVER="[$DNS_SERVER]"
fi

echo "[entrypoint] PORT=$PORT DNS_SERVER=$DNS_SERVER"

sed -i "s/listen 80;/listen ${PORT};/g" /etc/nginx/conf.d/default.conf
sed -i "s|__DNS_SERVER__|${DNS_SERVER}|g" /etc/nginx/conf.d/default.conf

exec nginx -g 'daemon off;'
