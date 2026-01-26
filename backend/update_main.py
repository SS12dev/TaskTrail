from pathlib import Path

main_file = Path("app/main.py")
content = main_file.read_text()

# Check if already has dotenv
if "from dotenv import load_dotenv" in content:
    print("✓ dotenv already imported")
else:
    # Insert dotenv loading at the very beginning
    new_content = '''# Load environment variables before importing config
from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path(__file__).parent.parent / ".env")

''' + content

    main_file.write_text(new_content)
    print("✓ Updated main.py with dotenv loading")
