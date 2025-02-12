from collections import UserString
from typing import ByteString


class BufStr(UserString):
    def __init__(self, buf: ByteString, indent: int  = 0):
        hex_str_list = []
        ascii_str_list = []
        indent_str = ' ' * indent
        str_list = [''.join((
            indent_str,
            '0x         00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F                  ')),
            ''.join((
                indent_str,
                '---------|-------------------------------------------------|-----------------'))
        ]

        for ii in range(len(buf)):
            if not ii % 16:
                if ii:
                    str_list.append(indent_str + ''.join(hex_str_list + ascii_str_list))
                hex_str_list = ['%08X | ' % ii]
                ascii_str_list = ['| ']
            hex_str_list.append('%02X ' % buf[ii])
            if (buf[ii] > 0x20) and (buf[ii] < 0x7F):
                ascii_str_list.append(chr(buf[ii]))
            else:
                ascii_str_list.append('.')

        str_list.append(indent_str + '%-59s%s\n' % (''.join(hex_str_list), ''.join(ascii_str_list)))

        super().__init__('\n'.join(str_list))
