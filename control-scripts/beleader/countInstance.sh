#!/bin/bash
curl http://192.168.1.106:10089/getActiveJob | jq '.Nums'

