#include "common/protocol/cmd_exec.h"
#include "thermal/thermal.h"
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
            const auto* cmd = reinterpret_cast<CmdRead*>(usb_transport.get_cmd_buf());
            if (!error) {
                if (cmd->reset) {
                    const auto& thermal_device = ThermalDevice::get();
                    thermal_device.reset_filters();
                }
                update_telemetry(false);
            }
        }
        else if (in_packet_hdr->cmd == Cmd::GET_THERMAL_STATE) {
            auto& thermal_device = ThermalDevice::get();
            auto* resp = new (resp_buf) RespGetThermalState();
            static_cast<ThermalDeviceState&>(*resp) = thermal_device.get_state();
            usb_transport.send_resp(resp, sizeof(*resp));
        }
        else if (in_packet_hdr->cmd == Cmd::SET_THERMAL_STATE) {
            const auto* cmd = reinterpret_cast<CmdSetThermalState*>(usb_transport.get_cmd_buf());
            error = usb_transport.validate_cmd(sizeof(*cmd));
            if (!error) {
                auto& thermal_device = ThermalDevice::get();
                thermal_device.set_state(cmd->state);
                const auto resp = new (resp_buf) RespVoid;
                usb_transport.send_resp(resp, sizeof(*resp));
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

    const auto& thermal_device = ThermalDevice::get();

    thermal_device.update();

    datapoint.add<float>(EP_TEMPERATURE, thermal_device.get_temperature());
    for (auto sensor_temp : thermal_device.get_sensor_temperatures()) {
        datapoint.add<float>(EP_TEMPERATURE_SENSORS, sensor_temp);
    }

    usb_transport.send_resp(&datapoint, datapoint.get_size(), async);
}
