import time
import threading
from scapy.all import sniff, IP, TCP, UDP

class FlowTracker:
    def __init__(self, start_time):
        self.start_time = start_time
        self.last_seen = start_time
        self.fwd_packets = 0
        self.fwd_len_total = 0
        self.fwd_len_max = 0
        self.fwd_len_min = float('inf')
        self.syn_count = 0
        self.ack_count = 0

class NetworkInterface:
    def __init__(self, feature_names):
        self.feature_names = feature_names
        self.active_flows = {}
        self.latest_feature_vector = None
        self.running = False

    def packet_callback(self, pkt):
        if IP not in pkt: return
        
        proto = pkt[IP].proto
        src_ip, dst_ip = pkt[IP].src, pkt[IP].dst
        sport = pkt.sport if (TCP in pkt or UDP in pkt) else 0
        dport = pkt.dport if (TCP in pkt or UDP in pkt) else 0
        flow_key = (src_ip, sport, dst_ip, dport, proto)
        
        curr_time = time.time()
        if flow_key not in self.active_flows:
            self.active_flows[flow_key] = FlowTracker(curr_time)
        
        flow = self.active_flows[flow_key]
        flow.last_seen = curr_time
        flow.fwd_packets += 1
        flow.fwd_len_total += len(pkt)
        flow.fwd_len_max = max(flow.fwd_len_max, len(pkt))
        flow.fwd_len_min = min(flow.fwd_len_min, len(pkt))
        
        if TCP in pkt:
            if pkt[TCP].flags & 0x02: flow.syn_count += 1
            if pkt[TCP].flags & 0x10: flow.ack_count += 1

        self.latest_feature_vector = self.generate_vector(flow, dport, proto)

    def generate_vector(self, flow, dport, proto):
        duration = (flow.last_seen - flow.start_time) * 1000000 
        vector_dict = {name: 0.0 for name in self.feature_names}
        
        # Mapping calculated values to their exact Parquet column names
        vector_dict['Protocol'] = float(proto)
        vector_dict['Destination Port'] = float(dport)
        vector_dict['Flow Duration'] = float(duration)
        vector_dict['Total Fwd Packets'] = float(flow.fwd_packets)
        vector_dict['Fwd Packet Length Max'] = float(flow.fwd_len_max)
        vector_dict['Fwd Packet Length Min'] = float(flow.fwd_len_min if flow.fwd_len_min != float('inf') else 0)
        vector_dict['SYN Flag Count'] = float(flow.syn_count)
        vector_dict['ACK Flag Count'] = float(flow.ack_count)
        
        return [vector_dict[name] for name in self.feature_names]

    def start_sniffing(self, interface=None):
        """Starts the sniffer in a background thread."""
        self.running = True
        # Use 'iface' if you are on Linux/Mac, or leave None for default Windows interface
        thread = threading.Thread(target=self._run_sniff, args=(interface,), daemon=True)
        thread.start()

    def _run_sniff(self, interface):
        print(f"[*] Sniffer started on {interface if interface else 'default interface'}...")
        sniff(prn=self.packet_callback, store=0, iface=interface)