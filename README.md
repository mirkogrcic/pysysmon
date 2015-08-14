# pysysmon
Linux system monitor for CPU,GPU,Memory and Disk usage, realtime and logging for later. I'm planning to make a diagram gui just like the Proces Hacker(Windows only) resource window just with more features, will port it to C++ when it's done(hard to test on C++ for me).

# Gui Features
- Scrolling on x axis, keyboard(left,right), mouse(wheel, hold leftB and move): DONE
- Dynamic distance between values: DONE
- Process list(name, %) on hover on the left side of graph
- Highlight items on hover: CURRENT

# Deamon features
- CPU usage(per process and total)
- GPU usage(total), not sure if per process is possible
- Memory usage(physical, virtual, swap...)
- Disk usage
- Network usage
- Ping
