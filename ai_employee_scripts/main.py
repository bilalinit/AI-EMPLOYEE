"""
AI Employee Scripts - Main Entry Point

Personal AI Employee Hackathon 0 - Silver Tier

Usage:
    python main.py                    # Show status
    python main.py filesystem         # Run filesystem watcher
    python main.py gmail              # Run Gmail watcher
    python main.py linkedin           # Run LinkedIn watcher
    python main.py --status           # Check system status
"""

import sys
import os
from pathlib import Path

# Add watchers directory to path
sys.path.insert(0, str(Path(__file__).parent / "watchers"))


def print_banner():
    """Print the AI Employee banner."""
    print("=" * 55)
    print(" " * 10 + "AI EMPLOYEE SCRIPTS")
    print(" " * 8 + "Personal AI Employee Hackathon 0")
    print(" " * 15 + "Silver Tier")
    print("=" * 55)
    print()


def get_vault_path():
    """Get the vault path from environment or default."""
    vault_path = os.getenv("VAULT_PATH", "../AI_Employee_Vault")
    vault_path = Path(vault_path).resolve()

    if not vault_path.exists():
        print(f"Error: Vault not found at {vault_path}")
        print("Please set VAULT_PATH environment variable or create the vault.")
        sys.exit(1)

    return vault_path


def check_status():
    """Check and display system status."""
    vault_path = get_vault_path()

    print("System Status:")
    print("-" * 40)

    # Check vault folders
    folders = ["Inbox", "Needs_Action", "Plans", "Pending_Approval",
               "Approved", "Rejected", "Done", "Logs"]

    for folder in folders:
        folder_path = vault_path / folder
        status = "✓" if folder_path.exists() else "✗"
        file_count = len(list(folder_path.glob("*"))) if folder_path.exists() else 0
        print(f"  {status} /{folder}/ ({file_count} files)")

    print("-" * 40)

    # Check key files
    key_files = ["Dashboard.md", "Company_Handbook.md"]
    for filename in key_files:
        filepath = vault_path / filename
        status = "✓" if filepath.exists() else "✗"
        print(f"  {status} {filename}")

    print()
    print(f"Vault location: {vault_path}")
    print()

    # Check credentials
    scripts_dir = Path(__file__).parent
    print("Credentials:")
    if (scripts_dir / "credentials.json").exists():
        print("  ✓ Gmail credentials.json")
    else:
        print("  ✗ Gmail credentials.json (not found)")
    print()


def run_filesystem_watcher():
    """Run the filesystem watcher."""
    from filesystem_watcher import FileSystemWatcher

    vault_path = get_vault_path()
    print(f"Starting File System Watcher...")
    print(f"Vault: {vault_path}")
    print()

    watcher = FileSystemWatcher(str(vault_path))
    watcher.run()


def run_gmail_watcher():
    """Run the Gmail watcher."""
    from gmail_watcher import GmailWatcher

    vault_path = get_vault_path()
    scripts_dir = Path(__file__).parent

    print(f"Starting Gmail Watcher...")
    print(f"Vault: {vault_path}")
    print(f"Credentials: {scripts_dir / 'credentials.json'}")
    print()

    try:
        watcher = GmailWatcher(str(vault_path))
        watcher.run()
    except FileNotFoundError as e:
        print(f"\n❌ {e}")
        print("\nTo set up Gmail API:")
        print("1. Go to https://console.cloud.google.com")
        print("2. Create project → Enable Gmail API")
        print("3. Create OAuth 2.0 credentials (Desktop app)")
        print("4. Download credentials.json to this directory")


def run_linkedin_watcher():
    """Run the LinkedIn watcher."""
    from linkedin_watcher import LinkedInWatcher

    vault_path = get_vault_path()
    print(f"Starting LinkedIn Watcher...")
    print(f"Vault: {vault_path}")
    print()

    try:
        watcher = LinkedInWatcher(str(vault_path))
        watcher.run()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nLinkedIn Watcher requires Playwright setup.")
        print("First run will open browser for LinkedIn login.")


def main():
    """Main entry point."""
    print_banner()

    # Parse arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "filesystem":
            run_filesystem_watcher()
        elif command == "gmail":
            run_gmail_watcher()
        elif command == "linkedin":
            run_linkedin_watcher()
        elif command in ("--status", "status", "-s"):
            check_status()
        elif command in ("--help", "help", "-h"):
            print("Usage:")
            print("  python main.py              - Show status")
            print("  python main.py filesystem   - Run filesystem watcher")
            print("  python main.py gmail        - Run Gmail watcher")
            print("  python main.py linkedin     - Run LinkedIn watcher")
            print("  python main.py --status     - Check system status")
            print("  python main.py --help       - Show this help")
        else:
            print(f"Unknown command: {command}")
            print("Run 'python main.py --help' for usage information")
            sys.exit(1)
    else:
        # Default: show status
        check_status()
        print("To start a watcher, run:")
        print("  python main.py filesystem")
        print("  python main.py gmail")
        print("  python main.py linkedin")


if __name__ == "__main__":
    main()
