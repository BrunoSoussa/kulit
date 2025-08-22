import os
import requests
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template
from PIL import Image
from gemini_model import GeminiModelWrapper
from newsapi import NewsApiClient

gemini = GeminiModelWrapper()
app = Flask(__name__)

# Configuração da API de Notícias (substitua pela sua chave da NewsAPI)
NEWS_API_KEY = 'ddc8c0998474470aaffc7ee669211035'  # Esta é uma chave de exemplo, substitua pela sua
newsapi = NewsApiClient(api_key=NEWS_API_KEY)

def load_image_from_file(file):
    try:
        return Image.open(file)
    except Exception as e:
        print(f"Erro ao carregar imagem: {e}")
        return None

# Instancia o wrapper do modelo Gemini
gemini = GeminiModelWrapper()

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        print("Arquivos recebidos:", request.files)
        
        # Verifica se a imagem foi enviada
        if 'image' not in request.files:
            print("Nenhum arquivo de imagem encontrado no request")
            return jsonify({"error": "Nenhuma imagem enviada"}), 400
        
        image_file = request.files['image']
        if not image_file or image_file.filename == '':
            print("Arquivo de imagem vazio")
            return jsonify({"error": "Arquivo de imagem vazio"}), 400
            
        print(f"Arquivo recebido: {image_file.filename}, tipo: {image_file.content_type}")
        
        # Carrega a imagem
        try:
            image = load_image_from_file(image_file)
            if not image:
                print("Falha ao carregar a imagem")
                return jsonify({"error": "Formato de imagem não suportado"}), 400
        except Exception as img_error:
            print(f"Erro ao processar a imagem: {str(img_error)}")
            return jsonify({"error": f"Erro ao processar a imagem: {str(img_error)}"}), 400

        # Prompt estruturado para análise dermatológica
        prompt = """
        Analise esta imagem de pele e retorne um JSON com:
        
        Instruções:
        1. Verifique se a imagem contém pele humana
        2. Analise características como textura, cor e lesões
        3. Liste possíveis condições dermatológicas
        4. Classifique a urgência com base na gravidade
        """
        
        # Gera a resposta combinando imagem e prompt
        try:
            print("Enviando prompt para Gemini...")
            response = gemini.generate_content([prompt, image])
            print("Resposta recebida de Gemini")
            
            if not hasattr(response, 'text') or not response.text:
                print("Resposta vazia do Gemini")
                return jsonify({"error": "Resposta vazia do modelo"}), 500
                
            raw_text = response.text
            print("Resposta bruta (primeiros 500 caracteres):\n", raw_text[:500])
            
            # Extrai a primeira ocorrência de um objeto JSON válido na resposta
            import json, re
            match = re.search(r"\{[\s\S]*\}", raw_text)
            if not match:
                print("JSON não encontrado na resposta")
                return jsonify({
                    "error": "Resposta do modelo em formato inesperado",
                    "raw_preview": raw_text[:500] + "..." if len(raw_text) > 500 else raw_text
                }), 500
                
            json_str = match.group(0)
            try:
                data = json.loads(json_str)
            except json.JSONDecodeError as jde:
                print(f"Erro ao decodificar JSON: {str(jde)}")
                return jsonify({
                    "error": "Resposta do modelo não é um JSON válido",
                    "raw_preview": raw_text[:500] + "..." if len(raw_text) > 500 else raw_text
                }), 500

            # Garante que as chaves esperadas existam
            data.setdefault("pele_humana", False)
            data.setdefault("saudavel", False)
            data.setdefault("caracteristicas", "")
            data.setdefault("possiveis_condicoes", [])

            return jsonify(data), 200
            
        except Exception as gen_error:
            print(f"Erro na geração de conteúdo: {str(gen_error)}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": f"Erro na análise: {str(gen_error)}"}), 500
            
    except Exception as e:
        print(f"Erro inesperado: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Erro inesperado: {str(e)}"}), 500

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/template')
def template():
    return render_template('template.html')

@app.route('/api/news')
def get_news():
    try:
        # Busca notícias sobre câncer de pele nos últimos 30 dias
        from_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        # Primeira busca: notícias específicas sobre câncer de pele
        skin_cancer_news = newsapi.get_everything(
            q='câncer de pele OR "skin cancer"',
            language='pt',
            sort_by='relevancy',
            from_param=from_date,
            page_size=5
        )
        
        # Segunda busca: notícias gerais de saúde no Brasil
        health_news = newsapi.get_top_headlines(
            category='health',
            country='br',
            page_size=5
        )
        
        # Combina e filtra as notícias
        all_articles = []
        
        # Adiciona notícias sobre câncer de pele
        if skin_cancer_news.get('status') == 'ok':
            for article in skin_cancer_news.get('articles', []):
                if article.get('title') and article.get('url'):
                    all_articles.append({
                        'title': article['title'],
                        'description': article.get('description', ''),
                        'url': article['url'],
                        'source': article.get('source', {}).get('name', 'Fonte desconhecida'),
                        'published_at': article.get('publishedAt', ''),
                        'image_url': article.get('urlToImage', '')
                    })
        
        # Adiciona notícias gerais de saúde (se não tivermos notícias suficientes)
        if len(all_articles) < 5 and health_news.get('status') == 'ok':
            for article in health_news.get('articles', []):
                if article.get('title') and article.get('url') and len(all_articles) < 10:  # Limite de 10 notícias no total
                    all_articles.append({
                        'title': article['title'],
                        'description': article.get('description', ''),
                        'url': article['url'],
                        'source': article.get('source', {}).get('name', 'Fonte desconhecida'),
                        'published_at': article.get('publishedAt', ''),
                        'image_url': article.get('urlToImage', '')
                    })
        
        return jsonify({
            'status': 'success',
            'total_results': len(all_articles),
            'articles': all_articles[:10]  # Retorna no máximo 10 notícias
        })
        
    except Exception as e:
        print(f"Erro ao buscar notícias: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Erro ao buscar notícias. Por favor, tente novamente mais tarde.'
        }), 500

if __name__ == '__main__':
    app.run(debug=True)
