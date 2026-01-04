#!/bin/bash
set -e

cd $HOME/projects/page-watcher

# .env を読み込む（sh互換）
set -a
source .env
set +a

export PYTHONPATH=src

/usr/bin/python3 -m page_watcher.cli >> /var/log/cron/page_watcher.log 2>&1
