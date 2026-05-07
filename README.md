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

## Baza danych

Aplikacja korzysta z lokalnej bazy SQLite tworzonej automatycznie w folderze:

```text
data/app.db
```

## Uwagi projektowe

Aplikacja ma charakter edukacyjny i prototypowy. Nie łączy się z rachunkiem maklerskim, nie wykonuje rzeczywistych transakcji giełdowych i nie stanowi rekomendacji inwestycyjnej.
