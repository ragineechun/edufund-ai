from models.database import Database
import bcrypt

def init_admin():
    db = Database()
    
    # Check if admin exists
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = 'admin@edufund.ai'")
    admin = cursor.fetchone()
    
    if not admin:
        # Create admin user
        password_hash = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        cursor.execute('''
            INSERT INTO users (email, password_hash, name, role)
            VALUES (?, ?, ?, ?)
        ''', ('admin@edufund.ai', password_hash, 'Admin User', 'admin'))
        
        conn.commit()
        print("✅ Admin user created successfully!")
        print("   Email: admin@edufund.ai")
        print("   Password: admin123")
    else:
        print("✅ Admin user already exists")
    
    conn.close()

if __name__ == '__main__':
    init_admin()