from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import uuid
import psycopg2
import psycopg2.pool
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

app = Flask(__name__)
app.secret_key = 'fincontrol_secret_key_2026'

# ============ CONFIGURAÇÃO NEON COM POOL ============
DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    raise ValueError('⚠️ DATABASE_URL não encontrada! Define a variável de ambiente.')

# Criar pool de conexões
try:
    db_pool = psycopg2.pool.SimpleConnectionPool(
        1,   # min connections
        10,  # max connections
        dsn=DATABASE_URL
    )
    print('✅ Pool de conexões criado com sucesso!')
except Exception as e:
    print(f'❌ Erro ao criar pool: {e}')
    db_pool = None

@contextmanager
def get_db():
    """Obter conexão do pool"""
    if db_pool is None:
        conn = psycopg2.connect(DATABASE_URL)
        try:
            yield conn
        finally:
            conn.close()
    else:
        conn = db_pool.getconn()
        try:
            yield conn
        finally:
            db_pool.putconn(conn)

# ============ MOEDAS SUPORTADAS ============
MOEDAS = {
    'MZN': {'nome': 'Metical', 'simbolo': 'MT', 'pais': 'Moçambique'},
    'USD': {'nome': 'Dólar Americano', 'simbolo': '$', 'pais': 'Estados Unidos'},
    'EUR': {'nome': 'Euro', 'simbolo': '€', 'pais': 'Europa'},
    'GBP': {'nome': 'Libra Esterlina', 'simbolo': '£', 'pais': 'Reino Unido'},
    'ZAR': {'nome': 'Rand', 'simbolo': 'R', 'pais': 'África do Sul'},
    'AOA': {'nome': 'Kwanza', 'simbolo': 'Kz', 'pais': 'Angola'},
    'BRL': {'nome': 'Real', 'simbolo': 'R$', 'pais': 'Brasil'},
    'KES': {'nome': 'Xelim Queniano', 'simbolo': 'KSh', 'pais': 'Quénia'},
    'TZS': {'nome': 'Xelim Tanzaniano', 'simbolo': 'TSh', 'pais': 'Tanzânia'},
    'UGX': {'nome': 'Xelim Ugandês', 'simbolo': 'USh', 'pais': 'Uganda'},
    'NGN': {'nome': 'Naira', 'simbolo': '₦', 'pais': 'Nigéria'},
    'GHS': {'nome': 'Cedi', 'simbolo': '₵', 'pais': 'Gana'},
    'EGP': {'nome': 'Libra Egípcia', 'simbolo': 'E£', 'pais': 'Egipto'},
    'MAD': {'nome': 'Dirham', 'simbolo': 'DH', 'pais': 'Marrocos'},
    'CNY': {'nome': 'Yuan', 'simbolo': '¥', 'pais': 'China'},
    'JPY': {'nome': 'Iene', 'simbolo': '¥', 'pais': 'Japão'},
    'INR': {'nome': 'Rúpia Indiana', 'simbolo': '₹', 'pais': 'Índia'},
    'AUD': {'nome': 'Dólar Australiano', 'simbolo': 'A$', 'pais': 'Austrália'},
    'CAD': {'nome': 'Dólar Canadiano', 'simbolo': 'C$', 'pais': 'Canadá'},
    'CHF': {'nome': 'Franco Suíço', 'simbolo': 'CHF', 'pais': 'Suíça'},
}

PAISES = [
    'Moçambique', 'Angola', 'África do Sul', 'Brasil', 'Portugal',
    'Estados Unidos', 'Reino Unido', 'França', 'Alemanha', 'Espanha',
    'Itália', 'Canadá', 'Austrália', 'Japão', 'China', 'Índia',
    'Quénia', 'Tanzânia', 'Uganda', 'Nigéria', 'Gana', 'Egipto',
    'Marrocos', 'Suíça'
]

# ============ FUNÇÕES DA BASE DE DADOS ============

# --- Utilizadores ---

def get_user(username):
    with get_db() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        user = cursor.fetchone()
        return dict(user) if user else None

def create_user(username, password_hash, nome='', apelido='', pais='Moçambique', moeda='MZN'):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (username, password, nome, apelido, pais, moeda, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (username, password_hash, nome, apelido, pais, moeda, datetime.now().isoformat()))
        conn.commit()

def update_user(username, data):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users SET 
                nome = COALESCE(%s, nome),
                apelido = COALESCE(%s, apelido),
                pais = COALESCE(%s, pais),
                moeda = COALESCE(%s, moeda)
            WHERE username = %s
        ''', (data.get('nome'), data.get('apelido'), data.get('pais'), data.get('moeda'), username))
        conn.commit()

# --- Carteiras ---

def get_user_wallets(username):
    with get_db() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('SELECT * FROM wallets WHERE username = %s ORDER BY created_at', (username,))
        wallets = cursor.fetchall()
        return [dict(w) for w in wallets]

def create_wallet(username, name, type, balance=0, icon='💳'):
    wallet_id = str(uuid.uuid4())
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO wallets (id, username, name, type, balance, icon, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (wallet_id, username, name, type, balance, icon, datetime.now().isoformat()))
        conn.commit()
    return wallet_id

def update_wallet_balance(wallet_id, new_balance):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE wallets SET balance = %s WHERE id = %s', (new_balance, wallet_id))
        conn.commit()

def delete_wallet(wallet_id, username):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM wallets WHERE id = %s AND username = %s', (wallet_id, username))
        conn.commit()

# --- Categorias ---

def get_user_categories(username, category_type=None):
    with get_db() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        if category_type:
            cursor.execute('SELECT * FROM categories WHERE username = %s AND type = %s ORDER BY created_at', (username, category_type))
        else:
            cursor.execute('SELECT * FROM categories WHERE username = %s ORDER BY created_at', (username,))
        categories = cursor.fetchall()
        return [dict(c) for c in categories]

def create_category(username, name, category_type, icon='📌'):
    cat_id = str(uuid.uuid4())
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO categories (id, username, name, icon, type, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (cat_id, username, name, icon, category_type, datetime.now().isoformat()))
        conn.commit()
    return cat_id

def delete_category(category_id, username):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM categories WHERE id = %s AND username = %s', (category_id, username))
        conn.commit()

# --- Transações ---

def create_transaction(username, transaction_type, description, amount, category_id, wallet_id, date, notes='', taxa=0, total_amount=None):
    trans_id = str(uuid.uuid4())
    if total_amount is None:
        total_amount = amount + taxa
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO transactions 
            (id, username, type, description, amount, taxa, total_amount, category_id, wallet_id, date, notes, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (trans_id, username, transaction_type, description, amount, taxa, total_amount, category_id, wallet_id, date, notes, datetime.now().isoformat()))
        
        # Atualizar saldo da carteira (usando total_amount)
        cursor.execute('SELECT balance FROM wallets WHERE id = %s', (wallet_id,))
        result = cursor.fetchone()
        if result:
            current_balance = result[0]
            if transaction_type == 'income':
                new_balance = current_balance + total_amount
            else:
                new_balance = current_balance - total_amount
            cursor.execute('UPDATE wallets SET balance = %s WHERE id = %s', (new_balance, wallet_id))
        
        conn.commit()
    return trans_id

def update_transaction(username, transaction_id, data):
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Buscar transação antiga
        cursor.execute('SELECT * FROM transactions WHERE id = %s AND username = %s', (transaction_id, username))
        old_trans = cursor.fetchone()
        if not old_trans:
            return False
        
        old_cols = [desc[0] for desc in cursor.description]
        old = dict(zip(old_cols, old_trans))
        
        # Reverter saldo antigo (usando total_amount)
        cursor.execute('SELECT balance FROM wallets WHERE id = %s', (old['wallet_id'],))
        result = cursor.fetchone()
        if result:
            old_balance = result[0]
            old_total = old.get('total_amount', old['amount'])
            if old['type'] == 'income':
                new_old_balance = old_balance - old_total
            else:
                new_old_balance = old_balance + old_total
            cursor.execute('UPDATE wallets SET balance = %s WHERE id = %s', (new_old_balance, old['wallet_id']))
        
        # Atualizar transação
        cursor.execute('''
            UPDATE transactions SET
                type = %s,
                description = %s,
                amount = %s,
                taxa = %s,
                total_amount = %s,
                category_id = %s,
                wallet_id = %s,
                date = %s,
                notes = %s
            WHERE id = %s AND username = %s
        ''', (data['type'], data['description'], data['amount'], data.get('taxa', 0), data.get('total_amount', data['amount'] + data.get('taxa', 0)), data['category_id'], data['wallet_id'], data['date'], data.get('notes', ''), transaction_id, username))
        
        # Aplicar novo saldo
        cursor.execute('SELECT balance FROM wallets WHERE id = %s', (data['wallet_id'],))
        result = cursor.fetchone()
        if result:
            current_balance = result[0]
            new_total = data.get('total_amount', data['amount'] + data.get('taxa', 0))
            if data['type'] == 'income':
                new_balance = current_balance + new_total
            else:
                new_balance = current_balance - new_total
            cursor.execute('UPDATE wallets SET balance = %s WHERE id = %s', (new_balance, data['wallet_id']))
        
        conn.commit()
    return True

def delete_transaction(username, transaction_id):
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Buscar transação
        cursor.execute('SELECT * FROM transactions WHERE id = %s AND username = %s', (transaction_id, username))
        trans = cursor.fetchone()
        if not trans:
            return False
        
        trans_cols = [desc[0] for desc in cursor.description]
        trans_data = dict(zip(trans_cols, trans))
        
        # Reverter saldo (usando total_amount)
        cursor.execute('SELECT balance FROM wallets WHERE id = %s', (trans_data['wallet_id'],))
        result = cursor.fetchone()
        if result:
            current_balance = result[0]
            total_amount = trans_data.get('total_amount', trans_data['amount'])
            if trans_data['type'] == 'income':
                new_balance = current_balance - total_amount
            else:
                new_balance = current_balance + total_amount
            cursor.execute('UPDATE wallets SET balance = %s WHERE id = %s', (new_balance, trans_data['wallet_id']))
        
        # Eliminar transação
        cursor.execute('DELETE FROM transactions WHERE id = %s AND username = %s', (transaction_id, username))
        
        conn.commit()
    return True

def get_user_transactions(username, limit=None):
    with get_db() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        query = 'SELECT * FROM transactions WHERE username = %s ORDER BY date DESC, created_at DESC'
        if limit:
            query += f' LIMIT {limit}'
        cursor.execute(query, (username,))
        transactions = cursor.fetchall()
        
        # Converter datetime e date para strings
        result = []
        for t in transactions:
            t_dict = dict(t)
            if t_dict.get('date') and hasattr(t_dict['date'], 'strftime'):
                t_dict['date'] = t_dict['date'].strftime('%Y-%m-%d')
            if t_dict.get('created_at') and hasattr(t_dict['created_at'], 'strftime'):
                t_dict['created_at'] = t_dict['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            result.append(t_dict)
        
        return result

def get_user_investments(username):
    with get_db() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('SELECT * FROM transactions WHERE username = %s AND type = %s ORDER BY date DESC', (username, 'investment'))
        investments = cursor.fetchall()
        
        result = []
        for inv in investments:
            inv_dict = dict(inv)
            if inv_dict.get('date') and hasattr(inv_dict['date'], 'strftime'):
                inv_dict['date'] = inv_dict['date'].strftime('%Y-%m-%d')
            if inv_dict.get('created_at') and hasattr(inv_dict['created_at'], 'strftime'):
                inv_dict['created_at'] = inv_dict['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            result.append(inv_dict)
        
        return result

# --- Transferências ---

def transfer_money(username, from_wallet_id, to_wallet_id, amount, description, date):
    if from_wallet_id == to_wallet_id:
        return False
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Verificar saldo da carteira de origem
        cursor.execute('SELECT balance FROM wallets WHERE id = %s AND username = %s', (from_wallet_id, username))
        result = cursor.fetchone()
        if not result or result[0] < amount:
            return False
        
        # Buscar categorias
        cursor.execute('SELECT id FROM categories WHERE username = %s AND name = %s AND type = %s', (username, 'Outros', 'expense'))
        from_cat = cursor.fetchone()
        from_cat_id = from_cat[0] if from_cat else None
        
        cursor.execute('SELECT id FROM categories WHERE username = %s AND name = %s AND type = %s', (username, 'Outros', 'income'))
        to_cat = cursor.fetchone()
        to_cat_id = to_cat[0] if to_cat else None
        
    # Criar transação de saída
    if from_cat_id:
        create_transaction(username, 'expense', f'Transferência: {description}', amount, from_cat_id, from_wallet_id, date, f'Transferência para {to_wallet_id}')
    
    # Criar transação de entrada
    if to_cat_id:
        create_transaction(username, 'income', f'Transferência: {description}', amount, to_cat_id, to_wallet_id, date, f'Transferência de {from_wallet_id}')
    
    return True

# ============ FUNÇÕES DE ALERTAS ============

def gerar_alertas(username):
    transactions = get_user_transactions(username)
    wallets = get_user_wallets(username)
    user = get_user(username)
    
    if not user:
        return [{'tipo': 'info', 'mensagem': 'Utilizador não encontrado'}]
    
    moeda = user.get('moeda', 'MZN')
    
    if not transactions:
        return [{'tipo': 'info', 'mensagem': 'Comece a registar suas transações para receber alertas personalizados!'}]
    
    total_received = sum(t.get('total_amount', t['amount']) for t in transactions if t['type'] == 'income')
    total_expenses = sum(t.get('total_amount', t['amount']) for t in transactions if t['type'] == 'expense')
    total_invested = sum(t.get('total_amount', t['amount']) for t in transactions if t['type'] == 'investment')
    total_balance = sum(w['balance'] for w in wallets)
    
    alertas = []
    
    if total_received > 0:
        alertas.append({
            'tipo': 'success',
            'mensagem': f'💰 Recebeste um total de {total_received:.2f} {moeda}. Continue assim!'
        })
    
    if total_expenses > 0:
        alertas.append({
            'tipo': 'info',
            'mensagem': f'💸 Gastaste {total_expenses:.2f} {moeda}. Verifica se está dentro do orçamento.'
        })
    
    if total_invested > 0:
        alertas.append({
            'tipo': 'success',
            'mensagem': f'📈 Investiste {total_invested:.2f} {moeda}. Bom trabalho!'
        })
    
    wallet_total = total_balance
    calculated_balance = total_received - total_expenses - total_invested
    
    if abs(wallet_total - calculated_balance) > 0.01:
        alertas.append({
            'tipo': 'warning',
            'mensagem': f'⚠️ Discrepância detectada! Saldo das carteiras ({wallet_total:.2f}) não coincide com o saldo calculado ({calculated_balance:.2f}). Verifique as transações.'
        })
    
    if total_expenses > total_received * 0.7 and total_received > 0:
        alertas.append({
            'tipo': 'warning',
            'mensagem': '⚠️ Estás a gastar mais de 70% do que recebes. Tenta reduzir gastos ou aumentar receitas.'
        })
    
    if total_received > total_expenses + total_invested:
        poupanca = total_received - total_expenses - total_invested
        alertas.append({
            'tipo': 'success',
            'mensagem': f'✅ Estás a poupar {poupanca:.2f} {moeda}. Excelente!'
        })
    
    return alertas

# ============ ROTAS ============

@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = get_user(username)
        if user and check_password_hash(user['password'], password):
            session['username'] = username
            return redirect(url_for('dashboard'))
        return render_template('login.html', error='Usuário ou senha inválidos')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        nome = request.form.get('nome')
        apelido = request.form.get('apelido')
        pais = request.form.get('pais')
        moeda = request.form.get('moeda')
        
        if password != confirm_password:
            return render_template('register.html', error='As senhas não coincidem', paises=PAISES, moedas=MOEDAS)
        
        if get_user(username):
            return render_template('register.html', error='Usuário já existe', paises=PAISES, moedas=MOEDAS)
        
        password_hash = generate_password_hash(password)
        create_user(username, password_hash, nome, apelido, pais, moeda)
        
        # Criar carteira padrão
        create_wallet(username, 'Dinheiro em Mão', 'physical_cash', 0, '💰')
        
        # Criar categorias padrão
        categorias_padrao = {
            'income': [
                ('Salário', '💼'), ('Freelance', '💻'), ('Vendas', '🛒'),
                ('Investimentos', '📈'), ('Presentes', '🎁'), ('Outros', '📌')
            ],
            'expense': [
                ('Habitação', '🏠'), ('Alimentação', '🍽️'), ('Transporte', '🚗'),
                ('Saúde', '💊'), ('Lazer', '🎮'), ('Dívidas', '💳'),
                ('Presentes', '🎁'), ('Desperdício', '❌'), ('Comunicação', '📱'),
                ('Educação', '📚'), ('Outros', '📌')
            ]
        }
        
        for cat_type, cats in categorias_padrao.items():
            for name, icon in cats:
                create_category(username, name, cat_type, icon)
        
        return redirect(url_for('login'))
    
    return render_template('register.html', paises=PAISES, moedas=MOEDAS)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    user = get_user(username)
    wallets = get_user_wallets(username)
    transactions = get_user_transactions(username, 5)
    
    # Calcular totais de forma eficiente
    all_transactions = get_user_transactions(username)
    total_received = sum(t.get('total_amount', t['amount']) for t in all_transactions if t['type'] == 'income')
    total_expenses = sum(t.get('total_amount', t['amount']) for t in all_transactions if t['type'] == 'expense')
    total_invested = sum(t.get('total_amount', t['amount']) for t in all_transactions if t['type'] == 'investment')
    total_balance = sum(w['balance'] for w in wallets)
    
    moeda = user.get('moeda', 'MZN')
    simbolo = MOEDAS.get(moeda, {}).get('simbolo', 'MT')
    
    return render_template('dashboard.html',
        username=username,
        nome=user.get('nome', username),
        moeda=moeda,
        simbolo=simbolo,
        data={'wallets': wallets, 'transactions': transactions},
        wallets=wallets,
        total_received=total_received,
        total_expenses=total_expenses,
        total_invested=total_invested,
        total_balance=total_balance,
        transactions=transactions
    )

@app.route('/gastos', methods=['GET', 'POST'])
def gastos():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    user = get_user(username)
    wallets = get_user_wallets(username)
    categories = get_user_categories(username, 'expense')
    moeda = user.get('moeda', 'MZN')
    simbolo = MOEDAS.get(moeda, {}).get('simbolo', 'MT')
    
    if request.method == 'POST':
        description = request.form.get('description')
        amount = float(request.form.get('amount'))
        taxa = float(request.form.get('taxa', 0))
        total_amount = float(request.form.get('total_amount', amount + taxa))
        category_id = request.form.get('category_id')
        wallet_id = request.form.get('wallet_id')
        date = request.form.get('date') or datetime.now().strftime('%Y-%m-%d')
        transaction_id = request.form.get('transaction_id')
        notes = request.form.get('notes', '')
        
        if transaction_id:
            update_transaction(username, transaction_id, {
                'type': 'expense',
                'description': description,
                'amount': amount,
                'taxa': taxa,
                'total_amount': total_amount,
                'category_id': category_id,
                'wallet_id': wallet_id,
                'date': date,
                'notes': notes
            })
        else:
            create_transaction(username, 'expense', description, amount, category_id, wallet_id, date, notes, taxa, total_amount)
        
        return redirect(url_for('gastos'))
    
    transactions = get_user_transactions(username)
    gastos = [t for t in transactions if t['type'] == 'expense']
    total_gastos = sum(t.get('total_amount', t['amount']) for t in gastos)
    
    edit_id = request.args.get('edit_id')
    
    return render_template('gastos.html',
        username=username,
        nome=user.get('nome', username),
        moeda=moeda,
        simbolo=simbolo,
        data={'wallets': wallets, 'categories': {'expense': categories}},
        categories=categories,
        wallets=wallets,
        transactions=gastos,
        total_gastos=total_gastos,
        edit_id=edit_id
    )

@app.route('/recebimentos', methods=['GET', 'POST'])
def recebimentos():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    user = get_user(username)
    wallets = get_user_wallets(username)
    categories = get_user_categories(username, 'income')
    moeda = user.get('moeda', 'MZN')
    simbolo = MOEDAS.get(moeda, {}).get('simbolo', 'MT')
    
    if request.method == 'POST':
        description = request.form.get('description')
        amount = float(request.form.get('amount'))
        taxa = float(request.form.get('taxa', 0))
        total_amount = float(request.form.get('total_amount', amount + taxa))
        category_id = request.form.get('category_id')
        wallet_id = request.form.get('wallet_id')
        date = request.form.get('date') or datetime.now().strftime('%Y-%m-%d')
        transaction_id = request.form.get('transaction_id')
        notes = request.form.get('notes', '')
        
        if transaction_id:
            update_transaction(username, transaction_id, {
                'type': 'income',
                'description': description,
                'amount': amount,
                'taxa': taxa,
                'total_amount': total_amount,
                'category_id': category_id,
                'wallet_id': wallet_id,
                'date': date,
                'notes': notes
            })
        else:
            create_transaction(username, 'income', description, amount, category_id, wallet_id, date, notes, taxa, total_amount)
        
        return redirect(url_for('recebimentos'))
    
    transactions = get_user_transactions(username)
    recebimentos = [t for t in transactions if t['type'] == 'income']
    total_recebimentos = sum(t.get('total_amount', t['amount']) for t in recebimentos)
    
    edit_id = request.args.get('edit_id')
    
    return render_template('recebimentos.html',
        username=username,
        nome=user.get('nome', username),
        moeda=moeda,
        simbolo=simbolo,
        data={'wallets': wallets, 'categories': {'income': categories}},
        categories=categories,
        wallets=wallets,
        transactions=recebimentos,
        total_recebimentos=total_recebimentos,
        edit_id=edit_id
    )

@app.route('/investimentos', methods=['GET', 'POST'])
def investimentos():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    user = get_user(username)
    wallets = get_user_wallets(username)
    moeda = user.get('moeda', 'MZN')
    simbolo = MOEDAS.get(moeda, {}).get('simbolo', 'MT')
    
    if request.method == 'POST':
        description = request.form.get('description')
        amount = float(request.form.get('amount'))
        wallet_id = request.form.get('wallet_id')
        date = request.form.get('date') or datetime.now().strftime('%Y-%m-%d')
        transaction_id = request.form.get('transaction_id')
        notes = request.form.get('notes', '')
        
        if transaction_id:
            update_transaction(username, transaction_id, {
                'type': 'investment',
                'description': description,
                'amount': amount,
                'wallet_id': wallet_id,
                'date': date,
                'notes': notes
            })
        else:
            # Buscar categoria 'Investimento' ou criar
            categories = get_user_categories(username, 'expense')
            cat_id = next((c['id'] for c in categories if c['name'] == 'Investimento'), None)
            if not cat_id:
                cat_id = create_category(username, 'Investimento', 'expense', '📈')
            
            create_transaction(username, 'investment', description, amount, cat_id, wallet_id, date, notes)
        
        return redirect(url_for('investimentos'))
    
    investments = get_user_investments(username)
    total_invested = sum(t.get('total_amount', t['amount']) for t in investments)
    
    edit_id = request.args.get('edit_id')
    
    return render_template('investimentos.html',
        username=username,
        nome=user.get('nome', username),
        moeda=moeda,
        simbolo=simbolo,
        data={'wallets': wallets},
        wallets=wallets,
        investments=investments,
        total_invested=total_invested,
        edit_id=edit_id
    )

@app.route('/transferencia', methods=['GET', 'POST'])
def transferencia():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    user = get_user(username)
    wallets = get_user_wallets(username)
    moeda = user.get('moeda', 'MZN')
    simbolo = MOEDAS.get(moeda, {}).get('simbolo', 'MT')
    mensagem = None
    erro = None
    
    if request.method == 'POST':
        from_wallet_id = request.form.get('from_wallet_id')
        to_wallet_id = request.form.get('to_wallet_id')
        amount = float(request.form.get('amount'))
        description = request.form.get('description', 'Movimentação')
        date = request.form.get('date') or datetime.now().strftime('%Y-%m-%d')
        
        if from_wallet_id == to_wallet_id:
            erro = 'Não pode transferir para a mesma carteira'
        else:
            success = transfer_money(username, from_wallet_id, to_wallet_id, amount, description, date)
            if success:
                mensagem = f'Transferência de {amount:.2f} {simbolo} realizada com sucesso!'
            else:
                erro = 'Saldo insuficiente na carteira de origem'
    
    return render_template('transferencia.html',
        username=username,
        nome=user.get('nome', username),
        moeda=moeda,
        simbolo=simbolo,
        data={'wallets': wallets},
        wallets=wallets,
        mensagem=mensagem,
        erro=erro
    )

@app.route('/deletar_transacao/<transaction_id>')
def deletar_transacao(transaction_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    delete_transaction(username, transaction_id)
    return redirect(request.referrer or url_for('dashboard'))

@app.route('/perfil')
def perfil():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    user = get_user(username)
    wallets = get_user_wallets(username)
    transactions = get_user_transactions(username)
    moeda = user.get('moeda', 'MZN')
    simbolo = MOEDAS.get(moeda, {}).get('simbolo', 'MT')
    
    if user and user.get('created_at'):
        if hasattr(user['created_at'], 'strftime'):
            user['created_at'] = user['created_at'].isoformat()
    
    return render_template('perfil.html',
        username=username,
        nome=user.get('nome', username),
        moeda=moeda,
        simbolo=simbolo,
        data={
            'user': user,
            'wallets': wallets,
            'transactions': transactions
        }
    )

@app.route('/configuracoes', methods=['GET', 'POST'])
def configuracoes():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    user = get_user(username)
    wallets = get_user_wallets(username)
    categories_income = get_user_categories(username, 'income')
    categories_expense = get_user_categories(username, 'expense')
    
    if request.method == 'POST':
        update_user(username, {
            'nome': request.form.get('nome', username),
            'apelido': request.form.get('apelido', ''),
            'pais': request.form.get('pais', 'Moçambique'),
            'moeda': request.form.get('moeda', 'MZN')
        })
        return redirect(url_for('configuracoes'))
    
    return render_template('configuracoes.html',
        username=username,
        nome=user.get('nome', username),
        apelido=user.get('apelido', ''),
        pais=user.get('pais', 'Moçambique'),
        moeda=user.get('moeda', 'MZN'),
        paises=PAISES,
        moedas=MOEDAS,
        data={
            'wallets': wallets,
            'categories': {'income': categories_income, 'expense': categories_expense}
        },
        wallets=wallets,
        categories={'income': categories_income, 'expense': categories_expense}
    )

@app.route('/criar_carteira', methods=['POST'])
def criar_carteira():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    create_wallet(
        username,
        request.form.get('name'),
        request.form.get('type'),
        float(request.form.get('balance', 0)),
        request.form.get('icon', '💳')
    )
    
    return redirect(url_for('configuracoes'))

@app.route('/deletar_carteira/<wallet_id>')
def deletar_carteira(wallet_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    delete_wallet(wallet_id, username)
    return redirect(url_for('configuracoes'))

@app.route('/criar_categoria', methods=['POST'])
def criar_categoria():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    create_category(
        username,
        request.form.get('nome'),
        request.form.get('tipo'),
        request.form.get('icon', '📌')
    )
    
    return redirect(url_for('configuracoes'))

@app.route('/deletar_categoria/<tipo>/<category_id>')
def deletar_categoria(tipo, category_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    delete_category(category_id, username)
    return redirect(url_for('configuracoes'))

@app.route('/editar_carteira', methods=['POST'])
def editar_carteira():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    wallet_id = request.form.get('wallet_id')
    name = request.form.get('name')
    type = request.form.get('type')
    icon = request.form.get('icon', '💳')
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE wallets SET 
                name = %s,
                type = %s,
                icon = %s
            WHERE id = %s AND username = %s
        ''', (name, type, icon, wallet_id, username))
        conn.commit()
    
    return redirect(url_for('configuracoes'))

@app.route('/editar_categoria', methods=['POST'])
def editar_categoria():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    category_id = request.form.get('category_id')
    nome = request.form.get('nome')
    icon = request.form.get('icon', '📌')
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE categories SET 
                name = %s,
                icon = %s
            WHERE id = %s AND username = %s
        ''', (nome, icon, category_id, username))
        conn.commit()
    
    return redirect(url_for('configuracoes'))

@app.route('/relatorios')
def relatorios():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    user = get_user(username)
    transactions = get_user_transactions(username)
    categories_income = get_user_categories(username, 'income')
    categories_expense = get_user_categories(username, 'expense')
    moeda = user.get('moeda', 'MZN')
    simbolo = MOEDAS.get(moeda, {}).get('simbolo', 'MT')
    
    total_received = sum(t.get('total_amount', t['amount']) for t in transactions if t['type'] == 'income')
    total_expenses = sum(t.get('total_amount', t['amount']) for t in transactions if t['type'] == 'expense')
    total_invested = sum(t.get('total_amount', t['amount']) for t in transactions if t['type'] == 'investment')
    
    gastos_categoria = {}
    for t in transactions:
        if t['type'] == 'expense':
            cat = t['category_id']
            amount = t.get('total_amount', t['amount'])
            gastos_categoria[cat] = gastos_categoria.get(cat, 0) + amount
    
    receitas_categoria = {}
    for t in transactions:
        if t['type'] == 'income':
            cat = t['category_id']
            amount = t.get('total_amount', t['amount'])
            receitas_categoria[cat] = receitas_categoria.get(cat, 0) + amount
    
    transacoes_mes = {}
    for t in transactions:
        mes = t['date'][:7]
        if mes not in transacoes_mes:
            transacoes_mes[mes] = {'income': 0, 'expense': 0, 'investment': 0}
        amount = t.get('total_amount', t['amount'])
        transacoes_mes[mes][t['type']] += amount
    
    cat_names = {c['id']: c['name'] for c in categories_expense}
    cat_names.update({c['id']: c['name'] for c in categories_income})
    
    return render_template('relatorios.html',
        username=username,
        nome=user.get('nome', username),
        moeda=moeda,
        simbolo=simbolo,
        data={'transactions': transactions},
        total_received=total_received,
        total_expenses=total_expenses,
        total_invested=total_invested,
        gastos_categoria=gastos_categoria,
        receitas_categoria=receitas_categoria,
        transacoes_mes=transacoes_mes,
        cat_names=cat_names
    )

@app.route('/alertas')
def alertas():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    user = get_user(username)
    moeda = user.get('moeda', 'MZN')
    simbolo = MOEDAS.get(moeda, {}).get('simbolo', 'MT')
    
    alertas = gerar_alertas(username)
    
    return render_template('alertas.html',
        username=username,
        nome=user.get('nome', username),
        moeda=moeda,
        simbolo=simbolo,
        data={'alertas': alertas},
        alertas=alertas
    )

# ============ INICIAR APP ============
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)