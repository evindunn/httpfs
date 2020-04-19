import socket
import OpenSSL

from datetime import datetime
from OpenSSL.crypto import X509, X509Extension, FILETYPE_PEM


class X509Cert(X509):
    def __init__(self, rsa_key, country, state, locality, org, cn, issuer=None):
        super().__init__()
        self.set_pubkey(rsa_key)
        self.set_notBefore(X509Cert.get_now())
        self.set_notAfter(X509Cert.get_year_from_now())
        crt_subject = self.get_subject()
        crt_subject.C = country
        crt_subject.ST = state
        crt_subject.L = locality
        crt_subject.O = org
        crt_subject.CN = cn

        if issuer is None:
            issuer = crt_subject
            self.add_extensions([X509Extension(
                "basicConstraints".encode("utf-8"),
                critical=True,
                value="CA:TRUE".encode("utf-8")
            )])
        self.set_issuer(issuer)
        self._add_sans()

    def _add_sans(self):
        sans = [
            "DNS:*.{}".format(socket.getfqdn()),
            "IP:{}".format(X509Cert.get_current_ip())
        ]
        self.add_extensions([X509Extension(
            "subjectAltName".encode("utf-8"),
            critical=False,
            value=",".join(sans).encode("utf-8")
        )])

    def __bytes__(self):
        return OpenSSL.crypto.dump_certificate(FILETYPE_PEM, self)

    def write(self, file_name, chain=()):
        with open(file_name, 'wb') as f:
            f.write(bytes(self))
        for parent_crt in chain:
            with open(file_name, 'ab') as f:
                f.write(bytes(parent_crt))

    def sign(self, pkey):
        super().sign(pkey, "sha256")

    @staticmethod
    def get_now():
        return datetime.utcnow().strftime("%Y%m%d%H%M%SZ").encode("utf-8")

    @staticmethod
    def get_year_from_now():
        now = datetime.utcnow()
        year_out = now.replace(year=(now.year + 1))
        return year_out.strftime("%Y%m%d%H%M%SZ").encode("utf-8")

    @staticmethod
    def get_current_ip():
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("8.8.8.8", 1))
        ip = sock.getsockname()[0]
        sock.close()
        return ip
