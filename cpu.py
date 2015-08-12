__author__ = 'mirko'
import re, os

#TODO add __slots__

class CPUTime:
    def __init__(self, user, userLow, sys, idle):
        """
        user: time spent in userspace, int, seconds
        userLow: time spent in userspace with low priority, int, seconds
        sys: time spent in kernel space, int, seconds
        idle: idle time, int, seconds
        """
        self.user = user
        self.userLow = userLow
        self.sys = sys
        self.idle = idle

    def __repr__(self):
        return str((self.user, self.userLow, self.sys, self.idle))

    def __sub__(self, other):
        return CPUTime(
            self.user - other.user,
            self.userLow - other.userLow,
            self.sys - other.sys,
            self.idle - other.idle
        )

class ProcessTime:
    def __init__(self, name, user, sys, start_ms):
        """
        name: executable name, str
        user: cpu time in usermode, int, seconds
        sys: cpu time in kernelmode, int, seconds
        start_ms: time based on uptime when the process started, int, ms
        """
        self.name = name
        self.user = user
        self.sys = sys
        self.start_ms = start_ms

    def __repr__(self):
        return str((self.name,
                  round(self.user, 2),
                  round(self.sys, 2),
                  self.start_ms
                  ))

    def __sub__(self, other):
        if self.name != other.name or \
            self.start_ms != other.start_ms:
            return None

        return ProcessTime(
            self.name,
            self.user - other.user,
            self.sys - other.sys,
            self.start_ms
        )



regex_cpu_time = re.compile("cpu\d*\s+(\d+) (\d+) (\d+) (\d+)")
regex_cpu_time2 = re.compile("(cpu\d*\s+(\d+) (\d+) (\d+) (\d+).+)+")
regex_cpu_time3 = re.compile("(?:(cpu.+\n))+")

regex_proc_time = re.compile("\(?(.+?)\)? ")



def get_sys_uptime():
    """

    :return: (uptime, idle) in seconds
    """
    f = open("/proc/uptime") # %f(uptime) %f(idle) , all in seconds
    uptime = f.read()
    f.close()
    uptime, idle = uptime.split(" ")
    return float(uptime), float(idle)

def get_sys_clock():
    # to check in terminal: getconf CLK_TCK
    i = os.sysconf_names['SC_CLK_TCK']
    return os.sysconf(i)

cpu_stat_f = open("/proc/stat")
def get_cpu_time():
    """
    returns and array of CPUTime, first one[0] is all cpus combined
    :return:
    """
    # cache gives 40% performance improvement
    f = cpu_stat_f
    data = f.read()
    f.seek(0)
    if 1: # 0.004295000000000031 lap:0.014280000000000155
        r = regex_cpu_time.findall(data)
    elif 0: # 0.004840000000000004 lap:0.016098000000000043
        r = []
        s = data.split("\n")
        for i in s:
            if i.startswith("cpu"):
                if not r:
                    s2 = i.split(" ", 6)
                    s2.pop(1)
                else:
                    s2 = i.split(" ", 5)
                r.append(tuple(s2[1:5]))
    elif 0: # 0.006788000000000015 lap:0.02186399999999994
        r = []
        count = data.count("cpu")
        s = data.split("\n", count)[:count]
        r.append(tuple(s[0][5:].split(" ", 4)[:4])) # fist has 2 blanks
        s = s[1:]
        for i in s:
            s2 = i.split(" ", 5)[1:5]
            r.append(tuple(s2))
            print(s2)
        print(r)
    else:
        print(data.encode())
        r = regex_cpu_time3.search(data)
        print(r)
        if not r: return None
        r = r.groups()
        print(r)
        if not r: return None
        return None



    if not r: return None
    cpus = []
    for user, userLow, sys, idle in r:
        cpus.append(CPUTime(int(user)/clk_tck, int(userLow)/clk_tck, int(sys)/clk_tck, int(idle)/clk_tck))
    return cpus

def get_proc_ids():
    dirs = os.listdir("/proc")
    ids = []
    for dir in dirs:
        if dir.isnumeric():
            ids.append(int(dir))
    return ids


proc_cache = {}
def get_proc_time(id):
    # using cache performance increased by 40%
    f = proc_cache.get(id, None)
    if not f:
        try:
            f = open("/proc/%s/stat" % id)
        except FileNotFoundError:
            return None
        proc_cache[id] = f
    try:
        data = f.read()
    except ProcessLookupError:
        f.close()
        try:
            f = open("/proc/%s/stat" % id)
        except FileNotFoundError:
            return None
        proc_cache[id] = f
        data = f.read()
    f.seek(0)
    if False:
        r = regex_proc_time.findall(data) # regex was 20% slower
    else:
        r = data.split()
        if r[1][-1] != ")":
            for i,v in enumerate(r, 2):
                if v[-1] == ")":
                    r = [r[0]] + r[1:i] + r[i:]
                    break
        r[1] = r[1][1:-1] # not needed for regex
    if not r: return None
    res = ProcessTime(r[1], int(r[13])/clk_tck, int(r[14])/clk_tck, int(r[21])/clk_tck)
    return res

def calc_cpu_percent(time_low_or_delta:CPUTime, time_high:CPUTime=None):
    if time_high:
        delta = time_high - time_low_or_delta
    else:
        delta = time_low_or_delta
    if delta.user < 0 or delta.userLow < 0 or delta.sys < 0 or delta.idle < 0:
        return None
    total = delta.user + delta.userLow + delta.sys
    if not total: return 0 # no cpu time used, low interval protection
    percent = total / (total + delta.idle)
    percent *= 100
    return percent

def calc_proc_percent(time_low_or_delta:ProcessTime, time_high:ProcessTime):
    if time_high:
        delta = time_high - time_low_or_delta
    else:
        delta = time_low_or_delta
    if delta.user < 0 or delta.sys < 0:
        return None
    total = delta.user + delta.sys
    if not total: return 0
    percent = total
    percent *= 100
    return percent



clk_tck = get_sys_clock()




if __name__ == "__main__":
    from time import sleep


    last = get_cpu_time()[0]
    while True:
        sleep(1)
        new = get_cpu_time()[0]
        print(calc_cpu_percent(last, new))
        last = new


    id = 2910
    last = get_proc_time(id)
    while True:
        sleep(1)
        new = get_proc_time(id)
        print(calc_proc_percent(last, new))
        last = new


    pass

