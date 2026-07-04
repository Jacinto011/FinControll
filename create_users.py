import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash
import uuid
from datetime import datetime

# Carregar variáveis de ambiente
load_dotenv()

# ============ CONFIGURAÇÃO ============
DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    raise ValueError('⚠️ DATABASE_URL não encontrada!')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
TRANSACTIONS_DIR = os.path.join(DATA_DIR, 'transactions')

# ============ CREDENCIAIS DO UTILIZADOR ============
USERNAME = 'JacintoPatricio'
PASSWORD = 'Jacinto2002'
NOME = 'Jacinto'
APELIDO = 'Patrício'
PAIS = 'Moçambique'
MOEDA = 'MZN'

def is_valid_uuid(val):
    try:
        uuid.UUID(str(val))
        return True
    except ValueError:
        return False

def generate_uuid():
    return str(uuid.uuid4())

def get_connection():
    return psycopg2.connect(DATABASE_URL)

def criar_usuario():
    """Criar utilizador com senha encriptada"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Verificar se o utilizador já existe
    cursor.execute('SELECT username FROM users WHERE username = %s', (USERNAME,))
    if cursor.fetchone():
        print(f'⚠️ Utilizador {USERNAME} já existe!')
        conn.close()
        return False
    
    # Encriptar a senha
    password_hash = generate_password_hash(PASSWORD)
    
    # Inserir utilizador
    cursor.execute('''
        INSERT INTO users (username, password, nome, apelido, pais, moeda, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    ''', (USERNAME, password_hash, NOME, APELIDO, PAIS, MOEDA, datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
    
    print(f'✅ Utilizador {USERNAME} criado com sucesso!')
    print(f'🔑 Senha: {PASSWORD}')
    return True

def migrar_dados_do_json():
    """Migrar dados do JSON para o utilizador"""
    # Buscar o ficheiro do utilizador antigo
    user_file = None
    for file in os.listdir(TRANSACTIONS_DIR):
        if file.endswith('.json'):
            user_file = os.path.join(TRANSACTIONS_DIR, file)
            break
    
    if not user_file:
        print('⚠️ Nenhum ficheiro de dados encontrado!')
        return False
    
    print(f'📁 A ler dados de: {user_file}')
    
    with open(user_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # ===== DICIONÁRIO PARA MAPEAR IDs =====
    wallet_id_map = {}
    category_id_map = {}
    
    try:
        # ===== MIGRAR CARTEIRAS =====
        print('\n📋 A migrar carteiras...')
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
                    USERNAME,
                    wallet.get('name', ''),
                    wallet.get('type', 'physical_cash'),
                    wallet.get('balance', 0),
                    wallet.get('icon', '💳'),
                    datetime.now().isoformat()
                ))
                print(f'  ✅ Carteira {wallet.get("name")} migrada')
            else:
                print(f'  ⏭️ Carteira {wallet.get("name")} já existe')
        
        # ===== MIGRAR CATEGORIAS =====
        print('\n📋 A migrar categorias...')
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
                        USERNAME,
                        cat.get('name', ''),
                        cat.get('icon', '📌'),
                        category_type,
                        datetime.now().isoformat()
                    ))
                    print(f'  ✅ Categoria {cat.get("name")} migrada')
                else:
                    print(f'  ⏭️ Categoria {cat.get("name")} já existe')
        
        # ===== MIGRAR TRANSAÇÕES =====
        print('\n📋 A migrar transações...')
        for transaction in data.get('transactions', []):
            trans_id = transaction.get('id')
            if not trans_id or not is_valid_uuid(trans_id):
                trans_id = generate_uuid()
                print(f'  🔄 ID de transação inválido -> novo UUID: {trans_id}')
            
            # Mapear category_id
            old_cat_id = transaction.get('category_id')
            if old_cat_id == 'inv_other':
                # Criar ou usar categoria "Investimento"
                cursor.execute('''
                    SELECT id FROM categories 
                    WHERE username = %s AND name = 'Investimento' AND type = 'expense'
                ''', (USERNAME,))
                result = cursor.fetchone()
                if result:
                    new_cat_id = result[0]
                else:
                    new_cat_id = generate_uuid()
                    cursor.execute('''
                        INSERT INTO categories (id, username, name, icon, type, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    ''', (new_cat_id, USERNAME, 'Investimento', '📈', 'expense', datetime.now().isoformat()))
                    print(f'  ✅ Criada categoria "Investimento"')
            elif old_cat_id in category_id_map:
                new_cat_id = category_id_map[old_cat_id]
            else:
                # Usar categoria "Outros" como fallback
                cursor.execute('''
                    SELECT id FROM categories 
                    WHERE username = %s AND name = 'Outros' AND type = 'expense'
                ''', (USERNAME,))
                result = cursor.fetchone()
                if result:
                    new_cat_id = result[0]
                else:
                    new_cat_id = generate_uuid()
                    cursor.execute('''
                        INSERT INTO categories (id, username, name, icon, type, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    ''', (new_cat_id, USERNAME, 'Outros', '📌', 'expense', datetime.now().isoformat()))
                    print(f'  ✅ Criada categoria "Outros"')
            
            # Mapear wallet_id
            old_wallet_id = transaction.get('wallet_id')
            if old_wallet_id in wallet_id_map:
                new_wallet_id = wallet_id_map[old_wallet_id]
            else:
                # Usar a primeira carteira como fallback
                cursor.execute('SELECT id FROM wallets WHERE username = %s LIMIT 1', (USERNAME,))
                result = cursor.fetchone()
                new_wallet_id = result[0] if result else None
            
            if not new_wallet_id:
                print(f'  ⚠️ Sem carteira para transação {transaction.get("description")[:30]}')
                continue
            
            # Inserir transação
            cursor.execute('SELECT id FROM transactions WHERE id = %s', (trans_id,))
            if not cursor.fetchone():
                try:
                    cursor.execute('''
                        INSERT INTO transactions 
                        (id, username, type, description, amount, category_id, wallet_id, date, notes, is_transfer, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ''', (
                        trans_id,
                        USERNAME,
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
                    print(f'  ⚠️ Erro: {e}')
            else:
                print(f'  ⏭️ Transação já existe')
        
        conn.commit()
        print('\n✅ Todos os dados migrados com sucesso!')
        return True
        
    except Exception as e:
        print(f'❌ Erro: {e}')
        conn.rollback()
        return False
    finally:
        conn.close()

def main():
    print('=' * 50)
    print('🔄 A criar utilizador e migrar dados...')
    print('=' * 50)
    
    # Criar utilizador
    print('\n📋 PASSO 1: Criar utilizador')
    if not criar_usuario():
        print('⚠️ Utilizador já existe, a continuar com a migração...')
    
    # Migrar dados
    print('\n📋 PASSO 2: Migrar dados do JSON')
    migrar_dados_do_json()
    
    print('\n' + '=' * 50)
    print('✅ Processo concluído!')
    print(f'🔑 Faça login com:')
    print(f'   Usuário: {USERNAME}')
    print(f'   Senha: {PASSWORD}')
    print('=' * 50)

if __name__ == '__main__':
    main()