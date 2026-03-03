"""Constantes de estilo e cores do relatório Somus Capital."""

# Cores RGB (para FPDF)
VERDE_ESCURO = (0, 77, 51)       # #004d33
AZUL = (24, 99, 220)             # #1863DC
TEXTO = (33, 33, 33)             # #212121
FUNDO_CLARO = (244, 244, 244)    # #F4F4F4
BRANCO = (255, 255, 255)
CINZA_MEDIO = (160, 160, 160)
VERDE_CLARO = (0, 128, 85)       # variante mais clara

# Cores para matplotlib (hex)
MPL_VERDE = "#004d33"
MPL_AZUL = "#1863DC"
MPL_VERDE_CLARO = "#008055"
MPL_CINZA = "#A0A0A0"
MPL_FUNDO = "#F4F4F4"

# Paleta de cores para gráficos (10 cores)
CHART_PALETTE = [
    "#004d33", "#1863DC", "#008055", "#2E86C1", "#1ABC9C",
    "#F39C12", "#E74C3C", "#9B59B6", "#34495E", "#95A5A6",
]

# Fontes (FPDF built-in)
FONT_TITLE = "Helvetica"
FONT_BODY = "Helvetica"

# Tamanhos de fonte
SIZE_TITLE = 24
SIZE_SUBTITLE = 16
SIZE_SECTION = 14
SIZE_BODY = 10
SIZE_SMALL = 8
SIZE_TINY = 7

# Margens e espaçamento
MARGIN_LEFT = 15
MARGIN_RIGHT = 15
MARGIN_TOP = 15
PAGE_WIDTH = 210  # A4
CONTENT_WIDTH = PAGE_WIDTH - MARGIN_LEFT - MARGIN_RIGHT
