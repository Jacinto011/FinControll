// ===== SIDEBAR =====
const menuToggle = document.getElementById('menuToggle');
const sidebar = document.getElementById('sidebar');
const sidebarOverlay = document.getElementById('sidebarOverlay');
const sidebarClose = document.getElementById('sidebarClose');

function openSidebar() {
    sidebar.classList.add('open');
    sidebarOverlay.classList.add('open');
    menuToggle.classList.add('active');
}

function closeSidebar() {
    sidebar.classList.remove('open');
    sidebarOverlay.classList.remove('open');
    menuToggle.classList.remove('active');
}

menuToggle.addEventListener('click', openSidebar);
sidebarClose.addEventListener('click', closeSidebar);
sidebarOverlay.addEventListener('click', closeSidebar);

document.querySelectorAll('.sidebar-link').forEach(link => {
    link.addEventListener('click', closeSidebar);
});

// ===== USER DROPDOWN =====
const userToggle = document.getElementById('userToggle');
const userDropdown = document.getElementById('userDropdown');

userToggle.addEventListener('click', function(e) {
    e.stopPropagation();
    userDropdown.classList.toggle('open');
});

document.addEventListener('click', function() {
    userDropdown.classList.remove('open');
});

// ===== TEMA DARK / LIGHT =====
const themeToggle = document.getElementById('themeToggle');
const html = document.documentElement;

const savedTheme = localStorage.getItem('fincontrol-theme') || 'light';
html.setAttribute('data-theme', savedTheme);
updateThemeIcon(savedTheme);

themeToggle.addEventListener('click', function() {
    const currentTheme = html.getAttribute('data-theme');
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    
    html.setAttribute('data-theme', newTheme);
    localStorage.setItem('fincontrol-theme', newTheme);
    updateThemeIcon(newTheme);
});

function updateThemeIcon(theme) {
    const icon = themeToggle.querySelector('.theme-icon');
    icon.textContent = theme === 'dark' ? '☀️' : '🌙';
}

// ===== MODAL FUNCTIONS =====
function openModal(tipo) {
    const modal = document.getElementById('modalOverlay');
    const title = document.getElementById('modalTitle');
    const form = document.getElementById('modalForm');
    const fields = document.getElementById('modalFormFields');
    const submitBtn = document.getElementById('modalSubmitBtn');
    
    // Limpar campos
    document.getElementById('modalTransactionId').value = '';
    
    // Copiar campos do tipo
    const source = document.getElementById(tipo + 'FormData');
    if (source) {
        fields.innerHTML = source.innerHTML;
    }
    
    // Definir ação do formulário
    const tipoMap = {
        'gasto': { action: '/gastos', title: '💸 Novo Gasto', btn: '💸 Registrar Gasto' },
        'recebimento': { action: '/recebimentos', title: '💰 Novo Recebimento', btn: '💰 Registrar Recebimento' },
        'investimento': { action: '/investimentos', title: '📈 Novo Investimento', btn: '📈 Registrar Investimento' }
    };
    
    if (tipoMap[tipo]) {
        form.action = tipoMap[tipo].action;
        title.textContent = tipoMap[tipo].title;
        submitBtn.textContent = tipoMap[tipo].btn;
    }
    
    // Preencher data
    const dateInput = fields.querySelector('input[type="date"]');
    if (dateInput && !dateInput.value) {
        dateInput.value = new Date().toISOString().split('T')[0];
    }
    
    modal.classList.add('open');
}

function openEditModal(tipo, id) {
    // Buscar dados do objeto global
    let dataKey = null;
    if (tipo === 'gasto' && typeof gastosData !== 'undefined') dataKey = gastosData;
    else if (tipo === 'recebimento' && typeof recebimentosData !== 'undefined') dataKey = recebimentosData;
    else if (tipo === 'investimento' && typeof investimentosData !== 'undefined') dataKey = investimentosData;
    
    if (!dataKey || !dataKey[id]) {
        showToast('Erro ao carregar dados para edição', 'error');
        return;
    }
    
    const data = dataKey[id];
    const modal = document.getElementById('modalOverlay');
    const title = document.getElementById('modalTitle');
    const form = document.getElementById('modalForm');
    const fields = document.getElementById('modalFormFields');
    const submitBtn = document.getElementById('modalSubmitBtn');
    const transactionId = document.getElementById('modalTransactionId');
    
    // Copiar campos do tipo
    const source = document.getElementById(tipo + 'FormData');
    if (source) {
        fields.innerHTML = source.innerHTML;
    }
    
    // Preencher campos com os dados
    const inputs = fields.querySelectorAll('input, select');
    inputs.forEach(input => {
        if (data[input.name] !== undefined) {
            input.value = data[input.name];
        }
    });
    
    // Definir ação do formulário
    const tipoMap = {
        'gasto': { action: '/gastos', title: '✏️ Editar Gasto', btn: '💾 Atualizar Gasto' },
        'recebimento': { action: '/recebimentos', title: '✏️ Editar Recebimento', btn: '💾 Atualizar Recebimento' },
        'investimento': { action: '/investimentos', title: '✏️ Editar Investimento', btn: '💾 Atualizar Investimento' }
    };
    
    if (tipoMap[tipo]) {
        form.action = tipoMap[tipo].action;
        title.textContent = tipoMap[tipo].title;
        submitBtn.textContent = tipoMap[tipo].btn;
    }
    
    transactionId.value = id;
    modal.classList.add('open');
}

function closeModal() {
    document.getElementById('modalOverlay').classList.remove('open');
}

function openDeleteModal(id, name) {
    const modal = document.getElementById('deleteModalOverlay');
    const confirmBtn = document.getElementById('deleteConfirmBtn');
    const itemName = document.getElementById('deleteItemName');
    
    itemName.textContent = name || 'Item';
    confirmBtn.href = '/deletar_transacao/' + id;
    modal.classList.add('open');
}

function closeDeleteModal() {
    document.getElementById('deleteModalOverlay').classList.remove('open');
}

// Fechar modais ao clicar fora
document.addEventListener('click', function(e) {
    const modal = document.getElementById('modalOverlay');
    const deleteModal = document.getElementById('deleteModalOverlay');
    
    if (e.target === modal) {
        closeModal();
    }
    if (e.target === deleteModal) {
        closeDeleteModal();
    }
});

// ===== TOAST NOTIFICATIONS =====
function showToast(message, type = 'success') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    
    const icons = {
        success: '✅',
        error: '❌',
        warning: '⚠️',
        info: 'ℹ️'
    };
    
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `<span class="toast-icon">${icons[type] || 'ℹ️'}</span> ${message}`;
    
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.transition = 'opacity 0.5s, transform 0.5s';
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100px)';
        setTimeout(() => toast.remove(), 500);
    }, 3000);
}

// ===== VERIFICAR TOASTS NA PÁGINA =====
document.addEventListener('DOMContentLoaded', function() {
    // Verificar se há mensagens de sucesso/erro no HTML
    const successToast = document.getElementById('successToast');
    const errorToast = document.getElementById('errorToast');
    
    if (successToast) {
        showToast(successToast.textContent.trim(), 'success');
        successToast.remove();
    }
    
    if (errorToast) {
        showToast(errorToast.textContent.trim(), 'error');
        errorToast.remove();
    }
    
    // Preencher data
    const dateInputs = document.querySelectorAll('input[type="date"]');
    const today = new Date().toISOString().split('T')[0];
    
    dateInputs.forEach(input => {
        if (!input.value) {
            input.value = today;
        }
    });
});

// ===== VALIDAR FORMULÁRIOS =====
document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', function(e) {
        const required = this.querySelectorAll('[required]');
        let valid = true;
        
        required.forEach(field => {
            if (!field.value.trim()) {
                field.style.borderColor = '#EF4444';
                valid = false;
            } else {
                field.style.borderColor = '';
            }
        });
        
        if (!valid) {
            e.preventDefault();
            showToast('Por favor, preencha todos os campos obrigatórios.', 'error');
        }
    });
});

console.log('💰 FinControl carregado com sucesso!');
console.log('🌙 Tema atual:', document.documentElement.getAttribute('data-theme'));