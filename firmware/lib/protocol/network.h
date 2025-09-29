#ifndef network_h
#define network_h

#include "command.h"


#define PACKET_CRC_BYTES 2
#define PACKET_MIN_BYTES sizeof(PacketHdr) + PACKET_CRC_BYTES

PacketHdr* recv_packet();
void send_packet(const void* ptr, size_t packet_size);


#endif /* network_h */