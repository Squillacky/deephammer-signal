import subprocess
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.deephammer.config import config

def check_ytdlp():
    try:
        result = subprocess.run(
            ["yt-dlp", "--version"],
            capture_output=True, text=True, timeout=10
        )
        version = result.stdout.strip()
        print(f"  yt-dlp {version}")
        return True
    except Exception as e:
        print(f"  yt-dlp failed: {e}")
        return False

def check_deepgram():
    try:
        from deepgram import DeepgramClient
        client = DeepgramClient(api_key=config.DEEPGRAM_API_KEY)
        print(f"  Deepgram SDK v5 loaded (key: ...{config.DEEPGRAM_API_KEY[-4:]})")
        return True
    except Exception as e:
        print(f"  Deepgram failed: {e}")
        return False

def check_anthropic():
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=24,
            messages=[{"role": "user", "content": "Reply with only: SIGNAL ONLINE"}]
        )
        reply = response.content[0].text.strip()
        print(f"  Anthropic responded: {reply}")
        return True
    except Exception as e:
        print(f"  Anthropic failed: {e}")
        return False

if __name__ == "__main__":
    print("DeepHammer Verification")

    validation = config.validate()
    if not validation["valid"]:
        print(f"  Config issues: {validation['issues']}")
        sys.exit(1)
    print("  Config loaded")

    print("Testing connections:")
    r1 = check_ytdlp()
    r2 = check_deepgram()
    r3 = check_anthropic()

    if all([r1, r2, r3]):
        print("ALL SYSTEMS GO")
    else:
        print("Fix the failures above before continuing")
