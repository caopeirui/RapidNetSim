from rapidnetsim.communication_strategy.hw_oxc_all2all_sz import HwOxcAll2AllSz

def get_hw_oxc_all2all_sz_hop_list(src, dst, NIC_num_in_a_server):
    src_port_serial = src % NIC_num_in_a_server
    src_belong = src // NIC_num_in_a_server
    dst_port_serial = dst % NIC_num_in_a_server
    dst_belong = dst // NIC_num_in_a_server
    
    if src_belong == dst_belong:
        return [dst]
    else:
        if src_port_serial == dst_belong:
            dst_mid = NIC_num_in_a_server * dst_belong + src_belong
            return [dst_mid, dst]
        src_mid = src_belong * NIC_num_in_a_server + dst_belong
        if dst_port_serial == src_belong:
            return [src_mid, dst]
        else:
            dst_mid = dst_belong * NIC_num_in_a_server + src_belong
            return [src_mid, dst_mid, dst]


if __name__ == "__main__":
    get_hw_oxc_all2all_sz_hop_list(5, 11, 4)
    test = HwOxcAll2AllSz()
    NIC_num_in_a_server = 4
    res = test.get_oxc_all2all_sz_every_round_pair(16, 4, NIC_num_in_a_server)
    
    step = 1
    for item in res:
        # every round
        record_path = {}
        for src, dst, _ in item:
            hop_list = get_hw_oxc_all2all_sz_hop_list(src, dst, NIC_num_in_a_server)
            tmp_src = src
            for next_hop in hop_list:
                if record_path.get((tmp_src, next_hop)):
                    record_path[(tmp_src, next_hop)].append('(', src // NIC_num_in_a_server, ',', src % NIC_num_in_a_server, '->', dst // NIC_num_in_a_server, ',', dst % NIC_num_in_a_server, ')')
                    print('conflict:', tmp_src, next_hop, hop_list, src, dst,  '(', src // NIC_num_in_a_server, ',', src % NIC_num_in_a_server, '->', dst // NIC_num_in_a_server, ',', dst % NIC_num_in_a_server, '), step:', step)
                else:
                    record_path[(tmp_src, next_hop)] = ['(', src // NIC_num_in_a_server, ',', src % NIC_num_in_a_server, '->', dst // NIC_num_in_a_server, ',', dst % NIC_num_in_a_server, ')']
                tmp_src = next_hop
        step += 1
