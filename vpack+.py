import struct, json, os, tempfile, webbrowser
from pathlib import Path

MAGIC = b'VPK1'

def xor_bytes(data: bytes, key: str) -> bytes:
    key_bytes = key.encode()
    key_len = len(key_bytes)
    return bytes([b ^ key_bytes[i % key_len] for i, b in enumerate(data)])

def encode_to_vpack_plus(input_mp4, output_vpack_plus):
    with open(input_mp4, 'rb') as f:
        data = f.read()

    password = input("🔐 Enter password to encrypt video: ")
    encrypted_data = xor_bytes(data, password)

    metadata = {
        "filename": os.path.basename(input_mp4),
        "size": len(data),
        "encrypted": True
    }

    json_bytes = json.dumps(metadata).encode('utf-8')
    header_len = len(json_bytes)

    with open(output_vpack_plus, 'wb') as out:
        out.write(MAGIC)
        out.write(struct.pack('>I', header_len))
        out.write(json_bytes)
        out.write(encrypted_data)

    print(f"\n✅ Encrypted and packed '{input_mp4}' into:")
    print(f"   '{output_vpack_plus}' ({len(encrypted_data)} bytes)\n")

def decode_vpack_plus(input_vpack_plus, play_immediately=True):
    with open(input_vpack_plus, 'rb') as f:
        magic = f.read(4)
        if magic != MAGIC:
            raise ValueError("Invalid VPACK+ file format.")

        header_len = struct.unpack('>I', f.read(4))[0]
        json_bytes = f.read(header_len)
        metadata = json.loads(json_bytes.decode('utf-8'))

        encrypted_video = f.read()

    if not metadata.get("encrypted"):
        raise ValueError("This file is not encrypted. Use the normal .vpack decoder.")

    password = input("🔐 Enter password to decrypt: ")
    video_data = xor_bytes(encrypted_video, password)

    if len(video_data) != metadata['size']:
        raise ValueError("❌ Incorrect password or corrupted file.")

    temp_path = os.path.join(tempfile.gettempdir(), metadata['filename'])
    with open(temp_path, 'wb') as temp_file:
        temp_file.write(video_data)

    print(f"\n✅ Decrypted and restored to temporary file:")
    print(f"   '{temp_path}'")

    if play_immediately:
        print("🎬 Attempting to play video...")
        try:
            if os.name == 'nt':
                os.startfile(temp_path)
            elif os.name == 'posix':
                import subprocess
                subprocess.run(['xdg-open', temp_path])
            else:
                webbrowser.open(temp_path)
        except Exception as e:
            print(f"⚠️ Couldn't auto-play: {e}")
    else:
        print("👋 Playback skipped (play_immediately=False)")

def main():
    try:
        print("\n🔐 VPACK+ TOOL")
        print("1. Encode MP4 to .vpack+ (encrypted)")
        print("2. Decode .vpack+ to play video")
        choice = input("Select an option (1 or 2): ")

        if choice == "1":
            mp4 = input("Enter full path to .mp4 file: ").strip('"')
            if not os.path.exists(mp4):
                print("❌ File not found.")
                return

            downloads = str(Path.home() / "Downloads")
            mp4_basename = os.path.splitext(os.path.basename(mp4))[0]
            output_file = os.path.join(downloads, mp4_basename + ".vpack+")

            print(f"Saving encrypted file as: {output_file}")
            encode_to_vpack_plus(mp4, output_file)

        elif choice == "2":
            vpack_plus = input("Enter full path to .vpack+ file: ").strip('"')
            if not os.path.exists(vpack_plus):
                print("❌ File not found.")
                return
            if not vpack_plus.endswith(".vpack+"):
                print("❌ Only .vpack+ files are supported in this tool.")
                return
            decode_vpack_plus(vpack_plus)

        else:
            print("❌ Invalid option.")

    except Exception as e:
        print(f"\n❌ Error: {e}")

    input("\n✅ Done. Press Enter to exit...")

if __name__ == "__main__":
    main()
