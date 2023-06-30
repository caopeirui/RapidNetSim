
from rapidnetsim.core.event.event import Event
from rapidnetsim.core.simulator import Simulator

class MeasureEvent(Event):
    """Network info measurement event.
    """
    def __init__(self, measure_sampling_interval) -> None:
        super().__init__(measure_sampling_interval)
        self._type_priority = 3
        self._measure_sampling_interval = measure_sampling_interval
        

    def do_sth(self):
        # Record occupied link informations.
        infra = Simulator.get_infrastructure()
        link_flow_occupy_dict = infra.get_link_flow_occupy_dict(-2)
        for (src, dst), occupied_list in link_flow_occupy_dict.items():
            occupied_num = len(occupied_list)
            if occupied_num > 0:
                the_link_capacity = infra.get_the_links_capacity(src, dst, -2)
                ave_bandwidth = the_link_capacity / occupied_num
                Simulator.occupied_num_logger.write(f'{Simulator.get_current_time()},{src},{dst},{occupied_num},{ave_bandwidth}\n')


        if len(Simulator._event_q) > 0 or len(Simulator.WAITING_TASK_LIST) > 0:
            Simulator.register_event(MeasureEvent(self._measure_sampling_interval))
        
        