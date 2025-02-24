import os
from flask import Flask, request, jsonify
import google.generativeai as genai
from PIL import Image
from google.ai.generativelanguage_v1beta.types import content

# Configure a chave da API
genai.configure(api_key="AIzaSyAgr6SVtn1tfrD_ynYO0eZKXaHQP8ONI28")

class GeminiModelWrapper:
    def __init__(self):
        self.generation_config = {
            "temperature": 1,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
            "response_schema": content.Schema(
                type=content.Type.OBJECT,
                enum=[],
                required=["pele_humana", "saudavel", "caracteristicas"],
                properties={
                    "pele_humana": content.Schema(
                        type=content.Type.BOOLEAN,
                    ),
                    "saudavel": content.Schema(
                        type=content.Type.BOOLEAN,
                    ),
                    "caracteristicas": content.Schema(
                        type=content.Type.STRING,
                    ),
                    "possiveis_condicoes": content.Schema(
                        type=content.Type.ARRAY,
                        items=content.Schema(
                            type=content.Type.OBJECT,
                            properties={
                                "condicao": content.Schema(
                                    type=content.Type.STRING,
                                ),
                                "urgencia": content.Schema(
                                    type=content.Type.STRING,
                                ),
                            },
                        ),
                    ),
                },
            ),
            "response_mime_type": "application/json",
        }
        # Inicializa o modelo Gemini
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-pro",
            generation_config=self.generation_config,
        )

    def generate_content(self, inputs):
        return self.model.generate_content(inputs)
