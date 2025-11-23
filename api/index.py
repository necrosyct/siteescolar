# Importa o objeto 'app' do seu arquivo principal (app.py)
from app import app

# Este arquivo é o ponto de entrada para o Vercel. 
# O Vercel espera uma variável chamada 'handler' ou simplesmente o objeto do aplicativo.
# Em Vercel, o framework Flask é detectado automaticamente se for o único arquivo Python 
# na pasta 'api' ou se 'app' for exposto.

# Se o Vercel detectar automaticamente o Flask, você não precisa fazer mais nada.
# Se precisar de um ponto de entrada explícito, pode ser:
# from app import app as handler 
# Mas geralmente basta garantir que 'app' esteja disponível.
