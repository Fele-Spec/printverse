#!/usr/bin/env bash
set -u
for u in \
  https://docker.m.daocloud.io/v2/ \
  https://dockerproxy.com/v2/ \
  https://docker.1panel.live/v2/ \
  https://hub.rat.dev/v2/ \
  https://docker.mirrors.ustc.edu.cn/v2/
do
  code=$(curl -sS -o /dev/null -w '%{http_code}' -m 8 "$u" 2>/dev/null || true)
  echo "$code $u"
done
printf 'pypi '
curl -sS -o /dev/null -w '%{http_code}\n' -m 8 https://pypi.org/simple/ 2>/dev/null || true
printf 'hostproxy '
curl -sS -o /dev/null -w '%{http_code}\n' -m 5 http://172.20.128.1:7897 2>/dev/null || true
