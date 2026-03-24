import time

class FlowManager:
    def __init__(self):
        # Dictionary to store active flows: {(5-tuple): flow_statistics}
        self.active_flows = {}
        self.flow_timeout = 30 # Seconds before a flow is considered "finished"

    def get_flow_features(self, packet):
        """Processes a single packet and updates its corresponding flow."""
        if not packet.haslayer('IP'):
            return None

        # 1. Generate the 5-tuple Key
        proto = packet['IP'].proto
        src_ip = packet['IP'].src
        dst_ip = packet['IP'].dst
        
        # Handle TCP/UDP ports
        src_port = packet.sport if (packet.haslayer('TCP') or packet.haslayer('UDP')) else 0
        dst_port = packet.dport if (packet.haslayer('TCP') or packet.haslayer('UDP')) else 0
        
        flow_key = (src_ip, src_port, dst_ip, dst_port, proto)

        # 2. Update or Create Flow
        current_time = time.time()
        
        if flow_key not in self.active_flows:
            self.active_flows[flow_key] = {
                'start_time': current_time,
                'last_seen': current_time,
                'fwd_packets': 1,
                'fwd_len_total': len(packet),
                'fwd_len_max': len(packet),
                'fwd_len_min': len(packet)
            }
        else:
            flow = self.active_flows[flow_key]
            flow['last_seen'] = current_time
            flow['fwd_packets'] += 1
            flow['fwd_len_total'] += len(packet)
            flow['fwd_len_max'] = max(flow['fwd_len_max'], len(packet))
            flow['fwd_len_min'] = min(flow['fwd_len_min'], len(packet))

        # 3. Format for the Model (The "Feature Vector")
        # This MUST match the column names and order of your cicsid2017.parquet
        stats = self.active_flows[flow_key]
        duration = stats['last_seen'] - stats['start_time']
        
        # Example feature vector construction:
        features = {
            "Destination Port": dst_port,
            "Flow Duration": int(duration * 1000000), # Convert to microseconds
            "Total Fwd Packets": stats['fwd_packets'],
            "Fwd Packet Length Max": stats['fwd_len_max'],
            "Fwd Packet Length Min": stats['fwd_len_min'],
            "Flow Bytes/s": stats['fwd_len_total'] / (duration if duration > 0 else 1)
        }
        
        return features