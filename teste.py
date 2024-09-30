from google.generativeai.types import HarmCategory, HarmBlockThreshold
from fastapi import FastAPI, UploadFile, File, HTTPException
import google.generativeai as genai
from PyPDF2 import PdfReader
import json
from pymongo import MongoClient
import os
from dotenv import load_dotenv

app = FastAPI(
    docs_url="/"
)

load_dotenv()

api_key = os.getenv('API_KEY')

genai.configure(api_key=api_key)

generation_config = {
    "temperature": 0.5,
    "top_k": 0,
    "top_p": 0.95,
    "max_output_tokens": 1000
}

safety_settings = {
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
}

model_name = "gemini-1.5-flash"

model = genai.GenerativeModel(
    model_name=model_name,
    generation_config=generation_config,
    safety_settings=safety_settings
)



# AQUI É PRA LER O PDF(nem eu li kkkkkk)
def extrairPdf(file: UploadFile):
    reader = PdfReader(file.file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text


#AQUI É AS CONFIGURAÇÕES PRA SE CONECTAR COM O MONGODB
def conectando_no_mongo():
    try:
        cliente = MongoClient('mongodb+srv://pedrolsantos390:mrNO4d6vouZw4XHd@cluster0.degni.mongodb.net/project0?retryWrites=true&w=majority&appName=Cluster0')
        db = cliente['project0']
        colecao = db['response']
        return colecao
    except Exception as e:
        print(f"bah meu , deu erro aqui: {e}")
        return None
    
#aqui slava no banco
def salvarMongo(data):
    colecao = conectando_no_mongo()
    if colecao is not None:
        resultado = colecao.insert_one(data)
        print(f"AEEEE SALVOU!! VAMO COMER UM CHURRASCO AGORA HEHE.")
    else:
        print("Bah meu ,não foi possível salvar no MongoDB .")


@app.post("/chatbot")
async def chatbot(
    file1: UploadFile = File(...), # esse file ai é uma função da fast api pra definir que é um parametro de entrada do tipo arquivo
    file2: UploadFile = File(...), # e esses 3 pontinhos é pra dizer que é obrigatorio , se o cara não entegar o pdf o negócio fica feio pra ele
    messagem: str = "Analise os PDFs"): 


    # extrair texto dos dois PDFs
    pdf1_text = extrairPdf(file1)
    pdf2_text = extrairPdf(file2)

    # aqui é o exemplo que eu usei pra engenharia de prompt 
    exemplo_data = [
        {
            "contrato": {
                "titulo": "Contrato de Consultoria Financeira",
                "partes": {
                    "contratante": {
                        "razao_social": "Nome da Empresa Contratante Ltda.",
                        "cnpj": "00.000.000/0001-00",
                        "endereco": "Endereço da Empresa Contratante"
                    },
                    "contratada": {
                        "razao_social": "Nome da Empresa Contratada Ltda.",
                        "cnpj": "11.111.111/0001-11",
                        "endereco": "Endereço da Empresa Contratada"
                    }
                },
                "assinaturas": {
                    "local": "Local Genérico",
                    "data": "01 de janeiro de 2024",
                    "contratante": "Nome da Empresa Contratante Ltda.",
                    "contratada": "Nome da Empresa Contratada Ltda."
                }
            }
        }
    ]

    
    gemini = model.start_chat(history=[{
        "role": "user",
        "parts": [
            {
                "text": json.dumps(exemplo_data)
            },
            {
                "text": f"texto do PDF 1: {pdf1_text}"
            },
            {
                "text": f"texto do PDF 2: {pdf2_text}"
            },
            {
                "text": "Você é uma especialista em finanças e deve garantir que todas as informações extraídas dos PDFs estejam sempre no formato padrão de JSON que eu forneci."
            }
        ]
    }])


   
    resposta = gemini.send_message(messagem)

    data_to_save = {
        "PDF_1_text": pdf1_text,
        "PDF_2_text": pdf2_text,
        "resposta": resposta.text,
        "mensagem": messagem
    }

    
    salvarMongo(data_to_save)

    return {
        "resposta": resposta.text
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
