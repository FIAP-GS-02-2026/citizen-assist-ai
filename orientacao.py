"""Classe Orientacao: um registro da base de conhecimento."""

# Tupla com os campos obrigatórios de cada orientação no JSON.
# Tupla porque a lista de campos não muda durante a execução.
CAMPOS_OBRIGATORIOS = (
    "id", "categoria", "titulo", "palavras_chave", "resposta",
    "documentos", "onde", "fonte", "verificado_em",
)

AVISO = "Aviso: este assistente NÃO é um canal oficial. Confirme no canal oficial antes de agir."


class Orientacao:
    """Guarda os dados de uma orientação e sabe exibi-la na tela."""

    def __init__(self, id, categoria, titulo, palavras_chave, resposta,
                 documentos, onde, fonte, verificado_em):
        self.id = id
        self.categoria = categoria
        self.titulo = titulo
        self.palavras_chave = palavras_chave
        self.resposta = resposta
        self.documentos = documentos
        self.onde = onde
        self.fonte = fonte
        self.verificado_em = verificado_em

    @classmethod
    def de_dicionario(cls, dados):
        """Cria uma Orientacao a partir de um dicionário do JSON.

        Levanta ValueError se faltar algum campo obrigatório ou se o tipo estiver errado.
        """
        faltando = [campo for campo in CAMPOS_OBRIGATORIOS if campo not in dados]
        if faltando:
            raise ValueError("campos ausentes: " + ", ".join(faltando))
        if not isinstance(dados["palavras_chave"], list) or not isinstance(dados["documentos"], list):
            raise ValueError("palavras_chave e documentos precisam ser listas")
        return cls(**{campo: dados[campo] for campo in CAMPOS_OBRIGATORIOS})

    def exibir(self):
        """Mostra a orientação completa, com fonte, data de verificação e aviso."""
        print(f"\n>> {self.titulo} [{self.categoria}]")
        print(self.resposta)
        if self.documentos:
            print("Documentos necessários:")
            for documento in self.documentos:
                print(f"  - {documento}")
        else:
            print("Documentos necessários: nenhum.")
        print(f"Onde: {self.onde}")
        print(f"Fonte: {self.fonte} (verificado em {self.verificado_em})")
        print(AVISO)
