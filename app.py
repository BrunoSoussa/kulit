import os
from flask import Flask, request, jsonify, render_template
from PIL import Image
from gemini_model import GeminiModelWrapper
gemini = GeminiModelWrapper()

app = Flask(__name__)

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
    print(request.files)
    # Verifica se a imagem foi enviada
    if 'image' not in request.files:
        return jsonify({"error": "Nenhuma imagem enviada"}), 400
    
    image_file = request.files['image']
    image = load_image_from_file(image_file)
    if not image:
        return jsonify({"error": "Erro ao carregar a imagem"}), 400

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
        response = gemini.generate_content([prompt, image])
        return response.text, 200
    except Exception as e:
        return jsonify({"error": f"Erro na geração de conteúdo: {str(e)}"}), 500

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/template')
def template():
    return render_template('template.html')

if __name__ == '__main__':
    app.run(debug=True)
