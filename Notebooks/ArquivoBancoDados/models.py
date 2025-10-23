from src.core.db import db

class Advogado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    oab_cpf = db.Column(db.String(50), unique=True, nullable=False)
    senha = db.Column(db.String(200), nullable=False)

    def __repr__(self):
        return f"<Advogado {self.oab_cpf}>"
