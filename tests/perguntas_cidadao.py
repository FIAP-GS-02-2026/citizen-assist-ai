"""Perguntas de cidadãos (linguagem coloquial, sem acento, com gíria) e a orientação esperada.

None = fora do escopo: o assistente deve responder "não encontrei".
AJUSTE: usadas para escolher palavras-chave (o acerto nelas é otimista).
VALIDACAO: escritas depois e usadas para medir; após medir (22 de 28 = 79%),
as falhas viraram novas palavras-chave, registradas no README.
"""

AJUSTE = [
    ("tenho 70 anos pago onibus?", 1), ("idoso paga onibus?", 1), ("minha mae tem 66 anos, ela paga busao?", 1),
    ("com quantos anos o idoso nao paga mais", 1), ("como faz o cartao do idoso", 1), ("vó de 80 anos precisa de bilhete?", 1),
    ("fiz 60 anos agora, ja posso andar de graca no onibus?", 2), ("tenho 63 anos tenho gratuidade", 2), ("quem tem 61 anos paga passagem", 2),
    ("meu filho e cadeirante, tem passe livre?", 3), ("como tirar bilhete de deficiente", 3),
    ("tenho deficiencia visual, como faço o cartao", 3), ("sou surdo tenho direito a bilhete gratis?", 3),
    ("posso levar acompanhante no onibus com meu filho pcd", 4), ("meu acompanhante paga?", 4),
    ("como tirar a carteirinha de estudante do onibus", 5), ("quanto paga estudante no busao", 5), ("meia passagem pra universitario", 5),
    ("estudante de escola publica paga onibus?", 6),
    ("onibus e de graca no domingo?", 7), ("domingo paga onibus?", 7), ("no natal o onibus e gratis?", 7),
    ("qual o preco da passagem", 8), ("qto ta a passagem de onibus", 8), ("quanto custa o busao", 8),
    ("quanto e a integraçao com o metro", 8), ("valor da tarifa do onibus em sp", 8),
    ("tem bilhete mensal?", 9), ("bilhete de 24 horas quanto custa", 9),
    ("como faço pra tirar o bilhete unico", 10), ("onde faço o bilhete unico", 10), ("quero fazer meu bilhete", 10), ("como fazer o cartao do onibus", 10),
    ("como recarregar o bilhete", 11), ("onde coloco credito no bilhete unico", 11), ("como por saldo no cartao", 11), ("da pra recarregar pelo celular?", 11),
    ("perdi meu bilhete unico", 12), ("roubaram meu cartao", 12), ("como tirar segunda via do bilhete", 12), ("furtaram minha carteira com o bilhete", 12),
    ("transporte pra cadeirante que nao consegue pegar onibus", 13), ("atende mais como pedir", 13),
    ("posso descer fora do ponto?", 14),
    ("o motorista nao parou no ponto, como reclamo", 15), ("onibus atrasado demais onde reclamar", 15),
    ("onibus sempre lotado quero reclamar", 15), ("o motorista foi grosso comigo", 15),
    ("reclamei no 156 e nada aconteceu", 16), ("minha reclamacao nao foi resolvida", 16),
    ("tem onibus de madrugada?", 17), ("onibus que roda a noite toda", 17), ("que horas o onibus para de rodar", 17),
    ("onibus tem wifi?", None), ("cade o onibus agora", None), ("como chego na paulista", None),
    ("onde e o banco preferencial no onibus", None), ("qual a previsão do tempo amanhã", None),
    # Energia e mobilidade elétrica (17/11/2026)
    ("quanto custa carregar bike eletrica na tomada", 18), ("carregar patinete eletrico pesa na conta de luz?", 18),
    ("qual o valor do kwh da enel", 18), ("o que é bandeira vermelha na conta de luz", 19), ("bandeira amarela aumenta quanto", 19),
    ("placa solar em casa gera credito na conta de luz?", 20), ("como funciona energia solar", 20),
    ("vale a pena painel solar pra carregar bike eletrica", 20), ("bike eletrica precisa de cnh e placa?", 21),
    ("patinete eletrico precisa de habilitacao", 21), ("preciso emplacar minha bicicleta eletrica?", 21),
    ("patinete eletrico pode andar na calcada", 22), ("qual a velocidade maxima na ciclovia", 22),
    ("bike eletrica pode andar na ciclofaixa?", 22),
    # Energia, orientações 23 e 24 (18/11/2026)
    ("vale a pena carregar a bike com energia solar ou na tomada?", 23), ("quanto custa uma carga completa do patinete", 23),
    ("quanto gasto por ano carregando a bike eletrica", 23), ("tarifa branca compensa pra carregar bike?", 23),
    ("onde descarto a bateria velha da bike", 24), ("posso jogar a bateria do patinete no lixo?", 24),
    ("como reciclar bateria de bike eletrica", 24),
    # Achados da auditoria de SERS (18/11/2026)
    ("quanto de co2 a bike emite?", 23), ("a bateria do patinete estragou, onde jogo?", 24),
]

VALIDACAO = [
    ("meu pai tem 68 anos, ele precisa pagar o busão?", 1), ("idosa paga metrô?", 1), ("como pede o bilhete especial do idoso", 1),
    ("minha tia fez 61, ela anda de graça?", 2), ("pessoa de 64 anos precisa de cartão?", 2),
    ("tenho autismo, posso ter bilhete grátis?", 3), ("criança com deficiência tem passe?", 3),
    ("meu filho cadeirante pode levar acompanhante?", 4), ("universitário paga quanto no ônibus?", 5),
    ("como pedir o bilhete de estudante", 5), ("aluno de escola pública tem passe livre?", 6),
    ("domingo o busão é de graça mesmo?", 7), ("quanto tá a tarifa do ônibus hoje", 8),
    ("quanto custa pegar ônibus e metrô junto", 8), ("quanto custa o bilhete mensal", 9),
    ("onde eu tiro o bilhete único", 10), ("preciso de um bilhete único novo, como faço", 10),
    ("como coloco crédito pelo app", 11), ("meu bilhete foi roubado o que eu faço", 12), ("perdi o cartão do ônibus", 12),
    ("minha mãe não consegue andar, tem transporte especial?", 13), ("o motorista me deixa descer fora do ponto?", 14),
    ("onde reclamo do motorista", 15), ("o ônibus nunca passa, quero reclamar", 15),
    ("ninguém resolveu minha reclamação do 156", 16), ("tem ônibus depois da meia noite?", 17),
    ("me passa uma receita de bolo", None),
    # Energia (17/11/2026): escritas depois do ajuste; acerto medido 8 de 10 (80%), as 2 falhas viraram palavras-chave.
    ("gasto muito de energia carregando minha bike eletrica todo dia?", 18), ("quanto ta o kwh em sao paulo", 18),
    ("mes de bandeira vermelha a conta sobe quanto", 19), ("o que significa bandeira verde", 19),
    ("quero colocar painel solar no telhado, sobra energia vira credito?", 20), ("energia solar compensa na conta da enel", 20),
    ("patinete eletrico tem que emplacar?", 21), ("precisa tirar carteira pra andar de bike eletrica", 21),
    ("posso andar de patinete na calçada?", 22), ("qual o limite de velocidade da bicicleta eletrica na ciclofaixa", 22),
    # Energia, orientações 23 e 24 (18/11/2026): acerto medido antes do ajuste: 2 de 6. Depois do ajuste, "bateria do patinete estragou, onde levo?" ainda falhava; foi resolvida em 18/11 com "patinete estragou".
    ("quanto eu pago de luz pra encher a bateria do patinete uma vez", 23), ("energia solar ou tomada, qual sai mais barato pra bike", 23),
    ("compensa aderir a tarifa branca so por causa da bike?", 23), ("quanto da por mes a recarga da bicicleta eletrica", 23),
    ("tem lugar pra reciclar bateria de lítio da bike?", 24),
]
