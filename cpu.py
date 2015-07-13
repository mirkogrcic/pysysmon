__author__ = 'mirko'
import re, os



class CPUTime:
    """
    cpu: 1 based, 0 for all
    user: time spent in userspace
    userLow: time spent in userspace with low priority
    sys: time spent in kernel space
    idle: idle time

    all times are in...
    """
    #TODO finish description
    def __init__(self, user, userLow, sys, idle):
        self.user = user
        self.userLow = userLow
        self.sys = sys
        self.idle = idle

    def __str__(self):
        return "(%s %s %s %s)" % (self.user, self.userLow, self.sys, self.idle)

    def __repr__(self):
        return self.__str__()

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
        return "(%s %s %s %s)" % (self.name,
                                      round(self.user, 2),
                                      round(self.sys, 2),
                                      self.start_ms
                                      )

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



regex_cpu_time = re.compile("cpu\d?\s+(\d+) (\d+) (\d+) (\d+)")
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

def get_cpu_time():
    """
    returns and array of CPUTime, first one[0] is all cpus combined
    :return:
    """
    f = open("/proc/stat")
    data = f.read()
    f.close()
    r = regex_cpu_time.findall(data)
    if not r: return None
    cpus = []
    for user, userLow, sys, idle in r:
        cpus.append(CPUTime(int(user), int(userLow), int(sys), int(idle)))
    return cpus

def get_proc_ids():
    dirs = os.listdir("/proc")
    ids = []
    for dir in dirs:
        if dir.isnumeric():
            ids.append(int(dir))
    return ids

def get_proc_time(id):
    f = open("/proc/%s/stat" % id)
    data = f.read()
    f.close()

    r = regex_proc_time.findall(data)
    if not r: return None
    res = ProcessTime(r[1], int(r[13])/clk_tck, int(r[14])/clk_tck, int(r[21])/clk_tck)
    return res

def calc_cpu_percent(time_low_or_delta:CPUTime, time_high:CPUTime):
    if time_high:
        delta = time_high - time_low_or_delta
    else:
        delta = time_low_or_delta
    if delta.user < 0 or delta.userLow < 0 or delta.sys < 0 or delta.idle < 0:
        return None
    total = delta.user + delta.userLow + delta.sys
    if not total: return 0
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
    print(delta, end="\t")
    if not total: return 0
    percent = total / 1
    percent *= 100
    return percent



clk_tck = get_sys_clock()




if __name__ == "__main__":
    #TODO 
    from time import sleep
    id = 2910
    last = get_proc_time(id)
    while True:
        sleep(1)
        new = get_proc_time(id)
        print(calc_proc_percent(last, new))
        last = new


    pass

