# 01 — Visão Geral

## Problema

Equipes universitárias de BAJA SAE e oficinas de pintura automotiva ainda
realizam a inspeção visual da pintura do chassi de forma **manual**,
dependente da experiência do operador. Esse processo é lento, subjetivo
e sujeito a falhas de detecção de defeitos sutis, o que compromete a
qualidade estética e a proteção contra corrosão.

## Solução Proposta

Uma **câmara fechada de inspeção** onde o chassi é posicionado após a
pintura. Câmeras distribuídas em ângulos complementares capturam imagens,
que são enviadas a um serviço de **Inteligência Artificial hospedado em
nuvem** para detecção automatizada, em tempo quase real, de:

- **Defeitos de pintura:** escorrimento, casca de laranja, falha de
  cobertura, bolhas.
- **Desgaste / danos:** riscos, oxidação, descascamento.

## Objetivos

### Geral

Construir um protótipo de inspeção automatizada que demonstre a
viabilidade técnica e científica do uso de visão computacional com deep
learning aplicado à inspeção de pintura em chassis de veículos de
competição.

### Específicos

1. Projetar a arquitetura do sistema (câmara física + software + IA).
2. Implementar um backend que exponha inferência de detecção de objetos
   por API REST.
3. Implementar um frontend que permita capturar imagens e visualizar
   detecções em tempo real.
4. Documentar a escolha tecnológica comparando nuvem × edge, modelos
   disponíveis e estratégia de dataset.
5. Entregar um protótipo funcional + documentação técnico-científica ao
   final do semestre.

## Público-alvo

- Equipes de competição BAJA SAE.
- Laboratórios de manufatura e pintura automotiva.
- Grupos de pesquisa em visão computacional industrial.

## Justificativa

Projetos recentes na área de *surface defect detection* mostram que
modelos baseados em CNN (em especial arquiteturas da família YOLO)
atingem mAP competitivo com inspeção humana em domínios industriais
semelhantes (aço, cerâmica, solda). A transferência desse conhecimento
ao domínio de pintura automotiva esportiva é direta e ainda pouco
explorada em trabalhos acadêmicos brasileiros, o que confere caráter
científico-tecnológico ao projeto.
