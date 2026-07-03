from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os
from datetime import datetime
import uuid

app = Flask(__name__)
app.secret_key = 'fincontrol_secret_key_2026'

# ============ CONFIGURAÇÕES ============
DATA_DIR = 'data'
USERS_FILE = os.path.join(DATA_DIR, 'users.json')
TRANSACTIONS_DIR = os.path.join(DATA_DIR, 'transactions')

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

# ============ INICIALIZAR PASTAS ============
def init_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    if not os.path.exists(TRANSACTIONS_DIR):
        os.makedirs(TRANSACTIONS_DIR)
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w') as f:
            json.dump({}, f)

# ============ FUNÇÕES DE UTILIZADOR ============
def load_users():
    with open(USERS_FILE, 'r') as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

def get_user_data(username):
    user_file = os.path.join(TRANSACTIONS_DIR, f'{username}.json')
    if not os.path.exists(user_file):
        initial_data = {
            'username': username,
            'nome': '',
            'apelido': '',
            'pais': 'Moçambique',
            'moeda': 'MZN',
            'wallets': [
                {'id': 'wallet_001', 'name': 'Dinheiro em Mão', 'type': 'physical_cash', 'balance': 0, 'icon': '💰'}
            ],
            'categories': {
                'income': [
                    {'id': 'cat_inc_01', 'name': 'Salário', 'icon': '💼'},
                    {'id': 'cat_inc_02', 'name': 'Freelance', 'icon': '💻'},
                    {'id': 'cat_inc_03', 'name': 'Vendas', 'icon': '🛒'},
                    {'id': 'cat_inc_04', 'name': 'Investimentos', 'icon': '📈'},
                    {'id': 'cat_inc_05', 'name': 'Presentes', 'icon': '🎁'},
                    {'id': 'cat_inc_06', 'name': 'Outros', 'icon': '📌'}
                ],
                'expense': [
                    {'id': 'cat_exp_01', 'name': 'Habitação', 'icon': '🏠'},
                    {'id': 'cat_exp_02', 'name': 'Alimentação', 'icon': '🍽️'},
                    {'id': 'cat_exp_03', 'name': 'Transporte', 'icon': '🚗'},
                    {'id': 'cat_exp_04', 'name': 'Saúde', 'icon': '💊'},
                    {'id': 'cat_exp_05', 'name': 'Lazer', 'icon': '🎮'},
                    {'id': 'cat_exp_06', 'name': 'Dívidas', 'icon': '💳'},
                    {'id': 'cat_exp_07', 'name': 'Presentes', 'icon': '🎁'},
                    {'id': 'cat_exp_08', 'name': 'Desperdício', 'icon': '❌'},
                    {'id': 'cat_exp_09', 'name': 'Comunicação', 'icon': '📱'},
                    {'id': 'cat_exp_10', 'name': 'Educação', 'icon': '📚'},
                    {'id': 'cat_exp_11', 'name': 'Outros', 'icon': '📌'}
                ]
            },
            'transactions': [],
            'investments': []
        }
        with open(user_file, 'w') as f:
            json.dump(initial_data, f, indent=2)
        return initial_data
    with open(user_file, 'r') as f:
        return json.load(f)

def save_user_data(username, data):
    user_file = os.path.join(TRANSACTIONS_DIR, f'{username}.json')
    with open(user_file, 'w') as f:
        json.dump(data, f, indent=2)

# ============ FUNÇÕES DE TRANSAÇÃO ============
def add_transaction(username, transaction):
    data = get_user_data(username)
    transaction['id'] = str(uuid.uuid4())
    transaction['created_at'] = datetime.now().isoformat()
    data['transactions'].append(transaction)
    
    wallet = next((w for w in data['wallets'] if w['id'] == transaction['wallet_id']), None)
    if wallet:
        if transaction['type'] in ['income']:
            wallet['balance'] += transaction['amount']
        elif transaction['type'] in ['expense', 'investment']:
            wallet['balance'] -= transaction['amount']
    
    save_user_data(username, data)
    return transaction

def update_transaction(username, transaction_id, updated_data):
    data = get_user_data(username)
    old_transaction = None
    for t in data['transactions']:
        if t['id'] == transaction_id:
            old_transaction = t.copy()
            break
    
    if not old_transaction:
        return False
    
    # Reverter saldo antigo
    old_wallet = next((w for w in data['wallets'] if w['id'] == old_transaction['wallet_id']), None)
    if old_wallet:
        if old_transaction['type'] in ['income']:
            old_wallet['balance'] -= old_transaction['amount']
        elif old_transaction['type'] in ['expense', 'investment']:
            old_wallet['balance'] += old_transaction['amount']
    
    # Atualizar transação
    for t in data['transactions']:
        if t['id'] == transaction_id:
            t.update(updated_data)
            break
    
    # Aplicar novo saldo
    new_wallet = next((w for w in data['wallets'] if w['id'] == updated_data['wallet_id']), None)
    if new_wallet:
        if updated_data['type'] in ['income']:
            new_wallet['balance'] += updated_data['amount']
        elif updated_data['type'] in ['expense', 'investment']:
            new_wallet['balance'] -= updated_data['amount']
    
    save_user_data(username, data)
    return True

def delete_transaction(username, transaction_id):
    data = get_user_data(username)
    transaction = next((t for t in data['transactions'] if t['id'] == transaction_id), None)
    if transaction:
        wallet = next((w for w in data['wallets'] if w['id'] == transaction['wallet_id']), None)
        if wallet:
            if transaction['type'] in ['income']:
                wallet['balance'] -= transaction['amount']
            elif transaction['type'] in ['expense', 'investment']:
                wallet['balance'] += transaction['amount']
        data['transactions'] = [t for t in data['transactions'] if t['id'] != transaction_id]
        save_user_data(username, data)
        return True
    return False

def transfer_money(username, from_wallet_id, to_wallet_id, amount, description, date):
    if from_wallet_id == to_wallet_id:
        return False
    
    data = get_user_data(username)
    from_wallet = next((w for w in data['wallets'] if w['id'] == from_wallet_id), None)
    to_wallet = next((w for w in data['wallets'] if w['id'] == to_wallet_id), None)
    
    if not from_wallet or not to_wallet:
        return False
    
    if from_wallet['balance'] < amount:
        return False
    
    # Atualizar saldos
    from_wallet['balance'] -= amount
    to_wallet['balance'] += amount
    
    # Criar transações
    today = date or datetime.now().strftime('%Y-%m-%d')
    
    # Saída da carteira de origem
    transaction_out = {
        'id': str(uuid.uuid4()),
        'type': 'expense',
        'description': f'Transferência: {description}',
        'amount': amount,
        'category_id': 'cat_exp_11',
        'wallet_id': from_wallet_id,
        'date': today,
        'notes': f'Transferência para {to_wallet["name"]}',
        'created_at': datetime.now().isoformat(),
        'is_transfer': True
    }
    data['transactions'].append(transaction_out)
    
    # Entrada na carteira de destino
    transaction_in = {
        'id': str(uuid.uuid4()),
        'type': 'income',
        'description': f'Transferência: {description}',
        'amount': amount,
        'category_id': 'cat_inc_06',
        'wallet_id': to_wallet_id,
        'date': today,
        'notes': f'Transferência de {from_wallet["name"]}',
        'created_at': datetime.now().isoformat(),
        'is_transfer': True
    }
    data['transactions'].append(transaction_in)
    
    save_user_data(username, data)
    return True

# ============ FUNÇÕES DE ALERTAS ============
def gerar_alertas(username, data):
    alertas = []
    transactions = data['transactions']
    
    if not transactions:
        return [{'tipo': 'info', 'mensagem': 'Comece a registar suas transações para receber alertas personalizados!'}]
    
    total_received = sum(t['amount'] for t in transactions if t['type'] == 'income')
    total_expenses = sum(t['amount'] for t in transactions if t['type'] == 'expense')
    total_invested = sum(t['amount'] for t in transactions if t['type'] == 'investment')
    total_balance = sum(w['balance'] for w in data['wallets'])
    
    if total_received > 0:
        alertas.append({
            'tipo': 'success',
            'mensagem': f'💰 Recebeste um total de {total_received:.2f} {data["moeda"]}. Continue assim!'
        })
    
    if total_expenses > 0:
        alertas.append({
            'tipo': 'info',
            'mensagem': f'💸 Gastaste {total_expenses:.2f} {data["moeda"]}. Verifica se está dentro do orçamento.'
        })
    
    if total_invested > 0:
        alertas.append({
            'tipo': 'success',
            'mensagem': f'📈 Investiste {total_invested:.2f} {data["moeda"]}. Bom trabalho!'
        })
    
    wallet_total = sum(w['balance'] for w in data['wallets'])
    calculated_balance = total_received - total_expenses - total_invested
    
    if abs(wallet_total - calculated_balance) > 0.01:
        alertas.append({
            'tipo': 'warning',
            'mensagem': f'⚠️ Discrepância detectada! Saldo das carteiras ({wallet_total:.2f}) não coincide com o saldo calculado ({calculated_balance:.2f}). Verifique as transações.'
        })
    
    if total_expenses > total_received * 0.7:
        alertas.append({
            'tipo': 'warning',
            'mensagem': '⚠️ Estás a gastar mais de 70% do que recebes. Tenta reduzir gastos ou aumentar receitas.'
        })
    
    if total_received > total_expenses + total_invested:
        poupanca = total_received - total_expenses - total_invested
        alertas.append({
            'tipo': 'success',
            'mensagem': f'✅ Estás a poupar {poupanca:.2f} {data["moeda"]}. Excelente!'
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
        
        users = load_users()
        if username in users and check_password_hash(users[username]['password'], password):
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
        
        users = load_users()
        if username in users:
            return render_template('register.html', error='Usuário já existe', paises=PAISES, moedas=MOEDAS)
        
        users[username] = {
            'password': generate_password_hash(password),
            'nome': nome,
            'apelido': apelido,
            'pais': pais or 'Moçambique',
            'moeda': moeda or 'MZN',
            'created_at': datetime.now().isoformat()
        }
        save_users(users)
        
        data = get_user_data(username)
        data['nome'] = nome or username
        data['apelido'] = apelido or ''
        data['pais'] = pais or 'Moçambique'
        data['moeda'] = moeda or 'MZN'
        save_user_data(username, data)
        
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
    data = get_user_data(username)
    
    total_received = sum(t['amount'] for t in data['transactions'] if t['type'] == 'income')
    total_expenses = sum(t['amount'] for t in data['transactions'] if t['type'] == 'expense')
    total_invested = sum(t['amount'] for t in data['transactions'] if t['type'] == 'investment')
    total_balance = sum(w['balance'] for w in data['wallets'])
    
    moeda = data.get('moeda', 'MZN')
    simbolo = MOEDAS.get(moeda, {}).get('simbolo', 'MT')
    
    ultimas = data['transactions'][-5:][::-1]
    
    return render_template('dashboard.html',
        username=username,
        nome=data.get('nome', username),
        moeda=moeda,
        simbolo=simbolo,
        data=data,
        wallets=data['wallets'],
        total_received=total_received,
        total_expenses=total_expenses,
        total_invested=total_invested,
        total_balance=total_balance,
        transactions=ultimas
    )

@app.route('/gastos', methods=['GET', 'POST'])
def gastos():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    data = get_user_data(username)
    moeda = data.get('moeda', 'MZN')
    simbolo = MOEDAS.get(moeda, {}).get('simbolo', 'MT')
    
    if request.method == 'POST':
        description = request.form.get('description')
        amount = float(request.form.get('amount'))
        category_id = request.form.get('category_id')
        wallet_id = request.form.get('wallet_id')
        date = request.form.get('date') or datetime.now().strftime('%Y-%m-%d')
        transaction_id = request.form.get('transaction_id')
        
        transaction_data = {
            'type': 'expense',
            'description': description,
            'amount': amount,
            'category_id': category_id,
            'wallet_id': wallet_id,
            'date': date,
            'notes': request.form.get('notes', '')
        }
        
        if transaction_id:
            # Editar transação existente
            update_transaction(username, transaction_id, transaction_data)
        else:
            # Nova transação
            add_transaction(username, transaction_data)
        
        return redirect(url_for('gastos'))
    
    gastos = [t for t in data['transactions'] if t['type'] == 'expense'][::-1]
    total_gastos = sum(t['amount'] for t in gastos)
    
    return render_template('gastos.html',
        username=username,
        nome=data.get('nome', username),
        moeda=moeda,
        simbolo=simbolo,
        data=data,
        categories=data['categories']['expense'],
        wallets=data['wallets'],
        transactions=gastos,
        total_gastos=total_gastos
    )

@app.route('/recebimentos', methods=['GET', 'POST'])
def recebimentos():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    data = get_user_data(username)
    moeda = data.get('moeda', 'MZN')
    simbolo = MOEDAS.get(moeda, {}).get('simbolo', 'MT')
    
    if request.method == 'POST':
        description = request.form.get('description')
        amount = float(request.form.get('amount'))
        category_id = request.form.get('category_id')
        wallet_id = request.form.get('wallet_id')
        date = request.form.get('date') or datetime.now().strftime('%Y-%m-%d')
        transaction_id = request.form.get('transaction_id')
        
        transaction_data = {
            'type': 'income',
            'description': description,
            'amount': amount,
            'category_id': category_id,
            'wallet_id': wallet_id,
            'date': date,
            'notes': request.form.get('notes', '')
        }
        
        if transaction_id:
            update_transaction(username, transaction_id, transaction_data)
        else:
            add_transaction(username, transaction_data)
        
        return redirect(url_for('recebimentos'))
    
    recebimentos = [t for t in data['transactions'] if t['type'] == 'income'][::-1]
    total_recebimentos = sum(t['amount'] for t in recebimentos)
    
    return render_template('recebimentos.html',
        username=username,
        nome=data.get('nome', username),
        moeda=moeda,
        simbolo=simbolo,
        data=data,
        categories=data['categories']['income'],
        wallets=data['wallets'],
        transactions=recebimentos,
        total_recebimentos=total_recebimentos
    )

@app.route('/investimentos', methods=['GET', 'POST'])
def investimentos():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    data = get_user_data(username)
    moeda = data.get('moeda', 'MZN')
    simbolo = MOEDAS.get(moeda, {}).get('simbolo', 'MT')
    
    if request.method == 'POST':
        description = request.form.get('description')
        amount = float(request.form.get('amount'))
        wallet_id = request.form.get('wallet_id')
        date = request.form.get('date') or datetime.now().strftime('%Y-%m-%d')
        transaction_id = request.form.get('transaction_id')
        
        transaction_data = {
            'type': 'investment',
            'description': description,
            'amount': amount,
            'category_id': 'inv_other',
            'wallet_id': wallet_id,
            'date': date,
            'notes': request.form.get('notes', '')
        }
        
        if transaction_id:
            update_transaction(username, transaction_id, transaction_data)
        else:
            add_transaction(username, transaction_data)
        
        return redirect(url_for('investimentos'))
    
    investments = [t for t in data['transactions'] if t['type'] == 'investment'][::-1]
    total_invested = sum(t['amount'] for t in investments)
    
    return render_template('investimentos.html',
        username=username,
        nome=data.get('nome', username),
        moeda=moeda,
        simbolo=simbolo,
        data=data,
        wallets=data['wallets'],
        investments=investments,
        total_invested=total_invested
    )

@app.route('/transferencia', methods=['GET', 'POST'])
def transferencia():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    data = get_user_data(username)
    moeda = data.get('moeda', 'MZN')
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
                data = get_user_data(username)  # Recarregar dados
            else:
                erro = 'Saldo insuficiente na carteira de origem'
    
    return render_template('transferencia.html',
        username=username,
        nome=data.get('nome', username),
        moeda=moeda,
        simbolo=simbolo,
        data=data,
        wallets=data['wallets'],
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

@app.route('/editar_transacao/<transaction_id>')
def editar_transacao(transaction_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    data = get_user_data(username)
    transaction = next((t for t in data['transactions'] if t['id'] == transaction_id), None)
    
    if not transaction:
        return redirect(request.referrer or url_for('dashboard'))
    
    # Redirecionar para a página correta baseada no tipo
    if transaction['type'] == 'expense':
        return redirect(url_for('gastos', edit_id=transaction_id))
    elif transaction['type'] == 'income':
        return redirect(url_for('recebimentos', edit_id=transaction_id))
    else:
        return redirect(url_for('investimentos', edit_id=transaction_id))

@app.route('/perfil')
def perfil():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    data = get_user_data(username)
    moeda = data.get('moeda', 'MZN')
    simbolo = MOEDAS.get(moeda, {}).get('simbolo', 'MT')
    
    return render_template('perfil.html',
        username=username,
        nome=data.get('nome', username),
        moeda=moeda,
        simbolo=simbolo,
        data=data
    )

@app.route('/configuracoes', methods=['GET', 'POST'])
def configuracoes():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    data = get_user_data(username)
    
    if request.method == 'POST':
        data['nome'] = request.form.get('nome', username)
        data['apelido'] = request.form.get('apelido', '')
        data['pais'] = request.form.get('pais', 'Moçambique')
        data['moeda'] = request.form.get('moeda', 'MZN')
        save_user_data(username, data)
        
        users = load_users()
        if username in users:
            users[username]['nome'] = data['nome']
            users[username]['apelido'] = data['apelido']
            users[username]['pais'] = data['pais']
            users[username]['moeda'] = data['moeda']
            save_users(users)
        
        return redirect(url_for('configuracoes'))
    
    return render_template('configuracoes.html',
        username=username,
        nome=data.get('nome', username),
        apelido=data.get('apelido', ''),
        pais=data.get('pais', 'Moçambique'),
        moeda=data.get('moeda', 'MZN'),
        paises=PAISES,
        moedas=MOEDAS,
        data=data,
        wallets=data['wallets'],
        categories=data['categories']
    )

@app.route('/criar_carteira', methods=['POST'])
def criar_carteira():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    data = get_user_data(username)
    
    new_wallet = {
        'id': str(uuid.uuid4()),
        'name': request.form.get('name'),
        'type': request.form.get('type'),
        'balance': float(request.form.get('balance', 0)),
        'icon': request.form.get('icon', '💳')
    }
    data['wallets'].append(new_wallet)
    save_user_data(username, data)
    
    return redirect(url_for('configuracoes'))

@app.route('/deletar_carteira/<wallet_id>')
def deletar_carteira(wallet_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    data = get_user_data(username)
    data['wallets'] = [w for w in data['wallets'] if w['id'] != wallet_id]
    save_user_data(username, data)
    
    return redirect(url_for('configuracoes'))

@app.route('/criar_categoria', methods=['POST'])
def criar_categoria():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    data = get_user_data(username)
    
    tipo = request.form.get('tipo')
    nome = request.form.get('nome')
    icon = request.form.get('icon', '📌')
    
    nova_categoria = {
        'id': str(uuid.uuid4()),
        'name': nome,
        'icon': icon
    }
    
    if tipo == 'income':
        data['categories']['income'].append(nova_categoria)
    else:
        data['categories']['expense'].append(nova_categoria)
    
    save_user_data(username, data)
    return redirect(url_for('configuracoes'))

@app.route('/deletar_categoria/<tipo>/<category_id>')
def deletar_categoria(tipo, category_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    data = get_user_data(username)
    
    if tipo == 'income':
        data['categories']['income'] = [c for c in data['categories']['income'] if c['id'] != category_id]
    else:
        data['categories']['expense'] = [c for c in data['categories']['expense'] if c['id'] != category_id]
    
    save_user_data(username, data)
    return redirect(url_for('configuracoes'))

@app.route('/relatorios')
def relatorios():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    data = get_user_data(username)
    moeda = data.get('moeda', 'MZN')
    simbolo = MOEDAS.get(moeda, {}).get('simbolo', 'MT')
    
    total_received = sum(t['amount'] for t in data['transactions'] if t['type'] == 'income')
    total_expenses = sum(t['amount'] for t in data['transactions'] if t['type'] == 'expense')
    total_invested = sum(t['amount'] for t in data['transactions'] if t['type'] == 'investment')
    
    gastos_categoria = {}
    for t in data['transactions']:
        if t['type'] == 'expense':
            cat = t['category_id']
            gastos_categoria[cat] = gastos_categoria.get(cat, 0) + t['amount']
    
    receitas_categoria = {}
    for t in data['transactions']:
        if t['type'] == 'income':
            cat = t['category_id']
            receitas_categoria[cat] = receitas_categoria.get(cat, 0) + t['amount']
    
    transacoes_mes = {}
    for t in data['transactions']:
        mes = t['date'][:7]
        if mes not in transacoes_mes:
            transacoes_mes[mes] = {'income': 0, 'expense': 0, 'investment': 0}
        transacoes_mes[mes][t['type']] += t['amount']
    
    cat_names = {c['id']: c['name'] for c in data['categories']['expense']}
    cat_names.update({c['id']: c['name'] for c in data['categories']['income']})
    
    return render_template('relatorios.html',
        username=username,
        nome=data.get('nome', username),
        moeda=moeda,
        simbolo=simbolo,
        data=data,
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
    data = get_user_data(username)
    moeda = data.get('moeda', 'MZN')
    simbolo = MOEDAS.get(moeda, {}).get('simbolo', 'MT')
    
    alertas = gerar_alertas(username, data)
    
    return render_template('alertas.html',
        username=username,
        nome=data.get('nome', username),
        moeda=moeda,
        simbolo=simbolo,
        data=data,
        alertas=alertas
    )

# ============ INICIAR APP ============
if __name__ == '__main__':
    init_data_dir()
    # Mudar para production
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)