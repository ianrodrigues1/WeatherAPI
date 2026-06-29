# Weather Widget

Esta pasta e o pacote minimo para copiar e colar o widget em outro projeto.

## Uso

```html
<script src="./widget.js" data-api="https://sua-api.com"></script>

<div class="weather-widget" data-city="Lisboa"></div>
```

## Com coordenadas

```html
<script src="./widget.js" data-api="https://sua-api.com"></script>

<div
  class="weather-widget"
  data-city="Lisboa"
  data-lat="38.7077"
  data-lon="-9.1366">
</div>
```

## Opcoes

- `data-city`: nome da cidade.
- `data-lat` e `data-lon`: coordenadas para evitar ambiguidade.
- `data-api`: URL base da API Flask publicada.
- `data-theme="light"`: tema claro.
- `data-compact="true"`: mostra apenas cidade, temperatura e condicao.

O widget nao usa frameworks, nao expõe a chave da OpenWeather e renderiza com Shadow DOM para evitar conflito com CSS do site onde for colado.

`data-api` deve apontar para a URL base da API Flask publicada, sem `/api` no final.
