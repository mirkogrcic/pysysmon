__author__ = 'mirko'

import cpu
from time import sleep, clock

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



"""def print(*args, **kwargs):
    return"""

while True:
    sleep(1)
    print("\n"*5)
    t1 = clock()
    new_cpu_u, new_procs = get_info()
    t2 = clock()
    print((t2-t1)*100)
    for i in range(len(new_cpu_u)):
        cpu_id = "" if not i else str(i-1)
        percent = cpu.calc_cpu_percent(last_cpu_u[i], new_cpu_u[i])
        percent = round(percent, 1)
        if i == 0:
            print("CPU %s | " % percent, end="")
        elif i == 1:
            print("%s" % percent, end="")
        else:
            print(", %s" % percent, end="")
    print()
    perc = []
    for proc_id in new_procs:
        try:percent = cpu.calc_proc_percent(last_procs[proc_id], new_procs[proc_id])
        except: continue # Process exited
        perc.append((percent, proc_id, new_procs[proc_id].name))
    perc = sorted(perc, reverse=True)
    for percent, proc_id, name in perc[:8]:
        print(str(round(percent,1)).ljust(8), str(proc_id).ljust(8), name)

    last_cpu_u, last_procs = new_cpu_u, new_procs
    t1 = clock()
    print((t1-t2)*100)


