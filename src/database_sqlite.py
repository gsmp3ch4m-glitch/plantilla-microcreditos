import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'system.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def log_action(user_id, action, details):
    """Logs a user action to the audit_logs table."""
    conn = get_db_connection()
    try:
        conn.execute("INSERT INTO audit_logs (user_id, action, details) VALUES (?, ?, ?)", (user_id, action, details))
        conn.commit()
    except Exception as e:
        print(f"Error logging action: {e}")
    finally:
        conn.close()

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            full_name TEXT,
            analyst_name TEXT,
            analyst_phone TEXT,
            permissions TEXT -- Comma separated list of allowed modules, or 'all'
        )
    ''')
    
    # Check if permissions column exists (for migration)
    try:
        cursor.execute("SELECT permissions FROM users LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE users ADD COLUMN permissions TEXT")
        cursor.execute("UPDATE users SET permissions = 'all' WHERE role = 'admin'")
    
    # Check if analyst fields exist (for migration)
    try:
        cursor.execute("SELECT analyst_name FROM users LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE users ADD COLUMN analyst_name TEXT")
        cursor.execute("ALTER TABLE users ADD COLUMN analyst_phone TEXT")
    
    # Clients table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dni TEXT UNIQUE NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            phone TEXT,
            address TEXT,
            email TEXT,
            work_address TEXT,
            occupation TEXT,
            photo_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Migration for new clients columns
    try:
        cursor.execute("SELECT email FROM clients LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE clients ADD COLUMN email TEXT")
    
    try:
        cursor.execute("SELECT work_address FROM clients LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE clients ADD COLUMN work_address TEXT")
        cursor.execute("ALTER TABLE clients ADD COLUMN occupation TEXT")
        cursor.execute("ALTER TABLE clients ADD COLUMN photo_path TEXT")

    # Loans table (Generic for all types)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS loans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            loan_type TEXT NOT NULL, -- 'empeno', 'bancario', 'rapidiario'
            amount REAL NOT NULL,
            interest_rate REAL,
            start_date DATE,
            due_date DATE,
            status TEXT DEFAULT 'active', -- 'active', 'paid', 'overdue'
            FOREIGN KEY (client_id) REFERENCES clients (id)
        )
    ''')

    # Migration for loans table (if missing columns)
    try:
        cursor.execute("SELECT interest_rate FROM loans LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE loans ADD COLUMN interest_rate REAL")
        cursor.execute("ALTER TABLE loans ADD COLUMN start_date DATE")
        cursor.execute("ALTER TABLE loans ADD COLUMN due_date DATE")
        cursor.execute("ALTER TABLE loans ADD COLUMN status TEXT DEFAULT 'active'")

    # Migration for Frozen Loans and Refinancing
    try:
        cursor.execute("SELECT refinance_count FROM loans LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE loans ADD COLUMN refinance_count INTEGER DEFAULT 0")
        cursor.execute("ALTER TABLE loans ADD COLUMN parent_loan_id INTEGER")
        cursor.execute("ALTER TABLE loans ADD COLUMN frozen_amount REAL DEFAULT 0")
        cursor.execute("ALTER TABLE loans ADD COLUMN admin_fee REAL DEFAULT 0")
        cursor.execute("ALTER TABLE loans ADD COLUMN sales_expense REAL DEFAULT 0")
        cursor.execute("ALTER TABLE loans ADD COLUMN sale_price REAL DEFAULT 0")
        cursor.execute("ALTER TABLE loans ADD COLUMN frozen_date DATE")

    # Pawn Details table (Collateral)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pawn_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            loan_id INTEGER,
            item_type TEXT, -- Joya, Electro, Vehiculo, etc.
            brand TEXT,
            characteristics TEXT,
            condition TEXT, -- Nuevo, Usado, Dañado
            market_value REAL,
            FOREIGN KEY (loan_id) REFERENCES loans (id) ON DELETE CASCADE
        )
    ''')

    # Migration for pawn_details
    try:
        cursor.execute("SELECT item_type FROM pawn_details LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE pawn_details ADD COLUMN item_type TEXT")
        cursor.execute("ALTER TABLE pawn_details ADD COLUMN brand TEXT")
        cursor.execute("ALTER TABLE pawn_details ADD COLUMN characteristics TEXT")
        cursor.execute("ALTER TABLE pawn_details ADD COLUMN condition TEXT")
        cursor.execute("ALTER TABLE pawn_details ADD COLUMN market_value REAL")

    # Transactions table (Caja)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL, -- 'income', 'expense'
            category TEXT, -- 'payment', 'loan_disbursement', 'operational'
            amount REAL NOT NULL,
            description TEXT,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_id INTEGER,
            loan_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (loan_id) REFERENCES loans (id)
        )
    ''')

    # Cash Sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cash_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            opening_balance REAL NOT NULL,
            opening_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            closing_balance REAL,
            closing_date TIMESTAMP,
            status TEXT DEFAULT 'open', -- 'open', 'closed'
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # Installments table (Cronograma de Pagos)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS installments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            loan_id INTEGER,
            number INTEGER,
            due_date DATE,
            amount REAL,
            status TEXT DEFAULT 'pending', -- 'pending', 'paid', 'partial', 'overdue'
            paid_amount REAL DEFAULT 0,
            payment_date DATE,
            payment_method TEXT DEFAULT 'efectivo', -- 'efectivo', 'yape', 'deposito'
            FOREIGN KEY (loan_id) REFERENCES loans (id) ON DELETE CASCADE
        )
    ''')
    
    # Migrations for existing tables
    try:
        cursor.execute("SELECT payment_method FROM installments LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE installments ADD COLUMN payment_method TEXT DEFAULT 'efectivo'")
    
    try:
        cursor.execute("SELECT analyst_id FROM clients LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE clients ADD COLUMN analyst_id INTEGER")
    
    try:
        cursor.execute("SELECT analyst_id FROM loans LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE loans ADD COLUMN analyst_id INTEGER")

    # Migration for transactions table
    try:
        cursor.execute("SELECT payment_method FROM transactions LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE transactions ADD COLUMN payment_method TEXT DEFAULT 'efectivo'")
    
    try:
        cursor.execute("SELECT cash_session_id FROM transactions LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE transactions ADD COLUMN cash_session_id INTEGER")

    # Settings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT,
            description TEXT
        )
    ''')
    
    # Default Settings
    default_settings = [
        ('company_name', 'Mi Empresa S.A.C.', 'Nombre de la Empresa'),
        ('company_registry', '', 'Partida Registral'),
        ('company_ruc', '20123456789', 'RUC'),
        ('company_manager', '', 'Gerente General'),
        ('manager_dni', '', 'DNI del Gerente'),
        ('company_address', 'Av. Principal 123', 'Dirección de la Empresa'),
        ('company_phone', '999 999 999', 'Teléfono de la Empresa'),
        ('company_phone2', '', 'Teléfono de la Empresa 2'),
        ('manager_phone', '', 'Teléfono del Gerente'),
        ('manager_address', '', 'Dirección del Gerente'),
        ('analyst_name', 'Analista', 'Nombre del Analista'),
        ('analyst_phone', '999 999 999', 'Teléfono del Analista'),
        # Interests moved to another module or kept in DB but not shown in Company tab
        ('interest_pawn', '5.0', 'Tasa de Interés - Empeño (%)'),
        ('interest_bank', '10.0', 'Tasa de Interés - Bancario (%)'),
        ('interest_rapid', '20.0', 'Tasa de Interés - Rapidiario (%)'),
        ('company_initial_cash', '0.00', 'Dinero Inicial de la Empresa'),
    ]
    
    for key, val, desc in default_settings:
        cursor.execute('INSERT OR IGNORE INTO settings (key, value, description) VALUES (?, ?, ?)', (key, val, desc))

    # Module Settings (Visibility and Labels)
    # Mandatory: Clients, Cash, Config, Loan 1
    # Optional: Loan 2-5, Calc, Analysis, Docs, Other 1-2
    module_settings = [
        # Visibility (1=Visible, 0=Hidden)
        ('mod_clients_visible', '1', 'Visible Clientes'),
        ('mod_cash_visible', '1', 'Visible Caja'),
        ('mod_config_visible', '1', 'Visible Configuración'),
        ('mod_loan1_visible', '1', 'Visible Préstamo 1'), # Mandatory
        
        ('mod_loan2_visible', '1', 'Visible Préstamo 2'),
        ('mod_loan3_visible', '1', 'Visible Préstamo 3'),
        ('mod_loan4_visible', '0', 'Visible Préstamo 4'),
        ('mod_loan5_visible', '0', 'Visible Préstamo 5'),
        
        ('mod_calc_visible', '1', 'Visible Calculadora'),
        ('mod_analysis_visible', '1', 'Visible Análisis'),
        ('mod_docs_visible', '0', 'Visible Documentos'),
        ('mod_db_visible', '1', 'Visible Base de Datos'), # Added default visible
        ('mod_notif_visible', '1', 'Visible Notificaciones'), # Added default visible
        ('mod_other1_visible', '0', 'Visible Otros 1'),
        ('mod_other2_visible', '0', 'Visible Otros 2'),

        # Labels (Customizable Names)
        ('label_clients', 'Clientes', 'Etiqueta Clientes'),
        ('label_cash', 'Caja', 'Etiqueta Caja'),
        ('label_config', 'Configuración', 'Etiqueta Configuración'),
        
        ('label_loan1', 'Casa de Empeño', 'Etiqueta Préstamo 1'),
        ('label_loan2', 'Préstamo Bancario', 'Etiqueta Préstamo 2'),
        ('label_loan3', 'Rapidiario', 'Etiqueta Préstamo 3'),
        ('label_loan4', 'Préstamo 4', 'Etiqueta Préstamo 4'),
        ('label_loan5', 'Préstamo 5', 'Etiqueta Préstamo 5'),
        
        ('label_calc', 'Calculadora', 'Etiqueta Calculadora'),
        ('label_analysis', 'Análisis', 'Etiqueta Análisis'),
        ('label_notif', 'Notificaciones', 'Etiqueta Notificaciones'),
        ('label_docs', 'Documentos', 'Etiqueta Documentos'),
        ('label_db', 'Base de Datos', 'Etiqueta Base de Datos'), # Reverted label
        ('label_other1', 'Otros 1', 'Etiqueta Otros 1'),
        ('label_other2', 'Otros 2', 'Etiqueta Otros 2'),
        
        ('app_theme', 'light', 'Tema de la Aplicación'),
    ]
    for key, val, desc in module_settings:
        cursor.execute('INSERT OR IGNORE INTO settings (key, value, description) VALUES (?, ?, ?)', (key, val, desc))

    # Migration: Ensure label_db is "Base de Datos" for the Main Menu
    cursor.execute("UPDATE settings SET value = 'Base de Datos' WHERE key = 'label_db' AND value = 'Respaldo/Reset'")

    # Notifications table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            notify_date TIMESTAMP NOT NULL,
            created_by INTEGER,
            is_done INTEGER DEFAULT 0, -- 0=False, 1=True
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES users (id)
        )
    ''')

    # Audit Logs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT,
            details TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Default admin user if not exists
    cursor.execute('SELECT * FROM users WHERE username = ?', ('admin',))
    if not cursor.fetchone():
        cursor.execute('INSERT INTO users (username, password, role, full_name, permissions) VALUES (?, ?, ?, ?, ?)',
                       ('admin', 'admin123', 'admin', 'Administrador Principal', 'all'))

    # Migration: Update existing loans with analyst_id from clients
    # This fixes old loans that were created before the analyst_id column existed
    cursor.execute("""
        UPDATE loans 
        SET analyst_id = (SELECT analyst_id FROM clients WHERE clients.id = loans.client_id)
        WHERE analyst_id IS NULL
    """)
    
    # Force fix: If any client still has NULL analyst_id, assign to admin (id 1)
    cursor.execute("UPDATE clients SET analyst_id = 1 WHERE analyst_id IS NULL")
    
    # Force fix: If any loan still has NULL analyst_id, assign to admin (id 1)
    cursor.execute("UPDATE loans SET analyst_id = 1 WHERE analyst_id IS NULL")

    conn.commit()
    conn.close()
    print("Base de datos inicializada correctamente.")

if __name__ == '__main__':
    init_db()
