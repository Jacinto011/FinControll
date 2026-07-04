import json
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import uuid
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

# Carregar variáveis de ambiente
load_dotenv()

# ============ CONFIGURAÇÃO ============
DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    raise ValueError('⚠️ DATABASE_URL não encontrada! Define a variável de ambiente.')

# ============ CAMINHOS ============
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
USERS_FILE = os.path.join(DATA_DIR, 'users.json')
TRANSACTIONS_DIR = os.path.join(DATA_DIR, 'transactions')

print(f'📁 Diretório base: {BASE_DIR}')
print(f'📁 Data dir: {DATA_DIR}')
print(f'📁 Users file: {USERS_FILE}')
print(f'📁 Transactions dir: {TRANSACTIONS_DIR}')

# ============ SENHA PADRÃO ============
DEFAULT_PASSWORD = 'Jacinto2002'

# ============ FUNÇÕES ============

def get_connection():
    """Estabelecer conexão com o Neon"""
    return psycopg2.connect(DATABASE_URL)

def create_tables():
    """Criar tabelas no Neon"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Criar extensão UUID
    cursor.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
    
    # ===== TABELA: users =====
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            nome TEXT,
            apelido TEXT,
            pais TEXT DEFAULT 'Moçambique',
            moeda TEXT DEFAULT 'MZN',
            created_at TIMESTAMP DEFAULT NOW()
        );
    ''')
    
    # ===== TABELA: wallets =====
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS wallets (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            username TEXT NOT NULL REFERENCES users(username) ON DELETE CASCADE,
            name TEXT NOT NULL,
            type TEXT NOT NULL CHECK (type IN ('physical_cash', 'mobile_money', 'bank_account')),
            balance REAL DEFAULT 0,
            icon TEXT DEFAULT '💳',
            created_at TIMESTAMP DEFAULT NOW()
        );
    ''')
    
    # ===== TABELA: categories =====
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            username TEXT NOT NULL REFERENCES users(username) ON DELETE CASCADE,
            name TEXT NOT NULL,
            icon TEXT DEFAULT '📌',
            type TEXT NOT NULL CHECK (type IN ('income', 'expense')),
            created_at TIMESTAMP DEFAULT NOW()
        );
    ''')
    
    # ===== TABELA: transactions =====
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            username TEXT NOT NULL REFERENCES users(username) ON DELETE CASCADE,
            type TEXT NOT NULL CHECK (type IN ('income', 'expense', 'investment')),
            description TEXT NOT NULL,
            amount REAL NOT NULL,
            category_id UUID NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
            wallet_id UUID NOT NULL REFERENCES wallets(id) ON DELETE CASCADE,
            date DATE NOT NULL,
            notes TEXT,
            is_transfer BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT NOW()
        );
    ''')
    
    # ===== ÍNDICES =====
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_username ON transactions(username);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_wallets_username ON wallets(username);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_categories_username ON categories(username);')
    
    conn.commit()
    conn.close()
    print('✅ Tabelas criadas com sucesso!')

def is_valid_uuid(val):
    """Verificar se um valor é um UUID válido"""
    try:
        uuid.UUID(str(val))
        return True
    except ValueError:
        return False

def generate_uuid():
    """Gerar um novo UUID"""
    return str(uuid.uuid4())

def migrate_users():
    """Migrar utilizadores com senha encriptada"""
    if not os.path.exists(USERS_FILE):
        print(f'⚠️ Ficheiro users.json não encontrado em: {USERS_FILE}')
        return
    
    with open(USERS_FILE, 'r', encoding='utf-8') as f:
        users = json.load(f)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    for username, data in users.items():
        # Verificar se o utilizador já existe
        cursor.execute('SELECT username FROM users WHERE username = %s', (username,))
        if cursor.fetchone():
            print(f'⏭️ Utilizador {username} já existe, a saltar...')
            continue
        
        # Encriptar a senha padrão
        password_hash = generate_password_hash(DEFAULT_PASSWORD)
        
        cursor.execute('''
            INSERT INTO users (username, password, nome, apelido, pais, moeda, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (
            username,
            password_hash,
            data.get('nome', ''),
            data.get('apelido', ''),
            data.get('pais', 'Moçambique'),
            data.get('moeda', 'MZN'),
            data.get('created_at', datetime.now().isoformat())
        ))
        print(f'✅ Utilizador {username} migrado com senha: {DEFAULT_PASSWORD}')
    
    conn.commit()
    conn.close()

def migrate_user_data(username):
    """Migrar dados de um utilizador"""
    user_file = os.path.join(TRANSACTIONS_DIR, f'{username}.json')
    if not os.path.exists(user_file):
        print(f'⚠️ Ficheiro para {username} não encontrado em: {user_file}')
        return
    
    with open(user_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # ===== DICIONÁRIO PARA MAPEAR IDs ANTIGOS -> NOVOS =====
    wallet_id_map = {}
    category_id_map = {}
    
    try:
        # ===== MIGRAR CARTEIRAS =====
        for wallet in data.get('wallets', []):
            old_id = wallet.get('id')
            if not old_id or not is_valid_uuid(old_id):
                new_id = generate_uuid()
                print(f'  🔄 ID inválido "{old_id}" -> novo UUID: {new_id}')
            else:
                new_id = old_id
            
            wallet_id_map[old_id] = new_id
            
            cursor.execute('SELECT id FROM wallets WHERE id = %s', (new_id,))
            if not cursor.fetchone():
                cursor.execute('''
                    INSERT INTO wallets (id, username, name, type, balance, icon, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                ''', (
                    new_id,
                    username,
                    wallet.get('name', ''),
                    wallet.get('type', 'physical_cash'),
                    wallet.get('balance', 0),
                    wallet.get('icon', '💳'),
                    datetime.now().isoformat()
                ))
                print(f'  ✅ Carteira {wallet.get("name")} migrada (ID: {new_id})')
            else:
                print(f'  ⏭️ Carteira {wallet.get("name")} já existe')
        
        # ===== MIGRAR CATEGORIAS =====
        for category_type in ['income', 'expense']:
            for cat in data.get('categories', {}).get(category_type, []):
                old_id = cat.get('id')
                if not old_id or not is_valid_uuid(old_id):
                    new_id = generate_uuid()
                    print(f'  🔄 ID inválido "{old_id}" -> novo UUID: {new_id}')
                else:
                    new_id = old_id
                
                category_id_map[old_id] = new_id
                
                cursor.execute('SELECT id FROM categories WHERE id = %s', (new_id,))
                if not cursor.fetchone():
                    cursor.execute('''
                        INSERT INTO categories (id, username, name, icon, type, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    ''', (
                        new_id,
                        username,
                        cat.get('name', ''),
                        cat.get('icon', '📌'),
                        category_type,
                        datetime.now().isoformat()
                    ))
                    print(f'  ✅ Categoria {cat.get("name")} migrada (ID: {new_id})')
                else:
                    print(f'  ⏭️ Categoria {cat.get("name")} já existe')
        
        # ===== MIGRAR TRANSAÇÕES =====
        for transaction in data.get('transactions', []):
            trans_id = transaction.get('id')
            if not trans_id or not is_valid_uuid(trans_id):
                trans_id = generate_uuid()
                print(f'  🔄 ID de transação inválido -> novo UUID: {trans_id}')
            
            # ===== PROCESSAR CATEGORY_ID =====
            old_cat_id = transaction.get('category_id')
            
            # Se for "inv_other", criar uma categoria especial
            if old_cat_id == 'inv_other':
                # Verificar se já existe uma categoria "Investimento" do tipo expense
                cursor.execute('''
                    SELECT id FROM categories 
                    WHERE username = %s AND name = 'Investimento' AND type = 'expense'
                ''', (username,))
                result = cursor.fetchone()
                if result:
                    new_cat_id = result[0]
                else:
                    # Criar categoria "Investimento"
                    new_cat_id = generate_uuid()
                    cursor.execute('''
                        INSERT INTO categories (id, username, name, icon, type, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    ''', (new_cat_id, username, 'Investimento', '📈', 'expense', datetime.now().isoformat()))
                    print(f'  ✅ Criada categoria "Investimento" para transações de investimento')
                    category_id_map[old_cat_id] = new_cat_id
            elif old_cat_id in category_id_map:
                new_cat_id = category_id_map[old_cat_id]
            else:
                # Se a categoria não existir no mapa, verificar se existe na BD
                if old_cat_id and is_valid_uuid(old_cat_id):
                    cursor.execute('SELECT id FROM categories WHERE id = %s AND username = %s', (old_cat_id, username))
                    result = cursor.fetchone()
                    if result:
                        new_cat_id = old_cat_id
                    else:
                        # Criar categoria "Outros" como fallback
                        cursor.execute('''
                            SELECT id FROM categories 
                            WHERE username = %s AND name = 'Outros' AND type = 'expense'
                        ''', (username,))
                        result = cursor.fetchone()
                        if result:
                            new_cat_id = result[0]
                        else:
                            new_cat_id = generate_uuid()
                            cursor.execute('''
                                INSERT INTO categories (id, username, name, icon, type, created_at)
                                VALUES (%s, %s, %s, %s, %s, %s)
                            ''', (new_cat_id, username, 'Outros', '📌', 'expense', datetime.now().isoformat()))
                            print(f'  ✅ Criada categoria "Outros" como fallback')
                        category_id_map[old_cat_id] = new_cat_id
                else:
                    # ID inválido, criar fallback
                    cursor.execute('''
                        SELECT id FROM categories 
                        WHERE username = %s AND name = 'Outros' AND type = 'expense'
                    ''', (username,))
                    result = cursor.fetchone()
                    if result:
                        new_cat_id = result[0]
                    else:
                        new_cat_id = generate_uuid()
                        cursor.execute('''
                            INSERT INTO categories (id, username, name, icon, type, created_at)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        ''', (new_cat_id, username, 'Outros', '📌', 'expense', datetime.now().isoformat()))
                        print(f'  ✅ Criada categoria "Outros" como fallback')
                    if old_cat_id:
                        category_id_map[old_cat_id] = new_cat_id
            
            # ===== PROCESSAR WALLET_ID =====
            old_wallet_id = transaction.get('wallet_id')
            if old_wallet_id in wallet_id_map:
                new_wallet_id = wallet_id_map[old_wallet_id]
            elif old_wallet_id and is_valid_uuid(old_wallet_id):
                cursor.execute('SELECT id FROM wallets WHERE id = %s AND username = %s', (old_wallet_id, username))
                result = cursor.fetchone()
                if result:
                    new_wallet_id = old_wallet_id
                else:
                    # Criar carteira fallback
                    new_wallet_id = generate_uuid()
                    cursor.execute('''
                        INSERT INTO wallets (id, username, name, type, balance, icon, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ''', (new_wallet_id, username, 'Carteira Padrão', 'physical_cash', 0, '💳', datetime.now().isoformat()))
                    print(f'  ✅ Criada carteira "Carteira Padrão" como fallback')
                    wallet_id_map[old_wallet_id] = new_wallet_id
            else:
                # Criar carteira fallback
                new_wallet_id = generate_uuid()
                cursor.execute('''
                    INSERT INTO wallets (id, username, name, type, balance, icon, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                ''', (new_wallet_id, username, 'Carteira Padrão', 'physical_cash', 0, '💳', datetime.now().isoformat()))
                print(f'  ✅ Criada carteira "Carteira Padrão" como fallback')
                if old_wallet_id:
                    wallet_id_map[old_wallet_id] = new_wallet_id
            
            # ===== INSERIR TRANSAÇÃO =====
            cursor.execute('SELECT id FROM transactions WHERE id = %s', (trans_id,))
            if not cursor.fetchone():
                try:
                    cursor.execute('''
                        INSERT INTO transactions 
                        (id, username, type, description, amount, category_id, wallet_id, date, notes, is_transfer, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ''', (
                        trans_id,
                        username,
                        transaction.get('type', 'expense'),
                        transaction.get('description', ''),
                        transaction.get('amount', 0),
                        new_cat_id,
                        new_wallet_id,
                        transaction.get('date', datetime.now().strftime('%Y-%m-%d')),
                        transaction.get('notes', ''),
                        transaction.get('is_transfer', False),
                        transaction.get('created_at', datetime.now().isoformat())
                    ))
                    print(f'  ✅ Transação {transaction.get("description")[:30]}... migrada')
                except Exception as e:
                    print(f'  ⚠️ Erro ao migrar transação {transaction.get("description")[:30]}...: {e}')
            else:
                print(f'  ⏭️ Transação {transaction.get("description")[:30]}... já existe')
        
        print(f'✅ Dados de {username} migrados com sucesso!')
    except Exception as e:
        print(f'❌ Erro ao migrar dados de {username}: {e}')
    finally:
        conn.commit()
        conn.close()

def reset_database():
    """Resetar todas as tabelas (cuidado!)"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Desabilitar verificações de chave estrangeira temporariamente
    cursor.execute('SET session_replication_role = replica;')
    
    # Eliminar tabelas na ordem correta
    cursor.execute('DROP TABLE IF EXISTS transactions CASCADE;')
    cursor.execute('DROP TABLE IF EXISTS categories CASCADE;')
    cursor.execute('DROP TABLE IF EXISTS wallets CASCADE;')
    cursor.execute('DROP TABLE IF EXISTS users CASCADE;')
    
    # Reabilitar verificações
    cursor.execute('SET session_replication_role = DEFAULT;')
    
    conn.commit()
    conn.close()
    print('🗑️ Base de dados resetada com sucesso!')

def migrate_all():
    """Executar migração completa"""
    print('🔄 Iniciando migração para Neon...')
    print('=' * 50)
    
    # Perguntar se quer resetar
    print('\n⚠️ ATENÇÃO: Este script vai recriar todas as tabelas.')
    resposta = input('Deseja resetar a base de dados antes de migrar? (s/N): ')
    
    if resposta.lower() == 's':
        reset_database()
    
    # Verificar se os diretórios existem
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        print(f'📁 Pasta {DATA_DIR} criada')
    
    if not os.path.exists(TRANSACTIONS_DIR):
        os.makedirs(TRANSACTIONS_DIR)
        print(f'📁 Pasta {TRANSACTIONS_DIR} criada')
    
    # Criar tabelas
    print('\n📋 A criar tabelas...')
    create_tables()
    
    # Migrar utilizadores
    print('\n📋 A migrar utilizadores...')
    migrate_users()
    
    # Migrar dados de cada utilizador
    print('\n📋 A migrar dados dos utilizadores...')
    if os.path.exists(TRANSACTIONS_DIR):
        files = os.listdir(TRANSACTIONS_DIR)
        if files:
            for file in files:
                if file.endswith('.json'):
                    username = file.replace('.json', '')
                    print(f'\n👤 A migrar {username}...')
                    migrate_user_data(username)
        else:
            print('⚠️ Nenhum ficheiro de transações encontrado')
    else:
        print(f'⚠️ Diretório {TRANSACTIONS_DIR} não encontrado')
    
    print('\n' + '=' * 50)
    print('✅ Migração concluída com sucesso!')
    print(f'🔑 Utilizadores migrados com senha padrão: {DEFAULT_PASSWORD}')

if __name__ == '__main__':
    migrate_all()