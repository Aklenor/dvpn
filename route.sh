#!/bin/sh

prefix="$(echo $1 | grep -E '^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])($|/([0-9]|[0-2][0-9]|3[0-2])$)')"

dev="$2"

if [ -z "$prefix" ]; then
    echo "prefix not specified or '$1' is not an IP address" >&2
    exit 1
fi

if [ -z "$dev" ]; then
    echo "device is not specified" >&2
    exit 1
elif [ $(ip link show $dev >/dev/null 2>&1; echo $?) ];then
    echo "device '$dev' is not exists"
fi

if [ -n "$(ip route show root $prefix)" ]; then
    # echo already exists
    exit 0
else
    # echo adding new route
    ip route add "$prefix" dev "$dev"
fi
