import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

# Carregar variáveis de ambiente
load_dotenv()

# ============ CONFIGURAÇÃO ============
DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    raise ValueError('⚠️ DATABASE_URL não encontrada!')

# Senha padrão
DEFAULT_PASSWORD = 'Jacinto2002'

def update_all_passwords():
    """Atualizar senha de todos os utilizadores"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Buscar todos os utilizadores
        cursor.execute('SELECT username FROM users')
        users = cursor.fetchall()
        
        if not users:
            print('⚠️ Nenhum utilizador encontrado na base de dados!')
            return
        
        # Encriptar a senha
        password_hash = generate_password_hash(DEFAULT_PASSWORD)
        
        # Atualizar senha para todos os utilizadores
        cursor.execute('UPDATE users SET password = %s', (password_hash,))
        conn.commit()
        
        print(f'✅ Senha atualizada para {len(users)} utilizador(es)!')
        print(f'🔑 Nova senha: {DEFAULT_PASSWORD}')
        
        # Listar utilizadores
        print('\n📋 Utilizadores:')
        for user in users:
            print(f'  - {user["username"]}')
        
        conn.close()
        
    except Exception as e:
        print(f'❌ Erro ao atualizar senhas: {e}')

if __name__ == '__main__':
    update_all_passwords()