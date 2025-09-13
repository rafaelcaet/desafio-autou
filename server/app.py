import os
import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import PyPDF2
import re
from dotenv import load_dotenv

# Config do logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)

try:
    import openai
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError as e:
    logger.error(f"OpenAI não disponível: {e}")
    OpenAI = None
    OPENAI_AVAILABLE = False
except Exception as e:
    logger.error(f"Erro inesperado ao importar OpenAI: {e}")
    OpenAI = None
    OPENAI_AVAILABLE = False

# envs
load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')

app = Flask(__name__)
CORS(app)

# Config OpenAI
openai_client = None
if OPENAI_AVAILABLE and api_key: # valida se a api key está disponível
    try:
        openai_client = OpenAI(api_key=api_key)
        logger.warning("IA configurada e disponível")
    except Exception as e:
        logger.error(f"Erro ao inicializar OpenAI: {e}")
        openai_client = None


class AIEmailService:
    """Serviço de classificação de email"""
    
    def __init__(self):
        self.client = openai_client
        if not self.client:
            raise ValueError("OpenAI client não configurado. Verifique a OPENAI_API_KEY.")
        
    def classify_email(self, text):
        """Classificar email
        Args:
            text: texto do email
        Returns:
            categoria do email
            confiança da classificação
            explicação da classificação
        """
        try:
            prompt = f"""
            Analise o seguinte email e classifique-o como "Produtivo" ou "Improdutivo":

            - Produtivo: emails que requerem ação, contêm dúvidas, problemas, solicitações, ou necessitam resposta
            - Improdutivo: emails de agradecimento, parabenizações, confirmações simples que não requerem ação

            Email: "{text}"

            Responda em formato JSON com:
            - category: "Produtivo" ou "Improdutivo"
            - confidence: número entre 0 e 1
            - reasoning: breve explicação da classificação
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Você é um assistente especializado em classificar emails em português brasileiro. Responda APENAS com JSON válido, sem texto adicional."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=400
            )
            
            content = response.choices[0].message.content.strip()
            
            
            try:
                result = json.loads(content) # json da saida
            except json.JSONDecodeError:
                category = "Produtivo"
                confidence = 0.7
                reasoning = content
                
                if "improdutivo" in content.lower():
                    category = "Improdutivo"
                
                result = {
                    "category": category,
                    "confidence": confidence,
                    "reasoning": reasoning[:200]
                }
            
            return {
                "category": result.get("category", "Produtivo"),
                "confidence": float(result.get("confidence", 0.8)),
                "reasoning": result.get("reasoning", "Classificação automática por IA")
            }
            
        except Exception as e:
            logger.error(f"Erro na classificação por IA: {e}")
            return {
                "category": "Produtivo",
                "confidence": 0.5,
                "reasoning": f"Erro na IA, usando fallback: {str(e)}"
            }
    
    def generate_response(self, text, category):
        """Gerar resposta
        Args:
            text: texto do email
            category: categoria do email
        Returns:
            resposta gerada pela IA
        """
        try:
            if category == "Produtivo":
                prompt = f"""
                Gere uma resposta profissional e empática para este email produtivo (que requer ação):
                
                Email: "{text}"
                
                A resposta deve:
                - Ser em português brasileiro
                - Ser profissional e cordial
                - Confirmar recebimento
                - Indicar próximos passos
                - Ter no máximo 100 palavras
                """
            else:
                prompt = f"""
                Gere uma resposta cordial para este email improdutivo (agradecimento/parabenização):
                
                Email: "{text}"
                
                A resposta deve:
                - Ser em português brasileiro
                - Ser calorosa e agradecida
                - Reconhecer o feedback positivo
                - Ter no máximo 50 palavras
                """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Você é um assistente que gera respostas profissionais para emails em português brasileiro."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=150
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Erro na geração de resposta por IA: {e}")
            if category == "Produtivo":
                return "Olá! Recebemos sua mensagem e nossa equipe irá analisá-la. Retornaremos em breve. Obrigado!"
            else:
                return "Muito obrigado pela sua mensagem! Ficamos felizes com seu contato."
                
class IntelligentEmailService:
    """Serviço inteligente"""
    
    def __init__(self):
        self.ai_service = None
        
        # Tentar inicializar serviço IA
        if openai_client:
            try:
                self.ai_service = AIEmailService()
            except Exception as e:
                logger.error(f"Erro ao inicializar serviço IA: {e}")
                self.ai_service = None
    
    def classify_email(self, text):
        """Classifica email usando a OpenAI
        Args:
            text: texto do email
        Returns:
            categoria do email
            confiança da classificação
            explicação da classificação
        """
        try:
            result = self.ai_service.classify_email(text)
            result['service_used'] = 'AI (OpenAI)'
            return result
        except Exception as e:
            logger.warning(f"IA falhou, usando fallback: {e}")
    
    def generate_response(self, text, category):
        """Gera resposta tentando IA primeiro, fallback para mock"""
        # Tentar IA primeiro
        try:
            return self.ai_service.generate_response(text, category)
        except Exception as e:
            logger.warning(f"IA falhou na resposta, usando fallback: {e}")
        
def get_email_service():
    return IntelligentEmailService()

# instancia o serviço de email
email_service = get_email_service()

def extract_text_from_pdf(pdf_file):
    """Extrair texto de arquivo PDF"""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text.strip()
    except Exception as e:
        logger.error(f"Erro ao extrair texto do PDF: {e}")
        return None


@app.route('/classify', methods=['POST'])
def classify_email():
    try:
        email_text = ""
        
        # verificar se é upload de arquivo
        if 'file' in request.files:
            file = request.files['file']
            if file.filename == '':
                return jsonify({"error": "Nenhum arquivo selecionado"}), 400
            
            # processa PDF
            if file.filename.lower().endswith('.pdf'):
                email_text = extract_text_from_pdf(file)
                if not email_text:
                    return jsonify({"error": "Não foi possível extrair texto do PDF"}), 400
            
            # processa TXT
            elif file.filename.lower().endswith('.txt'):
                email_text = file.read().decode('utf-8')
            
            else:
                return jsonify({"error": "Formato de arquivo não suportado. Use .txt ou .pdf"}), 400
        
        # verifica se é json e se tem texot
        elif request.is_json and 'text' in request.json:
            email_text = request.json['text']
        
        # verifica se é texto direto
        elif 'text' in request.form:
            email_text = request.form['text']
        
        else:
            return jsonify({"error": "Nenhum texto ou arquivo fornecido"}), 400
        
        # valida o texto
        if not email_text or len(email_text.strip()) < 10:
            return jsonify({"error": "Texto muito curto ou vazio"}), 400
        
        # classifica o email
        classification_result = email_service.classify_email(email_text)
        
        # gera resposta
        suggested_response = email_service.generate_response(
            email_text, 
            classification_result['category']
        )
        
        # processa texto para exibicao
        processed_text = ' '.join(email_text.split())

        # retorna um state com os dados
        return jsonify({
            "success": True,
            "original_text": email_text[:500] + "..." if len(email_text) > 500 else email_text,
            "processed_text": processed_text[:200] + "..." if len(processed_text) > 200 else processed_text,
            "classification": classification_result,
            "suggested_response": suggested_response,
            "mode": "intelligent",
            "service_type": classification_result.get('service_used', 'IA Inteligente'),
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erro no endpoint /classify: {e}")
        return jsonify({
            "error": "Erro interno do servidor",
            "details": str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
