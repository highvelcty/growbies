#pragma once

#include <cstddef>
#include <cstdint>
#include "command.h"

namespace transport {

    /// Pure virtual transport interface for any packet-based transport
    class ITransport {
    public:
        virtual ~ITransport() = default;

        /// Attempt to receive a packet. Returns nullptr if no packet is available.
        virtual PacketHdr* recv_packet() = 0;

        /// Send a packet of arbitrary bytes over the transport
        virtual void send_packet(const void* ptr, std::size_t packet_size) = 0;

        /// Optional: helper for sending typed payloads (similar to UsbTransport::send_payload)
        template <typename RespType>
        void send_payload(const RespType* _, const std::size_t num_bytes) {
            PacketHdr hdr{};
            hdr.resp = RespType::TYPE;
            hdr.version = RespType::VERSION;
            send_packet(&hdr, sizeof(hdr) + num_bytes);
        }
    };

} // namespace transport
