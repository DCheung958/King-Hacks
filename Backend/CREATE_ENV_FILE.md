# How to Create the .env File

> **📖 First time setting up?** See **[GETTING_STARTED.md](../GETTING_STARTED.md)** for complete setup instructions.

## Step-by-Step Instructions

### Option 1: Using Notepad (Windows - Easiest)

1. **Open Notepad** (or any text editor)

2. **Type this line** (replace `mypassword123` with your actual PostgreSQL password):
   ```
   DATABASE_URL=postgresql+asyncpg://postgres:mypassword123@localhost:5432/echocare_db
   ```

3. **Save the file:**
   - Click "File" → "Save As"
   - Navigate to your `Backend` folder
   - In "File name" field, type: `.env` (with the dot at the beginning!)
   - In "Save as type" dropdown, select "All Files (*.*)"
   - Click "Save"

   ⚠️ **Important:** The file must be named exactly `.env` (with the dot, no extension)

### Option 2: Using Command Line (Windows PowerShell)

1. **Open PowerShell** in the Backend folder:
   ```powershell
   cd Backend
   ```

2. **Create the file:**
   ```powershell
   echo "DATABASE_URL=postgresql+asyncpg://postgres:mypassword123@localhost:5432/echocare_db" > .env
   ```

3. **Replace the password:**
   - Open the `.env` file in Notepad
   - Replace `mypassword123` with your actual password
   - Save

### Option 3: Using VS Code or Any Code Editor

1. **Open the `Backend` folder** in your editor

2. **Create a new file:**
   - Right-click in the file explorer
   - Select "New File"
   - Name it `.env`

3. **Add this line:**
   ```
   DATABASE_URL=postgresql+asyncpg://postgres:mypassword123@localhost:5432/echocare_db
   ```

4. **Replace `mypassword123`** with your actual PostgreSQL password

5. **Save the file**

## Verify the File Was Created

1. **Go to the `Backend` folder**
2. **Make sure you can see hidden files:**
   - In File Explorer, click "View" tab
   - Check "Hidden items" checkbox
3. **You should see a file named `.env`** (it might appear without an icon)

## File Location

The `.env` file should be in:
```
Echocare/
  Backend/
    .env          ← HERE
    main.py
    database.py
    requirements.txt
```

## What to Put in the File

Replace `mypassword123` with your actual PostgreSQL password:

```env
DATABASE_URL=postgresql+asyncpg://postgres:YOUR_ACTUAL_PASSWORD@localhost:5432/echocare_db
```

**Example:**
If your password is `MySecurePass123`, the file should contain:
```env
DATABASE_URL=postgresql+asyncpg://postgres:MySecurePass123@localhost:5432/echocare_db
```

## After Creating the File

1. **Restart the backend** (if it's running)
2. **The backend will automatically load the `.env` file**
3. **Check the terminal** - you should no longer see "password authentication failed"

## Troubleshooting

### "I can't see the .env file"
- Make sure "Hidden items" is checked in File Explorer
- The file name starts with a dot (`.`), which makes it hidden on Windows

### "File saves as .env.txt"
- In Notepad "Save As" dialog:
  - Change "Save as type" to "All Files (*.*)"
  - Type `.env` in the filename (including the dot)
  - Or rename the file after saving: remove `.txt` extension

### "Still getting password errors"
- Make sure the password in `.env` matches your PostgreSQL password exactly
- No extra spaces before or after the password
- Restart the backend after creating/updating the file

