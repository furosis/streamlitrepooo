# Aplikacja wspomagająca inwestycje giełdowe

Projekt wykonany jako prototyp aplikacji webowej zgodnej ze specyfikacją SRS pod technologię **Python + Streamlit + SQLite**.

## Funkcje

- Rejestracja i logowanie użytkownika
- Zmiana nazwy użytkownika i hasła
- Dodawanie, edycja i usuwanie transakcji kupna/sprzedaży
- Przegląd portfela inwestycyjnego
- Obliczanie średniej ceny zakupu
- Obliczanie wartości pozycji, zysku/straty i stopy zwrotu
- Dodawanie danych historycznych ręcznie
- Import danych historycznych z CSV
- Generator przykładowych danych historycznych do testów
- Wykresy kursów i portfela
- Generowanie raportów inwestycyjnych
- Historia raportów
- Eksport transakcji, danych i raportów

## Technologie

- Python
- Streamlit
- SQLite
- pandas
- numpy
- Plotly

## Instalacja

1. Rozpakuj projekt.
2. Wejdź do folderu projektu:

```bash
cd aplikacja_inwestycje_streamlit
```

3. Utwórz środowisko wirtualne, opcjonalnie:

```bash
python -m venv .venv
```

4. Aktywuj środowisko:

Windows:

```bash
.venv\Scripts\activate
```

macOS/Linux:

```bash
source .venv/bin/activate
```

5. Zainstaluj wymagane biblioteki:

```bash
pip install -r requirements.txt
```

6. Uruchom aplikację:

```bash
streamlit run app.py
```

Po uruchomieniu aplikacja otworzy się w przeglądarce.

## Dane historyczne CSV

Plik CSV do importu powinien mieć kolumny:

```csv
price_date,close_price
2026-03-01,100.25
2026-03-02,101.40
```

## Baza danych

Aplikacja korzysta z lokalnej bazy SQLite tworzonej automatycznie w folderze:

```text
data/app.db
```

## Uwagi projektowe

Aplikacja ma charakter edukacyjny i prototypowy. Nie łączy się z rachunkiem maklerskim, nie wykonuje rzeczywistych transakcji giełdowych i nie stanowi rekomendacji inwestycyjnej.
