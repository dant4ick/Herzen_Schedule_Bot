import logging
import asyncio
import tarfile
from datetime import datetime, timedelta
from data.config import BASE_DIR


# Function to create a new log folder based on date
def create_log_folder():
    log_folder = BASE_DIR / 'logs' / datetime.now().strftime('%d-%m-%Y')
    if not log_folder.exists():
        log_folder.mkdir(parents=True)
    return log_folder


# Function to rotate log files
def rotate_log_file():
    current_log_folder = create_log_folder()
    current_log_file = current_log_folder / datetime.now().strftime('%H-%M-%S.log')

    if current_log_file.exists():
        return

    logging.basicConfig(
        filename=current_log_file,
        format='%(asctime)s - [%(levelname)s] - %(funcName)s - %(message)s',
        level=logging.INFO,
        force=True
    )


# Function to archive older log folders
def archive_old_logs(days: int = 7):
    old_logs_time = datetime.now() - timedelta(days=days)
    logs_folder = BASE_DIR / 'logs'

    for log_folder in logs_folder.iterdir():
        if log_folder.is_dir() and datetime.strptime(log_folder.name, '%d-%m-%Y') < old_logs_time:
            archive_path = log_folder.with_suffix('.tar.gz')
            with tarfile.open(archive_path, 'w:gz') as archive:
                archive.add(log_folder, arcname=log_folder.name)
            for log_file in log_folder.iterdir():
                log_file.unlink()  # Delete individual log files
            log_folder.rmdir()  # Delete empty log folder


# Asynchronous function that handles log rotation and archiving
async def log_rotation_and_archiving():
    while True:
        rotate_log_file()
        archive_old_logs()
        now = datetime.now()
        end_of_day = datetime(year=now.year, month=now.month, day=now.day) + timedelta(days=1)
        wait_duration = (end_of_day - now).total_seconds()
        await asyncio.sleep(wait_duration)
