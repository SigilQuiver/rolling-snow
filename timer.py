class Timer:
    def __init__(self):
        self.__timers = {}
        self.__dt = 0

    def create_timer(self, tag, max_time,progress=0):
        if not self.exists(tag):
            self.__timers[tag] = {"max_time": max_time, "time": progress*max_time}

    def check_timer(self, tag, max_time=1):
        if tag not in self.__timers:
            self.__timers[tag] = {"max_time": max_time, "time": 0}
        else:
            if self.__timers[tag]["time"] >= self.__timers[tag]["max_time"]:
                return True
        return False

    def reset_timer(self, tag):
        if tag in self.__timers:
            self.__timers[tag]["time"] = 0

    def just_set(self, tag):
        if tag in self.__timers:
            if self.__timers[tag]["time"] == 0:
                return True
        return False

    def just_finished(self, tag):
        if tag in self.__timers:
            if "finished" not in self.__timers[tag] and self.check_timer(tag, self.__timers[tag]["max_time"]):
                self.__timers[tag]["finished"] = True
                return True
        return False

    def lerp(self, tag):
        if tag in self.__timers:
            return self.__timers[tag]["time"] / self.__timers[tag]["max_time"]
        else:
            return 0

    def update(self, dt):
        self.__dt = dt
        for k in self.__timers:
            timer = self.__timers[k]
            if timer["time"] < timer["max_time"]:
                timer["time"] += dt

    def dt(self):
        return self.__dt

    def exists(self, tag):
        return tag in self.__timers

    def remove(self, tag):
        if tag in self.__timers:
            self.__timers.pop(tag)
