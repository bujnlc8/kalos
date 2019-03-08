#! /bin/zsh

gunicorn -w 4 demo.wsgi:app -b 0.0.0.0:10101