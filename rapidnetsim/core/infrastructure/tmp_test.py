import heapq
from flow import Flow

if __name__ == '__main__':
    flow1 = Flow(1, 2, 1, 1, 1, 1, 2, 1, 2)
    flow1.set_expected_finish_time(2)

    flow2 = Flow(2, 3, 1, 1, 1, 1, 2, 1, 2)
    flow2.set_expected_finish_time(20)

    flow3 = Flow(3, 3, 1, 1, 1, 1, 2, 1, 2)
    flow3.set_expected_finish_time(100)

    flow4 = Flow(3, 3, 1, 1, 1, 1, 2, 1, 2)
    flow4.set_expected_finish_time(1)

    flow_list = [flow1, flow2, flow3, flow4]
    print(flow_list)
    heapq.heapify(flow_list)
    print(flow_list)
    print(flow_list[0])

    print('pop print')
    # print(heapq.heappop(flow_list))
    # print(heapq.heappop(flow_list))
    # print(heapq.heappop(flow_list))
    # print(heapq.heappop(flow_list))