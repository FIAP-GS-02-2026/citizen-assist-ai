"""Casos de borda apontados na revisão: entradas exóticas, arquivos ruins e registro do histórico."""

import csv
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from assistente import Assistente, EntradaEncerrada  # noqa: E402
from base_conhecimento import BaseConhecimento, classificar_confianca, normalizar  # noqa: E402
from tests.perguntas_cidadao import AJUSTE, VALIDACAO  # noqa: E402

BASE_REAL = os.path.join(RAIZ, "data", "base_conhecimento.json")
REGISTRO = {
    "id": 1, "categoria": "Teste", "titulo": "Título de teste", "palavras_chave": ["um", "dois", "tres"],
    "resposta": "r", "documentos": [], "onde": "o", "fonte": "https://www.gov.br", "verificado_em": "2026-11-16",
}


def acertos(base, perguntas):
    certos, erros = 0, []
    for pergunta, esperado in perguntas:
        resultados = base.buscar(pergunta)
        pontos = resultados[0][0] if resultados else 0
        obtido = resultados[0][1].id if resultados and classificar_confianca(pontos) else None
        if obtido == esperado:
            certos += 1
        else:
            erros.append((pergunta, esperado, obtido))
    return certos, erros


class TestBateriaDePerguntas(unittest.TestCase):
    """Mede o acerto da busca em perguntas coloquiais (meta: 90% ou mais)."""

    def setUp(self):
        self.base = BaseConhecimento(BASE_REAL)
        self.base.carregar()

    def test_acerto_minimo(self):
        perguntas = AJUSTE + VALIDACAO
        certos, erros = acertos(self.base, perguntas)
        taxa = certos / len(perguntas)
        self.assertGreaterEqual(taxa, 0.90, f"acerto {certos}/{len(perguntas)}; erros: {erros}")

    def test_fora_do_escopo(self):
        for pergunta, esperado in AJUSTE + VALIDACAO:
            if esperado is None:
                resultados = self.base.buscar(pergunta)
                pontos = resultados[0][0] if resultados else 0
                self.assertIsNone(classificar_confianca(pontos), pergunta)


class TestNormalizacao(unittest.TestCase):

    def test_pontuacao_unicode_e_emoji(self):
        self.assertEqual(normalizar("domingo👍… ônibus!"), " domingo onibus ")

    def test_acento_fora_do_dicionario(self):
        self.assertEqual(normalizar("Müller"), " muller ")

    def test_palavras_comuns_nao_pontuam_no_titulo(self):
        base = BaseConhecimento(BASE_REAL)
        base.carregar()
        orientacao = [o for o in base.orientacoes if o.id == 10][0]
        self.assertEqual(base.pontuar("como para", orientacao), 0)


class TestArquivos(unittest.TestCase):

    def setUp(self):
        self.pasta = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.pasta)

    def caminho(self, nome):
        return os.path.join(self.pasta, nome)

    def test_base_fora_de_utf8(self):
        with open(self.caminho("b.json"), "w", encoding="latin-1") as arquivo:
            json.dump([dict(REGISTRO, titulo="Ônibus")], arquivo, ensure_ascii=False)
        base = BaseConhecimento(self.caminho("b.json"))
        self.assertFalse(base.carregar())
        self.assertIn("corrompido", base.erro)

    def test_tipos_errados_sao_ignorados(self):
        ruins = [
            dict(REGISTRO, id="5"), dict(REGISTRO, id=True), dict(REGISTRO, titulo=None),
            dict(REGISTRO, categoria=None), dict(REGISTRO, palavras_chave="sus"),
            dict(REGISTRO, palavras_chave=[1, 2, 3]), dict(REGISTRO, documentos=None), "texto solto",
        ]
        bom = dict(REGISTRO, id=2)
        with open(self.caminho("b.json"), "w", encoding="utf-8") as arquivo:
            json.dump(ruins + [bom, dict(bom)], arquivo)   # o último repete o id 2
        base = BaseConhecimento(self.caminho("b.json"))
        self.assertTrue(base.carregar())
        self.assertEqual([o.id for o in base.orientacoes], [2])
        self.assertIn("9 orientação(ões)", base.erro)
        base.categorias()
        base.por_categoria("Teste")
        base.buscar("um dois")

    def test_historico_com_itens_invalidos(self):
        with open(self.caminho("h.json"), "w", encoding="utf-8") as arquivo:
            json.dump([1, "x", None, {"pergunta": "ok", "encontrou": True, "ajudou": True}], arquivo)
        assistente = Assistente("t", BaseConhecimento(BASE_REAL), self.caminho("h.json"), self.caminho("a.csv"))
        self.assertEqual(len(assistente.historico), 1)
        assistente.indicadores()
        assistente.registrar_nota(3)

    def test_historico_corrompido_e_guardado(self):
        with open(self.caminho("h.json"), "w", encoding="utf-8") as arquivo:
            arquivo.write('[{"pergunta": "dado do teste",}]')
        assistente = Assistente("t", BaseConhecimento(BASE_REAL), self.caminho("h.json"), self.caminho("a.csv"))
        self.assertEqual(assistente.historico, [])
        copias = [n for n in os.listdir(self.pasta) if ".corrompido-" in n]
        self.assertEqual(len(copias), 1)
        with open(self.caminho(copias[0]), encoding="utf-8") as arquivo:
            self.assertIn("dado do teste", arquivo.read())
        self.assertIsNotNone(assistente.aviso_historico)

    def test_csv_abre_no_excel_com_acentos(self):
        assistente = Assistente("t", BaseConhecimento(BASE_REAL), self.caminho("h.json"), self.caminho("a.csv"))
        assistente.registrar("pergunta", "ônibus à noite", 17, True, True, 1, 1.0, ["madrugada?"])
        with mock.patch("builtins.print"):
            assistente.exportar_csv()
        with open(self.caminho("a.csv"), "rb") as arquivo:
            self.assertTrue(arquivo.read().startswith(b"\xef\xbb\xbf"))
        with open(self.caminho("a.csv"), encoding="utf-8-sig", newline="") as arquivo:
            linha = next(csv.DictReader(arquivo))
        self.assertEqual(linha["pergunta"], "ônibus à noite")
        self.assertEqual(linha["perguntas_sem_resultado"], "madrugada?")


class TestRegistro(unittest.TestCase):

    def setUp(self):
        self.pasta = tempfile.mkdtemp()
        base = BaseConhecimento(BASE_REAL)
        base.carregar()
        self.assistente = Assistente("t", base, os.path.join(self.pasta, "h.json"), os.path.join(self.pasta, "a.csv"))

    def tearDown(self):
        shutil.rmtree(self.pasta)

    def rodar(self, metodo, entradas):
        with mock.patch("builtins.input", side_effect=entradas), mock.patch("builtins.print"):
            metodo()

    def test_pergunta_reescrita_fica_guardada(self):
        self.rodar(self.assistente.perguntar, ["receita de bolo", "perdi meu bilhete", "s"])
        atendimento = self.assistente.historico[0]
        self.assertEqual(atendimento["perguntas_sem_resultado"], ["receita de bolo"])
        self.assertIn("receita de bolo", self.assistente.indicadores()["perguntas_reescritas"])

    def test_ctrl_d_com_resposta_na_tela_registra(self):
        with mock.patch("builtins.input", side_effect=["perdi meu bilhete", EOFError]), mock.patch("builtins.print"):
            with self.assertRaises(EntradaEncerrada):
                self.assistente.perguntar()
        self.assertEqual(len(self.assistente.historico), 1)
        self.assertTrue(self.assistente.historico[0]["encontrou"])
        self.assertIsNone(self.assistente.historico[0]["ajudou"])

    def test_ctrl_d_depois_de_nao_encontrar_registra_duvida(self):
        with mock.patch("builtins.input", side_effect=["receita de bolo", EOFError]), mock.patch("builtins.print"):
            with self.assertRaises(EntradaEncerrada):
                self.assistente.perguntar()
        self.assertFalse(self.assistente.historico[0]["encontrou"])
        self.assertIn("receita de bolo", self.assistente.indicadores()["duvidas_sem_solucao"])

    def test_zero_na_tela_sim_nao_volta(self):
        self.rodar(self.assistente.perguntar, ["perdi meu bilhete", "0"])
        self.assertIsNone(self.assistente.historico[0]["ajudou"])

    def test_navegacao_conta_uma_tentativa_por_atendimento(self):
        self.rodar(self.assistente.navegar, ["1", "1", "n", "2", "s", "0", "0"])
        self.assertEqual([a["tentativas"] for a in self.assistente.historico], [1, 1])
        self.assertIn(" > ", self.assistente.historico[0]["pergunta"])
        self.assertEqual(self.assistente.indicadores()["tentativas_media"], 1.0)


class TestProgramaReal(unittest.TestCase):

    def setUp(self):
        self.pasta = tempfile.mkdtemp()
        for nome in ("main.py", "orientacao.py", "base_conhecimento.py", "assistente.py"):
            shutil.copy(os.path.join(RAIZ, nome), self.pasta)
        os.makedirs(os.path.join(self.pasta, "data"))
        shutil.copy(BASE_REAL, os.path.join(self.pasta, "data"))

    def tearDown(self):
        shutil.rmtree(self.pasta)

    def executar(self, texto):
        return subprocess.run([sys.executable, "main.py"], cwd=self.pasta, input=texto,
                              capture_output=True, text=True, timeout=30)

    def test_digitos_unicode_no_menu(self):
        resultado = self.executar("²\n¹\n-1\n+1\n1.0\n0\n")
        self.assertNotIn("Traceback", resultado.stderr)
        self.assertEqual(resultado.returncode, 0)
        self.assertIn("Digite apenas o número", resultado.stdout)

    def test_sair_sem_atendimento_nao_pede_nota(self):
        resultado = self.executar("0\n")
        self.assertEqual(resultado.returncode, 0)
        self.assertIn("Nenhum atendimento nesta sessão", resultado.stdout)

    def test_nome_do_assistente_aparece(self):
        resultado = self.executar("0\n")
        self.assertIn("Eu sou o Citizen Assist AI Mobilidade", resultado.stdout)


if __name__ == "__main__":
    unittest.main()
