// Detecta automaticamente se é local ou Railway
const API_BASE_URL = window.location.hostname === 'localhost' 
    ? 'http://localhost:5000' 
    : window.location.origin;

const emailForm = document.getElementById('emailForm');
const emailText = document.getElementById('emailText');
const emailFile = document.getElementById('emailFile');
const fileUploadArea = document.getElementById('fileUploadArea');
const fileInfo = document.getElementById('fileInfo');
const submitBtn = document.getElementById('submitBtn');
const resultsSection = document.getElementById('resultsSection');
const charCount = document.getElementById('charCount');

// states
let currentFile = null;
let currentResponse = '';

document.addEventListener('DOMContentLoaded', function() {
    initializeEventListeners();
    checkAPIHealth();
    initializeTheme();
});

function initializeEventListeners() {
    emailForm.addEventListener('submit', handleFormSubmit);
    
    emailText.addEventListener('input', updateCharCount);
    
    emailFile.addEventListener('change', handleFileSelect);
    fileUploadArea.addEventListener('click', () => emailFile.click());
    fileUploadArea.addEventListener('dragover', handleDragOver);
    fileUploadArea.addEventListener('drop', handleFileDrop);
    fileUploadArea.addEventListener('dragleave', handleDragLeave);
    
    document.addEventListener('keydown', handleKeyboardShortcuts);
}


function updateCharCount() {
    const count = emailText.value.length;
    charCount.textContent = count;
    
    if (count > 4500) {
        charCount.style.color = '#e53e3e';
    } else if (count > 4000) {
        charCount.style.color = '#dd6b20';
    } else {
        charCount.style.color = '#718096';
    }
}

function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        processSelectedFile(file);
    }
}

function handleDragOver(event) {
    event.preventDefault();
    fileUploadArea.classList.add('dragover');
}

function handleDragLeave(event) {
    event.preventDefault();
    fileUploadArea.classList.remove('dragover');
}

function handleFileDrop(event) {
    event.preventDefault();
    fileUploadArea.classList.remove('dragover');
    
    const files = event.dataTransfer.files;
    if (files.length > 0) {
        const file = files[0];
        processSelectedFile(file);
        emailFile.files = files;
    }
}

function processSelectedFile(file) {
    const allowedTypes = ['.txt', '.pdf'];
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
    
    if (!allowedTypes.includes(fileExtension)) {
        showNotification('Formato de arquivo não suportado. Use .txt ou .pdf', 'error');
        return;
    }

    const maxSize = 10 * 1024 * 1024;
    if (file.size > maxSize) {
        showNotification('Arquivo muito grande. Tamanho máximo: 10MB', 'error');
        return;
    }
    
    currentFile = file;
    showFileInfo(file);
}

function showFileInfo(file) {
    const fileName = document.querySelector('.file-name');
    fileName.textContent = file.name;
    
    document.querySelector('.file-upload-content').style.display = 'none';
    fileInfo.style.display = 'flex';
}

function hideFileInfo() {
    document.querySelector('.file-upload-content').style.display = 'block';
    fileInfo.style.display = 'none';
}

function removeFile() {
    currentFile = null;
    emailFile.value = '';
    hideFileInfo();
}

async function handleFormSubmit(event) {
    event.preventDefault();
    
    const hasText = emailText.value.trim().length > 0;
    const hasFile = currentFile !== null;
    
    if (!hasText && !hasFile) {
        showNotification('Por favor, forneça um texto ou arquivo para análise', 'error');
        return;
    }
    
    if (hasText && emailText.value.trim().length < 10) {
        showNotification('O texto deve ter pelo menos 10 caracteres', 'error');
        return;
    }
    
    setLoadingState(true);
    
    try {
        
        const formData = new FormData();
        
        if (hasFile) {
            formData.append('file', currentFile);
        } else {
            formData.append('text', emailText.value.trim());
        }
        
        const response = await fetch(`${API_BASE_URL}/classify`, {
            method: 'POST',
            body: formData,
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        
        if (result.success) {
            displayResults(result);
            showNotification('Análise concluída com sucesso!', 'success');
        } else {
            throw new Error(result.error || 'Erro na análise');
        }
        
    } catch (error) {
        console.error('Erro na análise:', error);
        showNotification(`Erro na análise: ${error.message}`, 'error');
    } finally {
        setLoadingState(false);
    }
}

function setLoadingState(isLoading) {
    const submitText = submitBtn.querySelector('span');
    const loadingSpinner = submitBtn.querySelector('.loading-spinner');
    
    submitBtn.disabled = isLoading;
    
    if (isLoading) {
        submitBtn.classList.add('loading');
        submitText.style.display = 'none';
        loadingSpinner.style.display = 'flex';
    } else {
        submitBtn.classList.remove('loading');
        submitText.style.display = 'block';
        loadingSpinner.style.display = 'none';
    }
}

function displayResults(result) {
    currentResponse = result.suggested_response;
    
    resultsSection.style.display = 'block';
    
    displayClassification(result.classification);
    displaySuggestedResponse(result.suggested_response);
    displayAnalysisDetails(result);
    
    // Scrolla pro resultado
    setTimeout(() => {
        resultsSection.scrollIntoView({ 
            behavior: 'smooth', 
            block: 'start',
            inline: 'nearest'
        });
    }, 100);
}

function displayClassification(classification) {
    const categoryResult = document.getElementById('categoryResult');
    const categoryBadge = categoryResult.querySelector('.category-badge');
    const confidenceFill = document.getElementById('confidenceFill');
    const confidenceValue = document.getElementById('confidenceValue');
    const classificationDetails = document.getElementById('classificationDetails');
    
    const category = classification.category;
    categoryBadge.textContent = category;
    categoryBadge.className = `category-badge ${category.toLowerCase() === 'produtivo' ? 'productive' : 'unproductive'}`;
    
    const confidence = Math.round(classification.confidence * 100);
    confidenceFill.style.width = `${confidence}%`;
    confidenceValue.textContent = `${confidence}%`;
    
    let detailsHTML = '';
    
    if (classification.productive_score !== undefined && classification.unproductive_score !== undefined) {
        detailsHTML += `
            <div><strong>Pontuação Produtiva:</strong> ${classification.productive_score}</div>
            <div><strong>Pontuação Improdutiva:</strong> ${classification.unproductive_score}</div>
        `;
    }
    
    if (classification.reasoning) {
        detailsHTML += `<div><strong>Análise:</strong> ${classification.reasoning}</div>`;
    }
    
    if (classification.error) {
        detailsHTML += `<div style="color: #e53e3e;"><strong>Observação:</strong> ${classification.error}</div>`;
    }
    
    classificationDetails.innerHTML = detailsHTML;
}

function displaySuggestedResponse(response) {
    const responseText = document.getElementById('responseText');
    responseText.textContent = response;
}

function displayAnalysisDetails(result) {
    const processedText = document.getElementById('processedText');
    const analysisInfo = document.getElementById('analysisInfo');
    
    processedText.textContent = result.processed_text || 'Texto não disponível';
    
    analysisInfo.innerHTML = `
        <div><strong>Texto Original:</strong> ${result.original_text.length} caracteres</div>
        <div><strong>Texto Processado:</strong> ${result.processed_text ? result.processed_text.length : 0} caracteres</div>
        <div><strong>Categoria:</strong> ${result.classification.category}</div>
        <div><strong>Confiança:</strong> ${Math.round(result.classification.confidence * 100)}%</div>
        ${result.classification.reasoning ? `<div><strong>Justificativa:</strong> ${result.classification.reasoning}</div>` : ''}
        <div><strong>Data/Hora:</strong> ${formatDateTime(result.timestamp)}</div>
    `;
}

function copyResponse() {
    navigator.clipboard.writeText(currentResponse).then(() => {
        showNotification('Copiado!', 'success');
        
        const copyBtn = document.querySelector('.copy-btn');
        const originalText = copyBtn.innerHTML;
        copyBtn.innerHTML = '<i class="fas fa-check"></i> Copiado!';
        copyBtn.style.background = '#c6f6d5';
        copyBtn.style.color = '#22543d';
        
        setTimeout(() => {
            copyBtn.innerHTML = originalText;
            copyBtn.style.background = '';
            copyBtn.style.color = '';
        }, 2000);
    }).catch(() => {
        showNotification('Erro ao copiar resposta', 'error');
    });
}

function editResponse() {
    const modal = document.getElementById('editModal');
    const editTextarea = document.getElementById('editResponseText');
    
    editTextarea.value = currentResponse;
    modal.style.display = 'flex';
    editTextarea.focus();
}

function closeEditModal() {
    const modal = document.getElementById('editModal');
    modal.style.display = 'none';
}

function saveEditedResponse() {
    const editTextarea = document.getElementById('editResponseText');
    const newResponse = editTextarea.value.trim();
    
    if (newResponse.length < 10) {
        showNotification('A resposta deve ter pelo menos 10 caracteres', 'error');
        return;
    }
    
    currentResponse = newResponse;
    displaySuggestedResponse(newResponse);
    closeEditModal();
    showNotification('Resposta atualizada com sucesso!', 'success');
}

function resetForm() {
    emailForm.reset();
    emailText.value = '';
    currentFile = null;
    hideFileInfo();
    updateCharCount();
    
    resultsSection.style.display = 'none';
    
    showTab('text');
    
    window.scrollTo({ top: 0, behavior: 'smooth' });
    
    showNotification('Formulário limpo', 'success');
}

function handleKeyboardShortcuts(event) {
    if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
        event.preventDefault();
        if (!submitBtn.disabled) {
            handleFormSubmit(event);
        }
    }
    
    if (event.key === 'Escape') {
        const modal = document.getElementById('editModal');
        if (modal.style.display === 'flex') {
            closeEditModal();
        }
    }
}

function formatDateTime(timestamp) {
    try {
        const date = new Date(timestamp);
        return date.toLocaleString('pt-BR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch {
        return 'Data não disponível';
    }
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas ${getNotificationIcon(type)}"></i>
            <span>${message}</span>
        </div>
        <button class="notification-close" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${getNotificationColor(type)};
        color: white;
        padding: 15px 20px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 1001;
        max-width: 400px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        animation: slideInRight 0.3s ease-out;
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        if (notification.parentElement) {
            notification.style.animation = 'slideOutRight 0.3s ease-out';
            setTimeout(() => notification.remove(), 300);
        }
    }, 5000);
}


function getNotificationIcon(type) {
    switch (type) {
        case 'success': return 'fa-check-circle';
        case 'error': return 'fa-exclamation-circle';
        case 'warning': return 'fa-exclamation-triangle';
        default: return 'fa-info-circle';
    }
}

function getNotificationColor(type) {
    switch (type) {
        case 'success': return '#48bb78';
        case 'error': return '#e53e3e';
        case 'warning': return '#ed8936';
        default: return '#4299e1';
    }
}

const notificationStyles = document.createElement('style');
notificationStyles.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
    
    .notification-content {
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .notification-close {
        background: none;
        border: none;
        color: white;
        cursor: pointer;
        padding: 5px;
        border-radius: 4px;
        margin-left: 15px;
        opacity: 0.8;
        transition: opacity 0.3s ease;
    }
    
    .notification-close:hover {
        opacity: 1;
        background: rgba(255,255,255,0.1);
    }
`;
document.head.appendChild(notificationStyles);


// THEME
function initializeTheme() {
    const savedTheme = localStorage.getItem('theme');
    document.documentElement.setAttribute('data-theme', savedTheme);
    
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
}

