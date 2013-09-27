#!/usr/bin/bash

screen -ls | grep 280logger

if [ "$?" -ne "0" ]; then
	screen -d -m -S 280logger bash -c "exec bash -l -c 'workon submission-logger; python server.py'"
fi
