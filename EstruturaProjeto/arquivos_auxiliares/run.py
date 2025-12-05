# do modulo src.web.flask_app chama o create_app (pode ver o arquivo desse modulo para vc entender melhor -> control + clique no create_app -> Vai direto para o arquivo)
from src.web.flask_app import create_app


# instanciado a import dele 
app = create_app()

if __name__ == "__main__":
    # debug=True apenas em ambiente de desenvolvimento
    app.run(host="0.0.0.0", port=5000, debug=True)
