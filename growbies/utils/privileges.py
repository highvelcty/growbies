import os
import pwd

from growbies.constants import USERNAME

def drop_privileges():
    """
    Drop from root if needed.
    """
    # If not root, no need to drop privileges
    if os.getuid() != 0:
        return

    pw = pwd.getpwnam(USERNAME)

    # Clear supplementary groups (optional but recommended)
    os.setgroups([])
    os.setgid(pw.pw_gid)
    os.setuid(pw.pw_uid)

    # Verify the drop
    assert os.getuid() == pw.pw_uid
    assert os.getgid() == pw.pw_gid