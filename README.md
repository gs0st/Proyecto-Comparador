# Comparador de aceleradores lineales

Flujo: **1 Modelos** (nombres, vida útil) → **2 Evaluación** (valor técnico, fuente y estado, o Importar CSV) → **3 Comparación** (resumen por categoría, costo lado a lado, tabla por criterio, informe).

## Ejecutar desde el código

```bash
pip install -r requirements.txt
python app.py
```

Requiere Python 3.10 a 3.13 (PySide6 puede no tener paquetes aún para versiones más nuevas).

## Generar el ejecutable

* **Windows:** doble clic en `build_windows.bat` → `dist\Comparador-Linac.exe` (copia también `ejemplos\` y este README).
* **Linux/macOS:** `./build.sh`.
* **Sin instalar nada:** suba la carpeta a GitHub y ejecute *Actions → Construir ejecutables → Run workflow*; descargue el artefacto de Windows.

PyInstaller no compila de un sistema a otro: el .exe se construye en Windows.

## CSV de importación

Columnas `codigo;respuesta` (opcionales `fuente;estado;observacion`; se aceptan con tilde y en mayúsculas). Separador `;` o `,`; decimal con coma o punto. Varios elementos en una respuesta: `6|10|15`. Sí/No acepta Sí/No/true/false. "Importar CSV" muestra una vista previa (reconocidas, códigos desconocidos, tipo inválido, sobrescrituras) y solo aplica al pulsar **Aplicar**. En `ejemplos/` hay dos CSV y un estudio de muestra.

## Archivos editables

* `criterios.json`: criterios, tipo, dirección, tolerancias.
* `relevancia.json`: reglas de "Resaltar relevancia" (nivel, técnicas, pacientes/día). Son un punto de partida: revíselas con el físico médico.
* `catalogos.json`: opciones de los criterios de selección múltiple con casillas (hoy E-036 y E-037).

## Cómo se lee la comparación

* Diferencia = Modelo B − Modelo A. Favorable = celda con color y borde + texto de Lectura; dentro de la banda de empate se muestra "Igual"; rayado = sin dato.
* Los criterios descriptivos o sin dirección no se cuentan como favorables; los costos no suman a ningún puntaje.
* Costo: Compra = C-048+049+050+051+053; Obra civil y blindaje = C-052; Servicio = C-055 × vida útil. Si falta algún componente se marca "parcial" y no se señala el menor.
* Habilitante C-058: cumple si ≥ 95 % de disponibilidad.

## Pruebas

```bash
python tests/run_tests.py
```
