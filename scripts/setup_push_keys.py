"""Create the VAPID key pair for daily word push notifications (run once per stage).

Usage (on your laptop, after `awsp em`):
    pip install cryptography boto3
    python scripts/setup_push_keys.py staging
    python scripts/setup_push_keys.py prod

What it does:
- makes a new P-256 key pair;
- stores the private key in SSM Parameter Store as a SecureString at
  /vocab/<stage>/vapid-private-key (SendDailyPush reads it from there);
- prints the public key, which goes in the frontend's .env.<stage> as
  VITE_VAPID_PUBLIC_KEY.

It refuses to overwrite an existing key: a new key would silently cut off
every device already subscribed. Pass --replace only if you mean that.
"""
import base64
import sys

import boto3
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization


def b64url(data):
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode()


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ('staging', 'prod'):
        sys.exit('Usage: python scripts/setup_push_keys.py staging|prod [--replace]')
    stage = sys.argv[1]
    name = f'/vocab/{stage}/vapid-private-key'
    ssm = boto3.client('ssm', region_name='us-east-1')

    try:
        ssm.get_parameter(Name=name)
        if '--replace' not in sys.argv:
            sys.exit(f'{name} already exists. Not replacing it (that would cut off every subscribed device).')
    except ssm.exceptions.ParameterNotFound:
        pass

    key = ec.generate_private_key(ec.SECP256R1())
    private = b64url(key.private_numbers().private_value.to_bytes(32, 'big'))
    public = b64url(key.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint))

    ssm.put_parameter(Name=name, Value=private, Type='SecureString', Overwrite='--replace' in sys.argv,
                      Description='VAPID private key for daily word push notifications')
    print(f'Stored the private key at {name}.')
    print(f'Add this line to v2/.env.{"production" if stage == "prod" else "staging"} in the frontend repo:')
    print(f'VITE_VAPID_PUBLIC_KEY={public}')


if __name__ == '__main__':
    main()
