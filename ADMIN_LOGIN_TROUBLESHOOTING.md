# ConsultEase Admin Login Troubleshooting Guide

## 🚨 Problem: "Invalid Username and Password" Error

If you're getting an "Invalid Username and Password" error when trying to log in with `admin` / `TempPass123!`, this guide will help you resolve the issue.

## 🔍 Quick Diagnosis

### Step 1: Check Admin Account Status

Run the admin status checker to see what's in the database:

**On Windows:**
```cmd
scripts\check_admin_status.bat
```

**On Linux/macOS:**
```bash
python3 scripts/check_admin_status.py
```

This will show you:
- Whether admin accounts exist in the database
- If the default password works
- What credentials are currently valid

### Step 2: Fix Admin Account

If the status checker shows issues, run the fix script:

**On Windows:**
```cmd
scripts\fix_admin_login.bat
```

**On Linux/macOS:**
```bash
python3 scripts/fix_admin_login.py
```

This script will:
- Initialize the database properly
- Create or reset the admin account
- Set the correct password
- Test the login credentials

## 🔧 Manual Troubleshooting Steps

### 1. Database Connection Issues

If the scripts fail with database errors:

```bash
# Check if the database file exists
ls -la consultease.db

# If using PostgreSQL, check if the service is running
sudo systemctl status postgresql

# If using SQLite, check file permissions
chmod 664 consultease.db
```

### 2. Reinitialize Database

If the database is corrupted or missing:

```python
# Run this Python code to reinitialize
python3 -c "
from central_system.models.base import init_db
init_db()
print('Database reinitialized')
"
```

### 3. Manual Admin Creation

If automated scripts fail, create admin manually:

```python
python3 -c "
import sys
sys.path.insert(0, '.')
from central_system.models.base import get_db
from central_system.models.admin import Admin

# Create admin manually
db = get_db()
password_hash, salt = Admin.hash_password('TempPass123!')
admin = Admin(
    username='admin',
    password_hash=password_hash,
    salt=salt,
    email='admin@consultease.com',
    is_active=True,
    force_password_change=True
)
db.add(admin)
db.commit()
db.close()
print('Admin created manually')
"
```

### 4. Reset Admin Password

If you need to reset the admin password:

```bash
python3 scripts/fix_admin_login.py --reset-password
```

## 🎯 Common Causes and Solutions

### Cause 1: Database Not Initialized
**Symptoms:** No admin accounts found
**Solution:** Run `python3 scripts/fix_admin_login.py`

### Cause 2: Wrong Password Hash
**Symptoms:** Admin exists but password doesn't work
**Solution:** Reset password with fix script

### Cause 3: Admin Account Inactive
**Symptoms:** Admin exists but login fails
**Solution:** Activate account with fix script

### Cause 4: Database Permissions
**Symptoms:** Database connection errors
**Solution:** Check file permissions and database service status

### Cause 5: Multiple Admin Accounts
**Symptoms:** Conflicting admin accounts
**Solution:** Use fix script to clean up and reset

## 📋 Expected Working Credentials

After running the fix script, these credentials should work:

```
Username: admin
Password: TempPass123!
```

**Important Notes:**
- This is a **temporary password**
- You **must change it** on first login
- The system will **force a password change**
- New password must meet security requirements

## 🔒 Password Requirements

When changing the password, it must have:
- **Minimum 8 characters**
- **At least 1 uppercase letter** (A-Z)
- **At least 1 lowercase letter** (a-z)
- **At least 1 digit** (0-9)
- **At least 1 special character** (!@#$%^&*)

**Good password examples:**
- `MySecure@Pass2024`
- `Strong#Password1`
- `Complex$Admin456`

## 🚀 Step-by-Step Login Process

1. **Start ConsultEase** application
2. **Click Login** button on main screen
3. **Enter credentials:**
   - Username: `admin`
   - Password: `TempPass123!`
4. **Click Login** button
5. **Change password** when prompted
6. **Enter new secure password** meeting requirements
7. **Confirm new password**
8. **Access admin dashboard**

## 🛠️ Advanced Troubleshooting

### Check Database Contents Directly

**For SQLite:**
```bash
sqlite3 consultease.db
.tables
SELECT * FROM admins;
.quit
```

**For PostgreSQL:**
```bash
sudo -u postgres psql consultease
\dt
SELECT * FROM admins;
\q
```

### Enable Debug Logging

Add this to your Python script to see detailed logs:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check System Logs

```bash
# Check application logs
tail -f consultease.log

# Check system logs (Linux)
journalctl -u consultease.service -f
```

## 🆘 Emergency Access

If all else fails, you can create a temporary admin account:

```python
# Emergency admin creation
python3 -c "
import sys, os
sys.path.insert(0, '.')
os.environ['DB_TYPE'] = 'sqlite'
os.environ['DB_PATH'] = 'consultease.db'

from central_system.models.base import get_db, init_db
from central_system.models.admin import Admin

init_db()
db = get_db()

# Remove existing admin
db.query(Admin).filter(Admin.username == 'admin').delete()

# Create new admin
password_hash, salt = Admin.hash_password('Emergency123!')
admin = Admin(
    username='admin',
    password_hash=password_hash,
    salt=salt,
    email='admin@consultease.com',
    is_active=True,
    force_password_change=True
)
db.add(admin)
db.commit()
db.close()
print('Emergency admin created: admin / Emergency123!')
"
```

## 📞 Getting Help

If you're still having issues:

1. **Run the diagnostic scripts** and save the output
2. **Check the application logs** for error messages
3. **Verify database connectivity** and permissions
4. **Try the emergency access** method above
5. **Document the exact error messages** you're seeing

## ✅ Success Indicators

You'll know the login is working when:
- ✅ No "Invalid Username and Password" error
- ✅ System prompts for password change
- ✅ Admin dashboard loads successfully
- ✅ All admin functions are accessible

## 🎉 Final Notes

The ConsultEase system is designed with security in mind, which is why the default password must be changed immediately. Once you successfully log in and change the password, the system will work reliably with your new credentials.

Remember to:
- **Use a strong, unique password**
- **Don't share admin credentials**
- **Log out properly when finished**
- **Monitor the audit logs** for security
