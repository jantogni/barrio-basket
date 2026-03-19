# Dashboard dinámico para encuesta de basketball

## Opción recomendada
Este proyecto está listo para correr con **Streamlit** y generar un dashboard online/local usando tu archivo Excel de respuestas.

## Cómo ejecutarlo
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Qué hace
- Lee el Excel de respuestas
- Calcula IMC
- Clasifica IMC en Bajo peso / Normal / Sobrepeso / Obesidad
- Agrupa jugadores por categoría Maxi Basket: <30, 30+, 35+, 40+, 45+, 50+
- Calcula medidas de tendencia central y dispersión
- Muestra gráficos interactivos
- Permite filtrar por categoría, posición y edad
- Permite descargar los datos procesados

## Archivo esperado
La app detecta automáticamente columnas como:
- Nombre Completo
- Edad
- Altura (cm)
- Peso (kg)
- Años jugando basketball
- Posición principal
- Posición secundaria
- Velocidad, Resistencia, Fuerza, etc.

También acepta que subas otro archivo desde la barra lateral.
