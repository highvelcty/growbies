#pragma once

#include "transport/usb.h"

class CmdExec {
public:
    // Get the single global instance
    static CmdExec& get() {
        static CmdExec instance;  // created on first call, destroyed on program exit
        return instance;
    }

    // Delete copy/move constructors and assignment for singleton
    CmdExec(const CmdExec&) = delete;
    CmdExec& operator=(const CmdExec&) = delete;
    CmdExec(CmdExec&&) = delete;
    CmdExec& operator=(CmdExec&&) = delete;

    void exec();

    void update_telemetry(bool async = false) const;

private:
    // Private constructor for singleton
    CmdExec() = default;

    transport::UsbTransport usb_transport{};
};
