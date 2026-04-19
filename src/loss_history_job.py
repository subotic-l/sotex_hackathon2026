import subprocess
import sys
from datetime import date, timedelta
import schedule
import time

def run_for_last_10_days():
    today = date.today()
    for i in range(9, -1, -1):
        target_date = today - timedelta(days=i)
        date_str = target_date.strftime('%Y-%m-%d')
        print(f"Pokrecam za datum: {date_str}")
        result = subprocess.run(
            [sys.executable, 'calculate_losses.py', date_str],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"{date_str} uspesno")
        else:
            print(f"{date_str} greska:")
            print(result.stderr)

# Pokreni odmah za poslednjih 10 dana pri prvom pokretanju
run_for_last_10_days()

# Zatim pokreci svaki dan u 00:05
schedule.every().day.at("00:05").do(run_for_last_10_days)

print("Scheduler pokrenut, ceka 00:05...")
while True:
    schedule.run_pending()
    time.sleep(300)