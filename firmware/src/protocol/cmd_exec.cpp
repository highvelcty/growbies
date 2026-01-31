#include "cmd_exec.h"
#include "command.h"
#include "measure/stack.h"
#include "remote/remote_out.h"

void CmdExec::exec() {
    auto resp_buf = usb_transport.get_resp_buf();
    auto error = usb_transport.recv_cmd();

    if (error == ERROR_INCOMPLETE_SLIP_FRAME) {
        return;
    }

    if (!error) {
        const auto in_packet_hdr = usb_transport.get_cmd_hdr();

        if (in_packet_hdr->cmd == Cmd::GET_CALIBRATION) {
            error = usb_transport.validate_cmd(sizeof(CmdGetCalibration));
            if(!error) {
                auto* resp = new (resp_buf) RespGetCalibration();
                memcpy(&resp->calibration, calibration_store->view(), sizeof(resp->calibration));
                usb_transport.send_resp(resp, sizeof(*resp));
            }
        }
        else if (in_packet_hdr->cmd == Cmd::SET_CALIBRATION) {
            const auto* cmd = reinterpret_cast<CmdSetCalibration*>(usb_transport.get_cmd_buf());
            error = usb_transport.validate_cmd(sizeof(*cmd));
            if (!error) {
                const auto resp = new (resp_buf) RespVoid;
                if (cmd->init) {
                    calibration_store->init();
                }
                else {
                    calibration_store->put(cmd->calibration);
                }

                usb_transport.send_resp(resp, sizeof(*resp));
            }
        }
        else if (in_packet_hdr->cmd == Cmd::GET_IDENTIFY) {
            error = usb_transport.validate_cmd(sizeof(CmdGetIdentify));
            if (!error) {
                auto* resp = new (resp_buf) RespGetIdentify;
                memcpy(&resp->identify, identify_store->view(), sizeof(resp->identify));
                usb_transport.send_resp(resp, sizeof(*resp));
            }
        }
        else if (in_packet_hdr->cmd == Cmd::SET_IDENTIFY) {
            const auto* cmd = reinterpret_cast<CmdSetIdentify*>(usb_transport.get_cmd_buf());
            error = usb_transport.validate_cmd(sizeof(*cmd));
            if (!error) {
                const auto* resp = new (resp_buf) RespVoid;
                if (cmd->init) {
                    identify_store->init();
                }
                else {
                    RemoteOut& menu = RemoteOut::get();
                    identify_store->put(cmd->identify);
                    menu.synchronize();
                    menu.render();
                }
                usb_transport.send_resp(resp, sizeof(*resp));
            }
        }
        else if (in_packet_hdr->cmd == Cmd::POWER_ON_HX711) {
            error = usb_transport.validate_cmd(sizeof(CmdPowerOnHx711));
            if (!error) {
                const auto& measurement_stack = growbies::MeasurementStack::get();
                measurement_stack.power_on();
                const auto* resp = new (resp_buf) RespVoid;

                usb_transport.send_resp(resp, sizeof(*resp));
            }
        }
        else if (in_packet_hdr->cmd == Cmd::POWER_OFF_HX711) {
            error = usb_transport.validate_cmd(sizeof(CmdPowerOffHx711));
            if (!error) {
                const auto& measurement_stack = growbies::MeasurementStack::get();
                measurement_stack.power_off();
                const auto* resp = new (resp_buf) RespVoid;
                usb_transport.send_resp(resp, sizeof(*resp));
            }
        }
        else if (in_packet_hdr->cmd == Cmd::READ) {
            error = usb_transport.validate_cmd(sizeof(CmdRead));
            if (!error) {
                const auto& measurement_stack = growbies::MeasurementStack::get();
                measurement_stack.update();
                update_telemetry(false);
            }
        }
        else if (in_packet_hdr->cmd == Cmd::GET_TARE) {
            error = usb_transport.validate_cmd(sizeof(CmdGetTare));
            if (!error) {
                auto* resp = new (resp_buf) RespGetTare;
                memcpy(&resp->tare, tare_store->view(), sizeof(resp->tare));
                usb_transport.send_resp(resp, sizeof(*resp));
            }
        }
        else if (in_packet_hdr->cmd == Cmd::SET_TARE) {
            const auto* cmd = reinterpret_cast<CmdSetTare*>(usb_transport.get_cmd_buf());
            error = usb_transport.validate_cmd(sizeof(*cmd));
            if (!error) {
                const auto* resp = new (resp_buf) RespVoid;
                if (cmd->init) {
                    tare_store->init();
                }
                else {
                    tare_store->put(cmd->tare);
                }
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
    const auto& stack = MeasurementStack::get();

    stack.update();

    for (auto tare : tare_store->payload()->tares) {
        datapoint.add<float>(EP_TARE, tare.value);
    }

    datapoint.add<float>(EP_MASS, stack.aggregate_mass().total_mass());
    datapoint.add<float>(EP_TEMPERATURE, stack.aggregate_temp().average());

    for (auto sensor_mass : stack.aggregate_mass().sensor_masses()) {
        datapoint.add<float>(EP_MASS_SENSOR, sensor_mass);
    }

    for (auto sensor_temp : stack.aggregate_temp().sensor_temperatures()) {
        datapoint.add<float>(EP_TEMPERATURE_SENSORS, sensor_temp);
    }

    usb_transport.send_resp(&datapoint, datapoint.get_size(), async);
}
