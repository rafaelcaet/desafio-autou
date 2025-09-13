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

app = Flask(__name__, static_folder='../app', static_url_path='')
CORS(app)

# Rota para servir o frontend
@app.route('/')
def serve_frontend():
    return app.send_static_file('index.html')

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
    
    def _clean_and_parse_json(self, content):
        """Limpa e tenta parsear JSON da resposta da IA"""
        import re
        
        # Remover markdown e caracteres extras
        content = content.replace('```json', '').replace('```', '').strip()
        
        # Remover possível texto antes e depois do JSON
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            content = json_match.group(0)
        
        try:
            result = json.loads(content)
            
            # Validar estrutura esperada
            if not all(key in result for key in ['category', 'confidence', 'reasoning']):
                raise ValueError("JSON não contém todos os campos necessários")
            
            # Validar valores
            if result['category'] not in ['Produtivo', 'Improdutivo']:
                result['category'] = 'Produtivo'
            
            if not isinstance(result['confidence'], (int, float)) or not 0 <= result['confidence'] <= 1:
                result['confidence'] = 0.8
            
            return result
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Erro ao parsear JSON: {e}")
            return None
        
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

            IMPORTANTE: Responda APENAS com um JSON válido no formato exato:
            {{
                "category": "Produtivo",
                "confidence": 0.9,
                "reasoning": "Sua explicação aqui"
            }}
            
            NÃO adicione texto antes ou depois do JSON. NÃO use markdown.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Você é um classificador de emails. SEMPRE responda com JSON válido no formato: {\"category\": \"Produtivo\", \"confidence\": 0.9, \"reasoning\": \"explicação\"}. NUNCA adicione texto extra."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=200
            )
            
            content = response.choices[0].message.content.strip()
            logger.warning(f"Resposta bruta da IA: {content}")
            
            # Usar função auxiliar para limpar e parsear JSON
            result = self._clean_and_parse_json(content)
            
            # Se falhou o parsing, usar fallback
            if result is None:
                import re
                logger.warning(f"Fallback ativado para conteúdo: {content}")
                
                category = "Produtivo"
                confidence = 0.7
                reasoning = content[:200] if content else "Classificação automática"
                
                # Tentar identificar categoria no texto
                if any(word in content.lower() for word in ["improdutivo", "não requer", "agradecimento", "parabéns"]):
                    category = "Improdutivo"
                
                # Tentar extrair confiança se mencionada
                confidence_match = re.search(r'confidence["\s:]+([0-9.]+)', content.lower())
                if confidence_match:
                    try:
                        confidence = float(confidence_match.group(1))
                        confidence = max(0, min(1, confidence))  # Garantir entre 0 e 1
                    except:
                        pass
                
                result = {
                    "category": category,
                    "confidence": confidence,
                    "reasoning": reasoning
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
        
        # verifica se é json e se tem texto
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
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('RAILWAY_ENVIRONMENT') != 'production'
    app.run(debug=debug, host='0.0.0.0', port=port)
