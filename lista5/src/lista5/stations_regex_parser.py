import csv
import re


def extract_dates(data):
    pattern = re.compile(r"\d{4}-\d{2}-\d{2}")
    results = []
    
    for row in data:
        for column in ["Data uruchomienia", "Data zamknięcia"]:
            value = row.get(column, "")
            if value:
                matches = pattern.findall(value)
                results.extend(matches)

    return results

def extract_lon_lat(data):
    pattern = re.compile(r"\d{1,3}\.\d{6}")
    results = []

    for row in data:
        for column in ["WGS84 φ N", "WGS84 λ E"]:
            value = row.get(column, "")
            if value:
                matches = pattern.findall(value)
                results.extend(matches)

    return results

def extract_two_segment_names(data):
    pattern = re.compile(r"^[^-]+-[^-]+$")
    results = []

    for row in data:
        value = row.get("Nazwa stacji", row.get("Miejscowość", ""))
        if pattern.fullmatch(value):
            results.append(value)

    return results

def clean_station_names_and_save(data, output_filepath):
    if not data:
        return

    diacritics_map = {
        'ą': 'a', 'ć': 'c', 'ę': 'e', 'ł': 'l', 'ń': 'n', 'ó': 'o', 'ś': 's', 'ź': 'z', 'ż': 'z',
        'Ą': 'A', 'Ć': 'C', 'Ę': 'E', 'Ł': 'L', 'Ń': 'N', 'Ó': 'O', 'Ś': 'S', 'Ź': 'Z', 'Ż': 'Z'
    }
    
    fieldnames = data[0].keys()
    
    with open(output_filepath, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for row in data:
            name = row.get("Nazwa stacji", "")
            if name:
                name = name.replace(" ", "_") # spaces
                for pol, lat in diacritics_map.items(): #utf-8 chars
                    name = name.replace(pol, lat)
                
                row["Nazwa stacji"] = name
            
            writer.writerow(row)
    print(f"Saved cleared data into: {output_filepath}")

def verify_mob_stations(data):
    pattern = re.compile(r".*MOB$")
    results = []
    
    for row in data:
        kod = row.get("Kod stacji", "")
        if pattern.fullmatch(kod):
            rodzaj = row.get("Rodzaj stacji", "").lower()
            is_mobile = "mobilna" in rodzaj
            results.append({"kod": kod, "rodzaj": rodzaj, "prawidlowa": is_mobile})
            
    return results

def extract_three_segment_locations(data):
    pattern = re.compile(r"^[^-]+-[^-]+-[^-]+$")
    results = []

    for row in data:
        value = row.get("Nazwa stacji", "")
        if pattern.fullmatch(value):
            results.append(value)

    return results

def extract_comma_street_locations(data):
    pattern = re.compile(r".*,.*\b(ul\.|al\.).*")
    results = []

    for row in data:
        value = row.get("Nazwa stacji", "")
        if pattern.fullmatch(value):
            results.append(value)

    return results

def load_csv(filename):
    with open(filename, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def analyze_stations(filepath):
    stations = load_csv(filepath)
    
    print("Daty:")
    print(extract_dates(stations)[:5], "...\n")
    
    print("Szerokość i długość:")
    print(extract_lon_lat(stations)[:5], "...\n")
    
    print("Stacje dwuczłonowe:")
    print(extract_two_segment_names(stations)[:5], "...\n")
    
    print("Weryfikacja 'MOB':")
    mob_verification = verify_mob_stations(stations)
    for stat in mob_verification:
        status = "OK" if stat["prawidlowa"] else "BŁĄD"
        if status == "BŁĄD":
            print(f"Stacja: {stat['kod']} | Zapisany rodzaj: {stat['rodzaj']} | Weryfikacja: {status}")
        
    print()
    
    print("Stacje trzyczłonowe")
    print(extract_three_segment_locations(stations)[:5], "...\n")
    
    print("Przecinek + ul./al.")
    print(extract_comma_street_locations(stations)[:5], "...\n")

    print("Generowanie czystego pliku")
    # create new file with prefix "cleaned_"
    clean_station_names_and_save(stations, "cleaned_stacje.csv")

if __name__ == "__main__":
    analyze_stations("data/stacje.csv")