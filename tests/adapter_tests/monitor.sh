#!/bin/bash

inotifywait -q --time-out 10 /var/log/messages |
while read; do
    CPU_USAGE=$(top -b -n1 | grep "Cpu(s):" | awk '{print $4}')
    MEM_USAGE=$(free -m | awk 'NR==2 {print $3}' | sed 's/%//')
    DISK_USAGE=$(df -h --sync | awk '$NF=="/" {print $5}' | sed 's/%//')

    if [ $CPU_USAGE -ge 80 ]; then
        echo "CPU usage exceeded 80%!"
    fi

    if [ $MEM_USAGE -ge 80 ]; then
        echo "Memory usage exceeded 80%!"
    fi

    if [ $DISK_USAGE -ge 80 ]; then
        echo "Disk usage exceeded 80%!"
    fi
done