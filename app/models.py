from .app import db  # Importação relativa dentro do pacote

from .app import db

class NewTable(db.Model):
    __tablename__ = 'new_table'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200))

    def __repr__(self):
        return f'<NewTable {self.name}>'


class ExperimentData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False)
    page_variant = db.Column(db.String(10), nullable=False)
    impressions = db.Column(db.Integer, nullable=False)
    clicks = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f'<ExperimentData {self.page_variant} at {self.timestamp}>'
