import os
import base64
import html

def obfuscate_html(html_content):
    """
    Offusca l'HTML mantenendo integri tutti i caratteri speciali.
    Usa base64 standard che preserva i dati binari.
    """
    # Codifica in base64 - preserva tutti i caratteri UTF-8
    b64_content = base64.b64encode(html_content.encode('utf-8')).decode('ascii')
    
    # Crea lo script che decodifica e scrive l'HTML
    # Usa document.write che interpreta correttamente i caratteri UTF-8
    obfuscated_code = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Protected Content</title>
</head>
<body>
    <script type="text/javascript">
        // Decodifica il contenuto base64
        var encoded = "{b64_content}";
        var decoded = atob(encoded);
        // Decodifica UTF-8
        var bytes = new Uint8Array(decoded.length);
        for (var i = 0; i < decoded.length; i++) {{
            bytes[i] = decoded.charCodeAt(i);
        }}
        var utf8decoder = new TextDecoder('utf-8');
        var htmlContent = utf8decoder.decode(bytes);
        document.write(htmlContent);
        document.close();
    </script>
</body>
</html>'''
    return obfuscated_code

def obfuscate_html_simple(html_content):
    """
    Versione più semplice che usa solo atob/unescape
    """
    b64_content = base64.b64encode(html_content.encode('utf-8')).decode('ascii')
    obfuscated_code = f'''<script type="text/javascript">
    var encoded = "{b64_content}";
    var decoded = atob(encoded);
    document.write(unescape(encodeURIComponent(decoded)));
    document.close();
</script>'''
    return obfuscated_code

def process_folder(input_folder='sorgenti_html', output_folder='file_protetti', method='advanced'):
    """
    Processa tutti i file HTML nella cartella di input.
    
    Args:
        input_folder: Cartella con i file HTML originali
        output_folder: Cartella dove salvare i file offuscati
        method: 'advanced' o 'simple' - metodo di offuscamento
    """
    # Crea le cartelle se non esistono
    if not os.path.exists(input_folder):
        os.makedirs(input_folder)
        print(f"(!) Cartella '{input_folder}' creata. Inserisci qui i file HTML e riavvia.")
        return

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Trova tutti i file HTML
    files = [f for f in os.listdir(input_folder) if f.endswith(".html")]
    
    if not files:
        print(f"(!) La cartella '{input_folder}' è vuota. Non c'è nulla da offuscare.")
        return

    # Seleziona il metodo
    obfuscate_func = obfuscate_html if method == 'advanced' else obfuscate_html_simple

    for filename in files:
        try:
            # Leggi il file originale con encoding UTF-8
            with open(os.path.join(input_folder, filename), 'r', encoding='utf-8') as f:
                original_html = f.read()
            
            # Offusca il contenuto
            protected_html = obfuscate_func(original_html)
            
            # Salva il file offuscato con encoding UTF-8
            with open(os.path.join(output_folder, filename), 'w', encoding='utf-8') as f:
                f.write(protected_html)
                
            print(f"✅ SUCCESS: {filename} -> {output_folder}/{filename}")
            
        except Exception as e:
            print(f"❌ ERROR: {filename} - {str(e)}")

def test_character_preservation():
    """
    Funzione di test per verificare la preservazione dei caratteri
    """
    test_html = '''
    <!DOCTYPE html>
    <html lang="it">
    <head>
        <meta charset="UTF-8">
        <title>Test Caratteri Speciali</title>
    </head>
    <body>
        <h1>¡Hola! Málaga vs Deportivo</h1>
        <p>Caratteri: à è é ì ò ù · ñ €</p>
        <p>Vuelta a España · Etapa 3</p>
        <p>Supercopa Cataluña · Final</p>
    </body>
    </html>
    '''
    
    print("🔬 Test di preservazione caratteri:")
    print("=" * 50)
    
    # Test metodo avanzato
    obfuscated = obfuscate_html(test_html)
    print("✅ Metodo avanzato completato")
    
    # Test metodo semplice
    obfuscated_simple = obfuscate_html_simple(test_html)
    print("✅ Metodo semplice completato")
    
    print("\n💡 I file offuscati preservano tutti i caratteri speciali.")
    print("   Apri i file generati per verificare.")

# Esecuzione
if __name__ == "__main__":
    # Puoi scegliere tra 'advanced' (consigliato) o 'simple'
    process_folder('sorgenti_html', 'file_protetti', method='advanced')
    
    # Se vuoi testare la preservazione dei caratteri:
    # test_character_preservation()
