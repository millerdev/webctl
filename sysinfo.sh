#! /bin/bash
# A brief overview of system metrics
echo Uptime: $(uptime | sed -r 's/.*up(.*) [0-9]+ users?,/\1/')
echo ""
echo Free memory: $(free -t | grep "buffers/cache" | awk '{print $4/($3+$4) * 100}')%
echo ""
echo "Top processes"
echo "%CPU   PID COMMAND"
ps -eo pcpu,pid,args | grep -v CPU | sort -k 1 -n -r | head -4
echo ""
echo Wifi $(iwconfig 2> /dev/null | grep 'Link Quality' | sed -r 's/^ *//')
echo ""
echo "Audio playback parameters"
cat /proc/asound/card0/pcm0p/sub0/hw_params
echo ""
echo "Audio capture parameters"
cat /proc/asound/card0/pcm0c/sub0/hw_params
