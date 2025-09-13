# Classificador Inteligente de Emails

Uma aplicação web que utiliza inteligência artificial para classificar emails automaticamente e sugerir respostas apropriadas, economizando tempo da equipe.

## Funcionalidades

- **Classificação Automática**: Categoriza emails como "Produtivo" ou "Improdutivo"
- **Respostas Inteligentes**: Gera sugestões de resposta baseadas na categoria
- **Múltiplos Formatos**: Suporte para texto direto, arquivos .txt e .pdf
- **Interface Intuitiva**: Design moderno e responsivo
- **Análise Detalhada**: Mostra confiança da classificação e texto processado

## Como Executar

### Pré-requisitos

- Python 3.8 ou superior
- pip (gerenciador de pacotes do Python)
- Navegador web moderno

### Backend (Python Flask)

1. **Navegue até a pasta server:**
   ```bash
   cd server
   ```

2. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Execute a aplicação:**
   ```bash
   python app.py
   ```

4. **O servidor estará rodando em:** `http://localhost:5000`

### Frontend

1. **Navegue até a pasta app:**
   ```bash
   cd app
   ```

2. **Abra o arquivo index.html no navegador:**
   - Duplo clique no arquivo `index.html`
   - Ou use um servidor local como Live Server (VS Code)

## Tutorial

1. **Acesse a aplicação** no navegador
2. **Escolha o método de entrada:**
   - **Digitar Texto:** Cole ou digite o conteúdo do email
   - **Upload de Arquivo:** Envie um arquivo .txt ou .pdf
3. **Clique em "Classificar Email"**
4. **Visualize os resultados:**
   - Categoria (Produtivo/Improdutivo)
   - Nível de confiança
   - Resposta sugerida
   - Detalhes da análise
5. **Use as ações disponíveis:**
   - Copiar resposta
   - Editar resposta
   - Nova análise

## Configurações de ambiente

### Variáveis de Ambiente

Crie um arquivo `.env` na pasta server para configurações opcionais:

```env
# OpenAI API Key (para respostas mais avançadas)
OPENAI_API_KEY=sua_chave_aqui

# Configurações da aplicação
FLASK_ENV=development
FLASK_DEBUG=True
MAX_TEXT_LENGTH=5000
DEFAULT_CONFIDENCE_THRESHOLD=0.7
```

### Personalização

- **Palavras-chave**: Modifique as listas `productive_keywords` e `unproductive_keywords` no arquivo `app.py`
- **Respostas**: Personalize os templates de resposta na função `generate_response()`
- **Interface**: Customize cores e estilos no arquivo `styles.css`

## Categorização

### Produtivo
Emails que requerem ação ou resposta:
- Solicitações de suporte técnico
- Dúvidas sobre o sistema
- Atualizações sobre casos
- Problemas técnicos

### Improdutivo
Emails que não necessitam ação imediata:
- Mensagens de agradecimento
- Felicitações
- Feedback positivo
- Comunicados informativos

## Stacks

### Backend
- **Python 3.8+**
- **Flask** - Framework web
- **Transformers** - Modelos de IA da Hugging Face
- **NLTK** - Processamento de linguagem natural
- **PyPDF2** - Leitura de arquivos PDF
- **Flask-CORS** - Suporte a CORS

### Frontend
- **HTML5** - Estrutura
- **CSS3** - Estilização e animações
- **JavaScript ES6+** - Interatividade
- **Font Awesome** - Ícones

### IA/ML
- **Sentiment Analysis** - Classificação de sentimentos
- **Text Processing** - Pré-processamento de texto
- **Keyword Matching** - Análise por palavras-chave

## Estrutura do Projeto

```
teste-autoU/
├── server/
│   ├── app.py              # Aplicação Flask principal
│   ├── requirements.txt    # Dependências Python
│   └── .env               # Configurações (opcional)
├── app/
│   ├── index.html         # Interface principal
│   ├── styles.css         # Estilos CSS
│   └── script.js          # Lógica JavaScript
└── README.md             # Documentação
```

## Possível solução

### Erro: CORS
- Verifique se o Flask-CORS está instalado
- Confirme que o backend está rodando na porta 5000

### Erro: Arquivo PDF não processa
- Verifique se o PyPDF2 está instalado
- Teste com um arquivo PDF simples

## Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.
# desafio-autou
