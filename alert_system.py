import time
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import schedule
import logging
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Database Configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', 5432),
    'database': os.getenv('DB_NAME', 'your_database'),
    'user': os.getenv('DB_USER', 'your_username'),
    'password': os.getenv('DB_PASSWORD', 'your_password'),
    'table_name': os.getenv('DB_TABLE', 'your_table')
}

# Email Configuration
EMAIL_CONFIG = {
    'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
    'smtp_port': int(os.getenv('SMTP_PORT', 587)),
    'sender_email': os.getenv('SENDER_EMAIL', 'your_email@gmail.com'),
    'sender_password': os.getenv('SENDER_PASSWORD', 'your_app_password'),
    'recipient_email': os.getenv('RECIPIENT_EMAIL', 'recipient@gmail.com'),
    'subject_prefix': os.getenv('EMAIL_SUBJECT_PREFIX', 'Database Alert')
}

# Monitor Configuration
MONITOR_CONFIG = {
    'check_interval_minutes': int(os.getenv('CHECK_INTERVAL', 5)),
    'time_window_minutes': int(os.getenv('TIME_WINDOW', 30)),
    'status_id': int(os.getenv('TARGET_STATUS_ID', 3)),
    'enable_email': os.getenv('ENABLE_EMAIL', 'true').lower() == 'true',
    'enable_console': os.getenv('ENABLE_CONSOLE', 'true').lower() == 'true'
}


class DatabaseTrigger:
    def __init__(self, db_config, monitor_config):
        self.db_config = db_config
        self.monitor_config = monitor_config
        self.processed_ids = set()  # Track already processed rows

    def connect_db(self):
        """Create PostgreSQL database connection"""
        try:
            conn = psycopg2.connect(
                host=self.db_config['host'],
                port=self.db_config['port'],
                database=self.db_config['database'],
                user=self.db_config['user'],
                password=self.db_config['password']
            )
            return conn
        except psycopg2.Error as e:
            logging.error(f"PostgreSQL connection error: {e}")
            return None

    def check_recent_updates(self):
        """Check for rows updated in last specified minutes with target status_id"""
        conn = self.connect_db()
        if not conn:
            return []

        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # Query for recent updates using PostgreSQL interval
            query = f"""
            SELECT id, updated_at, status_id FROM {self.db_config['table_name']} 
            WHERE status_id = %s 
            AND api_data_source = 1
            AND updated_at >= NOW() - INTERVAL '%s minutes'
            ORDER BY updated_at DESC
            """

            cursor.execute(query, (
                self.monitor_config['status_id'],
                self.monitor_config['time_window_minutes']
            ))
            rows = cursor.fetchall()

            # Filter out already processed rows
            new_rows = [row for row in rows if row['id'] not in self.processed_ids]

            # Add new row IDs to processed set
            for row in new_rows:
                self.processed_ids.add(row['id'])

            return new_rows

        except psycopg2.Error as e:
            logging.error(f"PostgreSQL query error: {e}")
            return []
        finally:
            conn.close()

    def send_email_notification(self, rows, email_config):
        """Send email notification for detected rows"""
        if not rows:
            return

        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = email_config['sender_email']
            msg['To'] = email_config['recipient_email']
            msg[
                'Subject'] = f"{email_config['subject_prefix']}: {len(rows)} rows with status_id={self.monitor_config['status_id']} detected"

            # Create email body
            body = f"Database Alert Report\n"
            body += f"========================\n\n"
            body += f"Found {len(rows)} rows with status_id = {self.monitor_config['status_id']} "
            body += f"updated in the last {self.monitor_config['time_window_minutes']} minutes.\n\n"
            body += f"Details:\n"
            body += f"--------\n"

            for i, row in enumerate(rows, 1):
                body += f"\n{i}. Record ID: {row['id']}\n"
                body += f"   Updated At: {row['updated_at']}\n"
                body += f"   Status ID: {row['status_id']}\n"

                # Add other relevant fields (customize based on your table structure)
                for key, value in row.items():
                    if key not in ['id', 'updated_at', 'status_id']:
                        body += f"   {key.title()}: {value}\n"
                body += f"   {'-' * 40}\n"

            body += f"\nGenerated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"

            msg.attach(MIMEText(body, 'plain'))

            # Send email
            server = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
            server.starttls()
            server.login(email_config['sender_email'], email_config['sender_password'])
            text = msg.as_string()
            server.sendmail(email_config['sender_email'], email_config['recipient_email'], text)
            server.quit()

            logging.info(f"Email notification sent for {len(rows)} rows to {email_config['recipient_email']}")

        except Exception as e:
            logging.error(f"Email sending failed: {e}")

    def console_notification(self, rows):
        """Simple console notification"""
        if rows:
            print(
                f"\n🔔 ALERT: Found {len(rows)} rows with status_id={self.monitor_config['status_id']} updated in last {self.monitor_config['time_window_minutes']} minutes:")
            for row in rows:
                print(f"  - ID: {row['id']}, Updated: {row['updated_at']}")
                print(f"    Data: {dict(row)}")
            print("-" * 50)

    def run_check(self, email_config=None):
        """Main monitoring function"""
        logging.info("Running database check...")

        rows = self.check_recent_updates()

        if rows:
            logging.info(f"Found {len(rows)} new rows matching criteria")

            # Console notification (if enabled)
            if self.monitor_config['enable_console']:
                self.console_notification(rows)

            # Email notification (if enabled and configured)
            if self.monitor_config['enable_email'] and email_config:
                self.send_email_notification(rows, email_config)
        else:
            logging.info("No new matching rows found")


# Usage example
def main():
    # Validate email configuration if email is enabled
    if MONITOR_CONFIG['enable_email']:
        required_email_fields = ['sender_email', 'sender_password', 'recipient_email']
        missing_fields = [field for field in required_email_fields if not EMAIL_CONFIG[field]]

        if missing_fields:
            logging.error(f"Email is enabled but missing required fields: {missing_fields}")
            logging.error("Please set the following environment variables:")
            for field in missing_fields:
                logging.error(f"  - {field.upper()}")
            return

    # Initialize the trigger monitor
    trigger = DatabaseTrigger(DB_CONFIG, MONITOR_CONFIG)

    # Option 1: Run once
    trigger.run_check(email_config=EMAIL_CONFIG if MONITOR_CONFIG['enable_email'] else None)

    # Option 2: Schedule to run at specified intervals
    schedule.every(MONITOR_CONFIG['check_interval_minutes']).minutes.do(
        trigger.run_check,
        email_config=EMAIL_CONFIG if MONITOR_CONFIG['enable_email'] else None
    )

    print(
        f"Starting PostgreSQL database monitor (checking every {MONITOR_CONFIG['check_interval_minutes']} minutes)...")
    print(f"Email notifications: {'Enabled' if MONITOR_CONFIG['enable_email'] else 'Disabled'}")
    print(f"Console notifications: {'Enabled' if MONITOR_CONFIG['enable_console'] else 'Disabled'}")
    print("Press Ctrl+C to stop")

    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nMonitor stopped")


if __name__ == "__main__":
    main()