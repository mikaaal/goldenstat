#!/usr/bin/env python3
"""
Railway Database Sync Script

Synkroniserar goldenstat.db med Railway's persistent volume via Railway CLI
"""
import os
import sys
import subprocess
import argparse
from pathlib import Path


class RailwayDBSync:
    """Hanterar synkronisering av databas med Railway"""

    def __init__(self):
        self.db_file = Path("goldenstat.db")
        self.railway_db_path = "/app/data/goldenstat.db"  # Path i Railway container

        # Kolla Railway credentials
        self.project_id = os.getenv('RAILWAY_PROJECT_ID')
        self.service_id = os.getenv('RAILWAY_SERVICE_ID')
        self.token = os.getenv('RAILWAY_TOKEN')

        if not all([self.project_id, self.service_id, self.token]):
            print("⚠️  VARNING: Railway credentials saknas i miljövariabler")
            print("   Behöver: RAILWAY_PROJECT_ID, RAILWAY_SERVICE_ID, RAILWAY_TOKEN")
            if '--help' not in sys.argv and '-h' not in sys.argv:
                sys.exit(1)

    def run_railway_command(self, cmd: list, check=True):
        """Kör Railway CLI kommando"""
        env = os.environ.copy()
        env['RAILWAY_TOKEN'] = self.token

        try:
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                check=check
            )
            return result
        except subprocess.CalledProcessError as e:
            print(f"❌ Railway kommando misslyckades: {e}")
            print(f"   stdout: {e.stdout}")
            print(f"   stderr: {e.stderr}")
            raise

    def download_database(self):
        """Ladda ner databas från Railway"""
        print("📥 Laddar ner databas från Railway...")

        try:
            # Använd Railway run för att kopiera filen
            # Vi kör ett kommando som cattar databasen och sparar lokalt
            cmd = [
                'railway', 'run',
                '--service', self.service_id,
                'cat', self.railway_db_path
            ]

            result = self.run_railway_command(cmd, check=False)

            if result.returncode == 0 and result.stdout:
                # Spara utdata som databas
                with open(self.db_file, 'wb') as f:
                    f.write(result.stdout.encode('latin1'))  # Binary data
                print(f"✅ Databas nedladdad till {self.db_file}")
                print(f"   Storlek: {self.db_file.stat().st_size / 1024 / 1024:.2f} MB")
                return True
            else:
                print("⚠️  Ingen databas hittades på Railway (första körning?)")
                print("   Skapar ny databas lokalt...")
                return False

        except Exception as e:
            print(f"⚠️  Kunde inte ladda ner databas: {e}")
            print("   Fortsätter med lokal databas...")
            return False

    def upload_database(self):
        """Ladda upp databas till Railway"""
        if not self.db_file.exists():
            print(f"❌ Ingen databas att ladda upp: {self.db_file}")
            return False

        print("📤 Laddar upp databas till Railway...")

        try:
            db_size_mb = self.db_file.stat().st_size / 1024 / 1024
            print(f"   Databas storlek: {db_size_mb:.2f} MB")

            # Först, kopiera databasen med Railway CLI volume
            # Vi använder ett temporary Python script som körs på Railway
            upload_script = f"""
import sys
with open('{self.railway_db_path}', 'wb') as f:
    f.write(sys.stdin.buffer.read())
print('Database uploaded successfully')
"""

            # Kör upload via Railway
            cmd = [
                'railway', 'run',
                '--service', self.service_id,
                'python', '-c', upload_script
            ]

            # Skicka databasen via stdin
            with open(self.db_file, 'rb') as db:
                result = subprocess.run(
                    cmd,
                    stdin=db,
                    capture_output=True,
                    text=True,
                    env={**os.environ, 'RAILWAY_TOKEN': self.token}
                )

            if result.returncode == 0:
                print("✅ Databas uppladdad till Railway")
                return True
            else:
                print(f"❌ Uppladdning misslyckades: {result.stderr}")
                return False

        except Exception as e:
            print(f"❌ Fel vid uppladdning: {e}")
            return False

    def check_railway_db_status(self):
        """Kolla status på Railway-databasen"""
        print("🔍 Kollar Railway databas status...")

        try:
            cmd = [
                'railway', 'run',
                '--service', self.service_id,
                'test', '-f', self.railway_db_path, '&&', 'ls', '-lh', self.railway_db_path
            ]

            result = self.run_railway_command(cmd, check=False)

            if result.returncode == 0:
                print("✅ Databas finns på Railway:")
                print(result.stdout)
                return True
            else:
                print("⚠️  Ingen databas på Railway ännu")
                return False

        except Exception as e:
            print(f"⚠️  Kunde inte kolla status: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(
        description='Synkronisera databas med Railway'
    )
    parser.add_argument(
        'action',
        choices=['download', 'upload', 'status'],
        help='Åtgärd att utföra'
    )

    args = parser.parse_args()

    sync = RailwayDBSync()

    if args.action == 'download':
        success = sync.download_database()
        sys.exit(0 if success else 1)

    elif args.action == 'upload':
        success = sync.upload_database()
        sys.exit(0 if success else 1)

    elif args.action == 'status':
        sync.check_railway_db_status()
        sys.exit(0)


if __name__ == '__main__':
    main()
