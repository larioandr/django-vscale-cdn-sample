#!/usr/bin/env bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout ubio-staging.voidhost.xyz-2019.key -out ubio-staging.voidhost.xyz-2019.crt -config ubio-staging.voidhost.xyz.conf
