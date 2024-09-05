import base64

import rsa


class PyAdbProtocol:
    command: int
    arg0: int
    arg1: int
    data_length: int
    data_check: int
    magic: int


class Para:
    A_SYNC = 0x434e5953
    A_CNXN = 0x4e584e43
    A_OPEN = 0x4e45504f
    A_OKAY = 0x59414b4f
    A_CLSE = 0x45534c43
    A_WRTE = 0x45545257
    A_AUTH = 0x48545541


A_VERSION = 0x01000001
MAX_PAYLOAD = 1024 * 1024
ADB_AUTH_TOKEN = 1
ADB_AUTH_SIGNATURE = 2
ADB_AUTH_RSAPUBLICKEY = 3


def adb_connect():
    """
    p->msg.command = A_AUTH;
    p->msg.arg0 = ADB_AUTH_TOKEN;
    p->msg.data_length = sizeof(t->token);
    p->payload.assign(t->token, t->token + sizeof(t->token));
    send_packet(p, t);
}
    """
    msg = PyAdbProtocol()
    msg.command = Para.A_CNXN
    msg.arg0 = A_VERSION
    msg.arg1 = MAX_PAYLOAD
    msg.data_length = 0
    msg.data_check = 0
    msg.magic = Para.A_CNXN ^ 0xffffffff
    return msg


def adb_auth_signature(token, pri_key):
    """
       p->msg.command = A_AUTH;
       p->msg.arg0 = ADB_AUTH_SIGNATURE;
       p->payload.assign(result.begin(), result.end());
       p->msg.data_length = p->payload.size();
       send_packet(p, t);
    :return:
    """
    signature = rsa.sign(token, pri_key, 'SHA-1')
    data_len = len(signature)
    # print(rsa.verify(token, signature, pubkey))
    msg = PyAdbProtocol()
    msg.command = Para.A_AUTH
    msg.arg0 = ADB_AUTH_SIGNATURE
    msg.arg1 = 0
    msg.data_length = data_len
    msg.data_check = 0
    msg.magic = Para.A_AUTH ^ 0xffffffff
    return msg, signature


def adb_auth_rsa_publickey(pubkey):
    """
        p->msg.command = A_AUTH;
        p->msg.arg0 = ADB_AUTH_RSAPUBLICKEY;
        // adbd expects a null-terminated string.
        p->payload.assign(key.data(), key.data() + key.size() + 1);
        p->msg.data_length = p->payload.size();
        send_packet(p, t);
    :return:
    """
    a = pubkey.save_pkcs1(format='DER')
    pub_key = base64.b64encode(a).decode('utf-8').encode('utf-8') + b'\0'
    data_len = len(pub_key)
    msg = PyAdbProtocol()
    msg.command = Para.A_AUTH
    msg.arg0 = ADB_AUTH_RSAPUBLICKEY
    msg.arg1 = 0
    msg.data_length = data_len
    msg.data_check = 0
    msg.magic = Para.A_AUTH ^ 0xffffffff
    return msg, pub_key


def shell_command(command):
    """
    OPEN(local-id, 0, "destination")
      p->msg.command = A_OPEN;
      p->msg.arg0 = s->id;

     // adbd used to expect a null-terminated string.
    // Keep doing so to maintain backward compatibility.
    p->payload.resize(destination.size() + 1);
    memcpy(p->payload.data(), destination.data(), destination.size());
    p->payload[destination.size()] = '\0';
    p->msg.data_length = p->payload.size();
    CHECK_LE(p->msg.data_length, s->get_max_payload());
    send_packet(p, s->transport);
    """
    msg = PyAdbProtocol()
    command = f'shell,v2,TERM=xterm-256color,raw:{command}'
    b_mes = bytes(command, 'utf-8') + b'\0'
    data_length = len(b_mes)
    msg.command = Para.A_OPEN
    msg.arg0 = 2
    msg.arg1 = 0
    msg.data_length = data_length
    msg.data_check = 0
    msg.magic = Para.A_OPEN ^ 0xffffffff
    return msg, b_mes


if __name__ == '__main__':
    pass
