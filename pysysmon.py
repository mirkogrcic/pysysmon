__author__ = 'mirko'
import cpu
from time import sleep, clock

f_path = "/home/mirko/pysysmon.data"

f = open(f_path, "w")


def get_info():
    cpu_u = cpu.get_cpu_time()
    ids = cpu.get_proc_ids()
    procs = {}
    sm, count = 0,0
    for id in ids:
        t1 = clock()
        try: procs[id] = cpu.get_proc_time(id)
        except: pass # exited
        t2 = clock()
        sm += t2-t1
        count += 1
    print(sm / count * 100)
    print(sm*100)
    return cpu_u, procs

def calc_time(delta):
    total = delta.user + delta.userLow + delta.sys
    total_perc = total / (total+delta.idle)
    total_perc *= 100

    sys = delta.sys
    sys_perc = sys / (total+delta.idle)
    sys_perc *= 100

    return total_perc, sys_perc

last_cpu_time = cpu.get_cpu_time()[0]
sleep(1)
samples = 0
while True:
    new_cpu_time = cpu.get_cpu_time()[0]
    delta = new_cpu_time - last_cpu_time
    percent = calc_time(delta)


    last_cpu_time = new_cpu_time
    f.write(str(percent)+",")
    samples += 1
    print(str(samples).ljust(5),
          str(percent[0]).ljust(25),
          percent[1])
    sleep(1)