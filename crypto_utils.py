import hashlib
import ecdsa
import base58
import bech32

def sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()

def ripemd160(data: bytes) -> bytes:
    h = hashlib.new('ripemd160')
    h.update(data)
    return h.digest()

def hash160(data: bytes) -> bytes:
    return ripemd160(sha256(data))

def text_to_private_key(text: str) -> bytes:
    """Hashes text using SHA256 to create a 32-byte private key."""
    return sha256(text.encode('utf-8'))

def private_key_to_wif(priv_key: bytes, compressed: bool = True) -> str:
    """Converts a 32-byte private key to Wallet Import Format (WIF)."""
    prefix = b'\x80' # Mainnet
    payload = prefix + priv_key
    if compressed:
        payload += b'\x01'
    
    checksum = sha256(sha256(payload))[:4]
    return base58.b58encode(payload + checksum).decode('utf-8')

def private_key_to_public_key(priv_key: bytes, compressed: bool = True) -> bytes:
    """Generates a public key from a private key."""
    sk = ecdsa.SigningKey.from_string(priv_key, curve=ecdsa.SECP256k1)
    vk = sk.get_verifying_key()
    
    if not compressed:
        return b'\x04' + vk.to_string()
    
    # Compressed format
    x = vk.pubkey.point.x()
    y = vk.pubkey.point.y()
    prefix = b'\x02' if y % 2 == 0 else b'\x03'
    return prefix + x.to_bytes(32, 'big')

def pubkey_to_p2pkh(pubkey: bytes) -> str:
    """Generates a Legacy (P2PKH) address from a public key."""
    h160 = hash160(pubkey)
    prefix = b'\x00' # Mainnet P2PKH
    payload = prefix + h160
    checksum = sha256(sha256(payload))[:4]
    return base58.b58encode(payload + checksum).decode('utf-8')

def pubkey_to_p2sh_p2wpkh(pubkey: bytes) -> str:
    """Generates a Nested SegWit (P2SH-P2WPKH) address from a compressed public key."""
    h160 = hash160(pubkey)
    # P2SH(P2WPKH) script: OP_0 <20-byte-hash160(pubkey)>
    redeem_script = b'\x00\x14' + h160
    
    # Hash the redeem script
    script_hash = hash160(redeem_script)
    
    prefix = b'\x05' # Mainnet P2SH
    payload = prefix + script_hash
    checksum = sha256(sha256(payload))[:4]
    return base58.b58encode(payload + checksum).decode('utf-8')

def pubkey_to_p2wpkh(pubkey: bytes) -> str:
    """Generates a Native SegWit (P2WPKH) address from a compressed public key."""
    h160 = hash160(pubkey)
    # Convert 8-bit bytes to 5-bit words
    words = bech32.convertbits(h160, 8, 5)
    if words is None:
        raise ValueError("Failed to convert hash160 to 5-bit words for bech32 encoding")
    # Add witness version (0)
    words = [0] + words
    return bech32.bech32_encode('bc', words)

def generate_all_addresses(text: str) -> dict:
    """Generates all required addresses and WIFs from a text string."""
    priv_key = text_to_private_key(text)
    
    wif_compressed = private_key_to_wif(priv_key, compressed=True)
    wif_uncompressed = private_key_to_wif(priv_key, compressed=False)
    
    pubkey_compressed = private_key_to_public_key(priv_key, compressed=True)
    pubkey_uncompressed = private_key_to_public_key(priv_key, compressed=False)
    
    return {
        "text": text,
        "wif_compressed": wif_compressed,
        "wif_uncompressed": wif_uncompressed,
        "p2pkh_compressed": pubkey_to_p2pkh(pubkey_compressed),
        "p2pkh_uncompressed": pubkey_to_p2pkh(pubkey_uncompressed),
        "p2sh_p2wpkh_compressed": pubkey_to_p2sh_p2wpkh(pubkey_compressed),
        "p2wpkh_compressed": pubkey_to_p2wpkh(pubkey_compressed)
    }
