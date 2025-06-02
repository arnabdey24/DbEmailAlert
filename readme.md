# PostgreSQL Database Trigger Monitor

A Python application that monitors PostgreSQL database tables for recent updates and sends email notifications when specific conditions are met.

## Features

- **PostgreSQL Schema Support**: Full schema support including custom schemas
- **Configurable Monitoring**: Monitor any table for specific status changes
- **Email Notifications**: Rich email alerts with detailed row information
- **Time-based Filtering**: Configurable time windows for update detection
- **Duplicate Prevention**: Tracks processed rows to avoid duplicate notifications
- **Environment-based Configuration**: Easy setup with environment variables

## Requirements

- Python 3.7+
- PostgreSQL database
- SMTP email server access (Gmail, Office 365, etc.)

## Installation & Setup

### 1. Clone or Download the Project

```bash
git clone <your-repo-url>
cd database-trigger-monitor
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate

# On macOS/Linux:
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your settings
nano .env  # or use your preferred editor
```

### 5. Configure Your Settings

Edit the `.env` file with your database and email settings:

```bash
# PostgreSQL Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_database_name
DB_USER=your_username
DB_PASSWORD=your_password
DB_SCHEMA=public
DB_TABLE=your_table_name

# Monitor Settings
CHECK_INTERVAL=5        # Minutes between checks
TIME_WINDOW=30          # Minutes to look back for updates
TARGET_STATUS_ID=3      # Status ID to monitor

# Email Configuration
ENABLE_EMAIL=true
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=your_app_password
RECIPIENT_EMAIL=alerts@yourcompany.com
```

## Email Setup

### Gmail Configuration

1. **Enable 2-Factor Authentication** on your Gmail account
2. **Generate an App Password**:
   - Go to [Google Account Settings](https://myaccount.google.com/apppasswords)
   - Select "Mail" and generate a password
   - Use this password as `SENDER_PASSWORD` (not your regular Gmail password)

3. **Configure in .env**:
   ```bash
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   SENDER_EMAIL=your_email@gmail.com
   SENDER_PASSWORD=generated_app_password
   ```

### Other Email Providers

**Office 365:**
```bash
SMTP_SERVER=smtp.office365.com
SMTP_PORT=587
```

**Yahoo:**
```bash
SMTP_SERVER=smtp.mail.yahoo.com
SMTP_PORT=587
```

## Database Requirements

Your PostgreSQL table should have:
- An `id` column (primary key)
- A `status_id` column (integer)
- An `updated_at` column (timestamp)

Example table structure:
```sql
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    status_id INTEGER NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    customer_name VARCHAR(255),
    order_total DECIMAL(10,2)
    -- other columns...
);
```

## Usage

### Running the Monitor

1. **Activate your virtual environment** (if not already active):
   ```bash
   # Windows:
   .venv\Scripts\activate
   
   # macOS/Linux:
   source .venv/bin/activate
   ```

2. **Run the monitor**:
   ```bash
   python db_trigger.py
   ```

3. **The monitor will**:
   - Check the database every 5 minutes (configurable)
   - Look for rows with `status_id = 3` (configurable)
   - Send email alerts for new matching rows
   - Display console notifications
   - Run continuously until stopped with `Ctrl+C`

### One-time Check

To run a single check instead of continuous monitoring:

```python
# Edit db_trigger.py and comment out the scheduling loop
# Or create a simple script:
from db_trigger import DatabaseTrigger, DB_CONFIG, MONITOR_CONFIG, EMAIL_CONFIG

trigger = DatabaseTrigger(DB_CONFIG, MONITOR_CONFIG)
trigger.run_check(email_config=EMAIL_CONFIG)
```

## Configuration Options

### Database Settings
- `DB_HOST`: PostgreSQL server hostname
- `DB_PORT`: PostgreSQL port (default: 5432)
- `DB_NAME`: Database name
- `DB_USER`: Database username
- `DB_PASSWORD`: Database password
- `DB_SCHEMA`: Schema name (default: public)
- `DB_TABLE`: Table name to monitor

### Monitor Settings
- `CHECK_INTERVAL`: Minutes between database checks
- `TIME_WINDOW`: Minutes to look back for updates
- `TARGET_STATUS_ID`: Status ID to monitor for changes
- `ENABLE_EMAIL`: Enable/disable email notifications
- `ENABLE_CONSOLE`: Enable/disable console output

### Email Settings
- `SMTP_SERVER`: SMTP server hostname
- `SMTP_PORT`: SMTP server port
- `SENDER_EMAIL`: Email address to send from
- `SENDER_PASSWORD`: Email password (use app password for Gmail)
- `RECIPIENT_EMAIL`: Email address to send alerts to
- `EMAIL_SUBJECT_PREFIX`: Custom subject line prefix

## Example Use Cases

### E-commerce Order Monitoring
Monitor orders that change to "shipped" status:
```bash
DB_TABLE=orders
TARGET_STATUS_ID=3  # 3 = shipped
TIME_WINDOW=30      # Check last 30 minutes
```

### Support Ticket Alerts
Monitor support tickets that become urgent:
```bash
DB_TABLE=support_tickets
TARGET_STATUS_ID=5  # 5 = urgent
TIME_WINDOW=15      # Check last 15 minutes
```

### Multi-tenant Application
Monitor tenant-specific data:
```bash
DB_SCHEMA=tenant_001
DB_TABLE=user_activities
TARGET_STATUS_ID=2  # 2 = suspicious activity
```

## Troubleshooting

### Common Issues

1. **Connection Error**:
   - Verify database credentials in `.env`
   - Check if PostgreSQL server is running
   - Verify network connectivity

2. **Email Not Sending**:
   - Check SMTP settings
   - Verify email credentials
   - For Gmail, ensure you're using an App Password

3. **No Rows Found**:
   - Verify table and column names
   - Check if there are recent updates matching your criteria
   - Review the time window setting

### Logging

Enable debug logging by setting:
```bash
LOG_LEVEL=DEBUG
```

### Testing Connection

Test your database connection:
```python
from db_trigger import DatabaseTrigger, DB_CONFIG, MONITOR_CONFIG

trigger = DatabaseTrigger(DB_CONFIG, MONITOR_CONFIG)
conn = trigger.connect_db()
if conn:
    print("Database connection successful!")
    conn.close()
else:
    print("Database connection failed!")
```

### Project Structure

```
database-trigger-monitor/
├── db_trigger.py          # Main application
├── config.py              # Configuration management
├── requirements.txt       # Python dependencies
├── .env.example          # Environment template
├── .env                  # Your environment variables (not in git)
├── .venv/               # Virtual environment
└── README.md            # This file
```

## Contributing

1. Create a feature branch
2. Make your changes
3. Test thoroughly
4. Submit a pull request


## Support

For issues and questions:
- Check the troubleshooting section
- Review your configuration settings
- Check application logs for error details