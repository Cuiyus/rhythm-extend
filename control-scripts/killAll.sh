#!/bin/bash
ps -ef | grep memBw|cut -c 9-15|xargs kill -9
ps -ef | grep l3|cut -c 9-15|xargs kill -9
ps -ef | grep cpu|cut -c 9-15|xargs kill -9
ps -ef | grep python|cut -c 9-15|xargs kill -9
ps -ef | grep single|cut -c 9-15|xargs kill -9
