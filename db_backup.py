
import sqlite3
import io

backup_filename = 'backupdatabase_dump.sql'
with sqlite3.connect('DB.sqlite3') as conn:
    with io.open(backup_filename, 'w') as p: 
        # iterdump() function
        for line in conn.iterdump(): 
            p.write('%s\n' % line)
    print(f'Backup performed successfully!\nData Saved as {backup_filename}')
  