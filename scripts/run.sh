#!/bin/bash
set -e

cd $HOME/projects/page-watcher

# .env を読み込む（sh互換）
set -a
source .env
set +a

export PYTHONPATH=src

for TARGET in x1919 x1413 g2571 ; do
    /usr/bin/python3 -m page_watcher.cli --target $TARGET >> /var/log/cron/page_watcher-$TARGET.log 2>&1
done
