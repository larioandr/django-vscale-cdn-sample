#!/usr/bin/env bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout ubio.voidhost.xyz-2019.key -out ubio.voidhost.xyz-2019.crt -config ubio.voidhost.xyz.conf
