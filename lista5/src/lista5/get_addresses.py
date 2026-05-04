import csv
import re


# returns (województwo, miasto, ulica, opcjonalnie: numer)
def get_addresses(filepath, city) -> list[tuple[str,str,str,int | None]]:
    file = open(filepath, "r")
    reader = csv.reader(file)
    
    result = []
    
    headers = next(reader, [])
    
    wojewodztwo_idx = headers.index("Województwo")
    miasto_idx = headers.index("Miejscowość")
    ulica_idx = headers.index("Adres")
    
    for row in reader:
        if not row:
            continue
        
        if row[miasto_idx] == city:
            wojewodztwo = row[wojewodztwo_idx]
            miasto = row[miasto_idx]
            adres_pelny = row[ulica_idx].strip()
            
            # Wyszukujemy ulicę oraz opcjonalny numer na końcu adresu
            # ^ - poczatek stringa
            # (.*?) - dowolne znaki dopasowywane non-greedy (czyli jak najkrótszy możliwy ciąg znaków)
            # \s+ - co najmniej jedna spacja
            # (\d+) - jedna lub więcej cyfr (numer domu)
            # $ - koniec stringa
            match = re.search(r"^(.*?)\s+(\d+)$", adres_pelny) 
            if match:
                ulica = match.group(1).strip()
                numer = int(match.group(2))
            else:
                ulica = adres_pelny
                numer = None
            
            result.append((wojewodztwo, miasto, ulica, numer))

    file.close()
    return result