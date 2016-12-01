import os
import ssl

import wbull.util


def load_self_signed_cert(ssl_context: ssl.SSLContext):
    cert_dir = os.path.dirname(__file__)
    cert_path = wbull.util.get_package_data_path('data/mitm_client.crt', cert_dir)
    key_path = wbull.util.get_package_data_path('data/mitm_client.key', cert_dir)

    ssl_context.load_cert_chain(cert_path, key_path)
