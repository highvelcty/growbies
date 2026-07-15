#include "common/protocol/cmd_exec.h"
#include "command.h"

void CmdExec::exec() {
    auto resp_buf = usb_transport.get_resp_buf();
    auto error = usb_transport.recv_cmd();

    if (error == ERROR_INCOMPLETE_SLIP_FRAME) {
        return;
    }

    if (!error) {
        const auto in_packet_hdr = usb_transport.get_cmd_hdr();

        if (in_packet_hdr->cmd == Cmd::READ) {
            error = usb_transport.validate_cmd(sizeof(CmdRead));
            if (!error) {
                const auto* cmd = reinterpret_cast<CmdRead*>(usb_transport.get_cmd_buf());
                update_telemetry(false);
            }
        }
        else{
            error = ERROR_UNRECOGNIZED_COMMAND;
        }
    }

    if (error) {
        auto* resp = new (resp_buf) RespError;
        resp->error = error;
        usb_transport.send_resp(resp, sizeof(*resp));
    }
}

void CmdExec::update_telemetry(const bool async) const {
    auto datapoint = DataPoint(usb_transport.get_resp_buf(), MAX_RESP_BYTES);

    usb_transport.send_resp(&datapoint, datapoint.get_size(), async);
}
