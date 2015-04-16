netdev
========

A device manager for network devices.

## Usage ##

    sudo ./netdev.py

## Example rule file ##

    # This line will be ignored
    ACTION=="discover", HOSTNAME=="172.16.1.2", RUN+="echo FOUND 172.16.1.2"
    ACTION=="lost", HOSTNAME=="172.16.1.2", RUN+="echo LOST 172.16.1.2"

    ACTION=="discover", HOSTNAME=="192.168.1.24", RUN+="echo FOUND 24"
    ACTION=="lost", HOSTNAME=="192.168.1.24", RUN+="echo LOST 24"

The above rule file handles discovering two different network devices: 172.16.1.2, and 192.168.1.24.

All rule files must be stored in /etc/netdev/rules.d/ and have .rules as the file extension.