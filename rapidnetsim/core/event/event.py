

STATIC_EID = 0
class Event:
    """Event abstract class, which is triggered by Simulator.
    Must be overrided.
    """
    def __init__(self, relative_time_from_now) -> None:
        """Create event which will happen the given amount of nanoseconds later.
        """
        assert relative_time_from_now >= 0

        # let import codes into funciton to void the error of cross-reference
        from rapidnetsim.core.simulator import Simulator
        self._event_time = Simulator.get_plan_event_time(relative_time_from_now)
        global STATIC_EID
        self._eid = STATIC_EID
        STATIC_EID += 1

        self._active = True


    def __lt__(self, other):
        if self._event_time < other._event_time:
            return True
        elif self._event_time == other._event_time:
            if self._type_priority < other._type_priority:
                return True
            elif self._eid < other._eid:
                return True
            else:
                return False
        else:
            return False


    def do_sth(self):
        raise NotImplemented(f"NOTICE: You need to override {self.__class__}->{sys._getframe().f_code.co_name}() in a subclass!")

    
    def get_event_time(self):
        return self._event_time


    def change_to_inactive(self):
        self._active = False


    def get_active_status(self):
        return self._active
