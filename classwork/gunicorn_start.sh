#!/bin/bash
NAME="graduation_backend"
DIR=/srv/graduation_system/classwork
WORKERS=4
BIND=127.0.0.1:6184
DJANGO_SETTINGS_MODULE=classwork.settings
DJANGO_WSGI_MODULE=classwork.wsgi
LOG_LEVEL=debug
GUNICORN_PATH=/root/miniconda3/envs/graduation_env/bin/gunicorn

# 初始化 Conda
eval "$(/root/miniconda3/bin/conda shell.bash hook)"

# 激活 Conda 环境
conda activate graduation_env

# 进入项目目录
cd $DIR

export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE
export PYTHONPATH=$DIR:$PYTHONPATH

# 启动 Gunicorn
exec $GUNICORN_PATH ${DJANGO_WSGI_MODULE}:application \
  --name $NAME \
  --workers $WORKERS \
  --bind=$BIND \
  --log-level=$LOG_LEVEL \
  --timeout 180
