import hashlib


class SignatureValidator:

    @staticmethod
    def verify(payload, signature, secret):

        expected = hashlib.sha256(
            (payload + secret).encode()
        ).hexdigest()

        return expected == signature

