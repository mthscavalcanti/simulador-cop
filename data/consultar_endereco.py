"""
Reverse Geocoding OTIMIZADO - Processamento Paralelo com Google Maps API
VERSÃO ALTA PERFORMANCE para reduzir tempo ao máximo

- Processamento paralelo com ThreadPoolExecutor
- Batch requests quando possível
- Retry automático com backoff exponencial
- Progresso em tempo real
- Checkpoint para retomar em caso de interrupção
"""

import os
import time
import csv
import json
import traceback
import requests
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from datetime import datetime

# ---------------- CONFIG ----------------
API_KEY = os.getenv("GOOGLE_API_KEY", "AIzaSyDHIbL2fDFZ8d30eQVC28hsNisKdih9Ots")
INPUT_PATH = "lat_lon.csv"
OUTPUT_PATH = "lat_lon_enderecos.csv"
CHECKPOINT_PATH = "checkpoint_geocoding.json"

# PERFORMANCE SETTINGS
MAX_WORKERS = 50          # Número de threads paralelas (Google permite até 50 QPS padrão)
                          # Ajuste para 100+ se tiver limite maior na API
REQUEST_TIMEOUT = 10      # Timeout por request em segundos
MAX_RETRIES = 3          # Tentativas por coordenada
BATCH_SIZE = 100         # Salvar checkpoint a cada N linhas processadas

# Colunas de entrada
COL_LAT = "latitude"
COL_LON = "longitude"

# Colunas de saída
COL_FORMATTED_ADDRESS = "endereco_completo"
COL_RUA = "rua"
COL_NUMERO = "numero"
COL_BAIRRO = "bairro"
COL_CIDADE = "cidade"
COL_ESTADO = "estado"
COL_CEP = "cep"
COL_PAIS = "pais"
COL_PLACE_ID = "place_id"
COL_GEOCODER = "geocoder_usado"

# Google Reverse Geocoding
GOOGLE_REVERSE_URL = "https://maps.googleapis.com/maps/api/geocode/json"

# Controle de progresso (thread-safe)
progress_lock = Lock()
processed_count = 0
success_count = 0
failed_count = 0
start_time = None
# ------------------------------------------------------------------------

def convert_comma_to_dot(value):
    """Converte vírgula decimal para ponto"""
    if pd.isna(value):
        return None
    str_value = str(value).strip()
    if not str_value:
        return None
    str_value = str_value.replace(",", ".")
    try:
        return float(str_value)
    except ValueError:
        return None

def parse_google_result(result):
    """Extrai componentes do endereço do resultado do Google"""
    address_info = {
        "formatted_address": result.get("formatted_address", ""),
        "place_id": result.get("place_id", ""),
        "rua": "",
        "numero": "",
        "bairro": "",
        "cidade": "",
        "estado": "",
        "cep": "",
        "pais": ""
    }
    
    components = result.get("address_components", [])
    
    for comp in components:
        types = comp.get("types", [])
        long_name = comp.get("long_name", "")
        short_name = comp.get("short_name", "")
        
        if "street_number" in types:
            address_info["numero"] = long_name
        elif "route" in types:
            address_info["rua"] = long_name
        elif "sublocality" in types or "sublocality_level_1" in types:
            address_info["bairro"] = long_name
        elif "administrative_area_level_2" in types:
            if not address_info["cidade"]:
                address_info["cidade"] = long_name
        elif "administrative_area_level_1" in types:
            address_info["estado"] = short_name
        elif "postal_code" in types:
            address_info["cep"] = long_name
        elif "country" in types:
            address_info["pais"] = long_name
    
    return address_info

def reverse_geocode_google_fast(lat, lon, api_key, session=None):
    """
    Reverse geocoding otimizado via Google Maps API
    Retorna: dict com informações de endereço ou None
    """
    if lat is None or lon is None:
        return None
    
    s = session or requests
    latlng = f"{lat},{lon}"
    
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            params = {
                "latlng": latlng, 
                "key": api_key, 
                "language": "pt-BR",
                "result_type": "street_address|route|premise"  # Filtrar tipos relevantes
            }
            r = s.get(GOOGLE_REVERSE_URL, params=params, timeout=REQUEST_TIMEOUT)
            data = r.json()
            
            status = data.get("status")
            if status == "OK":
                results = data.get("results", [])
                if results:
                    return parse_google_result(results[0])
                return None
            
            # Retry em erros temporários
            if status in ("OVER_QUERY_LIMIT", "RESOURCE_EXHAUSTED", "UNKNOWN_ERROR"):
                if attempt < MAX_RETRIES:
                    time.sleep(0.5 * (2 ** attempt))  # Backoff exponencial
                    continue
            
            return None
            
        except requests.exceptions.Timeout:
            if attempt < MAX_RETRIES:
                continue
            return None
        except Exception as e:
            if attempt < MAX_RETRIES:
                time.sleep(0.2)
                continue
            return None
    
    return None

def process_single_row(idx, row_data, api_key, session):
    """Processa uma única linha (para execução paralela)"""
    global processed_count, success_count, failed_count
    
    lat_str, lon_str = row_data
    lat = convert_comma_to_dot(lat_str)
    lon = convert_comma_to_dot(lon_str)
    
    result = {
        "idx": idx,
        "success": False,
        "address_info": None
    }
    
    if lat is None or lon is None:
        return result
    
    # Validação de range (Brasil aproximado)
    if not (-34 <= lat <= 5) or not (-74 <= lon <= -30):
        return result
    
    address_info = reverse_geocode_google_fast(lat, lon, api_key, session=session)
    
    with progress_lock:
        processed_count += 1
        if address_info:
            success_count += 1
            result["success"] = True
            result["address_info"] = address_info
        else:
            failed_count += 1
        
        # Mostrar progresso a cada 100 linhas ou múltiplos de 1000
        if processed_count % 100 == 0:
            elapsed = time.time() - start_time
            rate = processed_count / elapsed if elapsed > 0 else 0
            eta_seconds = (len(row_data_list) - processed_count) / rate if rate > 0 else 0
            eta_minutes = eta_seconds / 60
            
            print(f"[{processed_count}/{len(row_data_list)}] "
                  f"✅ {success_count} | ❌ {failed_count} | "
                  f"⚡ {rate:.1f} req/s | "
                  f"⏱️  ETA: {eta_minutes:.1f}min")
    
    return result

def save_checkpoint(results_dict, checkpoint_path):
    """Salva checkpoint do progresso"""
    with open(checkpoint_path, 'w', encoding='utf-8') as f:
        json.dump(results_dict, f, ensure_ascii=False)

def load_checkpoint(checkpoint_path):
    """Carrega checkpoint se existir"""
    if os.path.exists(checkpoint_path):
        with open(checkpoint_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def detect_delimiter_and_encoding(path, sample_bytes=8192):
    with open(path, "rb") as f:
        sample_bytes_data = f.read(sample_bytes)
    for enc in ("utf-8-sig", "utf-8", "latin1", "cp1252"):
        try:
            sample = sample_bytes_data.decode(enc)
        except Exception:
            continue
        try:
            dialect = csv.Sniffer().sniff(sample)
            return dialect.delimiter, enc
        except Exception:
            if sample.count(";") > sample.count(","):
                return ";", enc
            if "," in sample:
                return ",", enc
    return ",", "utf-8"

def process_csv_parallel(input_path, output_path, api_key, checkpoint_path):
    global processed_count, success_count, failed_count, start_time, row_data_list
    
    if not api_key:
        raise ValueError("❌ Google API Key é obrigatória! Configure: export GOOGLE_API_KEY='sua_chave'")
    
    print(f"\n{'='*80}")
    print(f"🚀 REVERSE GEOCODING - MODO ALTA PERFORMANCE")
    print(f"{'='*80}")
    
    # Ler CSV
    delimiter, encoding = detect_delimiter_and_encoding(input_path)
    print(f"✓ Delimiter: {repr(delimiter)}, Encoding: {encoding}")
    
    df = pd.read_csv(input_path, dtype=str, sep=delimiter, keep_default_na=False,
                     na_values=[""], encoding=encoding, engine="python")
    
    print(f"✓ Total de linhas: {len(df):,}")
    
    # Validar colunas
    if COL_LAT not in df.columns or COL_LON not in df.columns:
        raise ValueError(f"❌ Colunas {COL_LAT} e/ou {COL_LON} não encontradas")
    
    # Preparar dados para processamento
    row_data_list = [(idx, (row[COL_LAT], row[COL_LON])) for idx, row in df.iterrows()]
    
    # Carregar checkpoint se existir
    results_dict = load_checkpoint(checkpoint_path)
    if results_dict:
        print(f"✓ Checkpoint encontrado com {len(results_dict)} linhas já processadas")
        # Filtrar apenas linhas não processadas
        row_data_list = [(idx, data) for idx, data in row_data_list if str(idx) not in results_dict]
        print(f"✓ Restam {len(row_data_list)} linhas para processar")
    
    if not row_data_list:
        print("✅ Todas as linhas já foram processadas!")
    else:
        print(f"\n{'='*80}")
        print(f"⚙️  CONFIGURAÇÕES DE PERFORMANCE:")
        print(f"   • Threads paralelas: {MAX_WORKERS}")
        print(f"   • Timeout por request: {REQUEST_TIMEOUT}s")
        print(f"   • Max retries: {MAX_RETRIES}")
        print(f"   • Checkpoint a cada: {BATCH_SIZE} linhas")
        print(f"{'='*80}\n")
        
        # Resetar contadores
        processed_count = 0
        success_count = 0
        failed_count = 0
        start_time = time.time()
        
        print(f"🏁 Iniciando processamento paralelo...\n")
        
        # Criar sessão por thread (mais eficiente)
        session = requests.Session()
        
        # Processar em paralelo
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {
                executor.submit(process_single_row, idx, data, api_key, session): idx
                for idx, data in row_data_list
            }
            
            batch_count = 0
            for future in as_completed(futures):
                try:
                    result = future.result()
                    results_dict[str(result["idx"])] = result
                    
                    batch_count += 1
                    # Salvar checkpoint periodicamente
                    if batch_count % BATCH_SIZE == 0:
                        save_checkpoint(results_dict, checkpoint_path)
                
                except Exception as e:
                    idx = futures[future]
                    print(f"❌ Erro ao processar linha {idx}: {e}")
        
        # Salvar checkpoint final
        save_checkpoint(results_dict, checkpoint_path)
        
        elapsed = time.time() - start_time
        print(f"\n{'='*80}")
        print(f"⏱️  Tempo total: {elapsed/60:.2f} minutos ({elapsed:.0f}s)")
        print(f"⚡ Taxa média: {processed_count/elapsed:.1f} requests/segundo")
        print(f"{'='*80}\n")
    
    # Montar DataFrame final
    print("📝 Montando DataFrame final...")
    
    for col in [COL_FORMATTED_ADDRESS, COL_RUA, COL_NUMERO, COL_BAIRRO,
                COL_CIDADE, COL_ESTADO, COL_CEP, COL_PAIS, COL_PLACE_ID, COL_GEOCODER]:
        if col not in df.columns:
            df[col] = ""
    
    for idx_str, result in results_dict.items():
        idx = int(idx_str)
        if result["success"] and result["address_info"]:
            addr = result["address_info"]
            df.at[idx, COL_FORMATTED_ADDRESS] = addr.get("formatted_address", "")
            df.at[idx, COL_RUA] = addr.get("rua", "")
            df.at[idx, COL_NUMERO] = addr.get("numero", "")
            df.at[idx, COL_BAIRRO] = addr.get("bairro", "")
            df.at[idx, COL_CIDADE] = addr.get("cidade", "")
            df.at[idx, COL_ESTADO] = addr.get("estado", "")
            df.at[idx, COL_CEP] = addr.get("cep", "")
            df.at[idx, COL_PAIS] = addr.get("pais", "")
            df.at[idx, COL_PLACE_ID] = addr.get("place_id", "")
            df.at[idx, COL_GEOCODER] = "google"
        else:
            df.at[idx, COL_GEOCODER] = "failed"
    
    # Salvar resultado
    df.to_csv('lat_lon_enderecos.csv', index=False, sep=delimiter, encoding=encoding)
    
    # Estatísticas finais
    total_in_checkpoint = len(results_dict)
    total_success = sum(1 for r in results_dict.values() if r["success"])
    total_failed = total_in_checkpoint - total_success
    
    print(f"\n{'='*80}")
    print(f"📊 ESTATÍSTICAS FINAIS")
    print(f"{'='*80}")
    print(f"Total processado: {total_in_checkpoint:,}")
    print(f"✅ Sucesso: {total_success:,} ({total_success/total_in_checkpoint*100:.1f}%)")
    print(f"❌ Falhas: {total_failed:,} ({total_failed/total_in_checkpoint*100:.1f}%)")
    print(f"\n✅ Arquivo salvo em: {output_path}")
    print(f"{'='*80}\n")
    
    # Limpar checkpoint
    if os.path.exists(checkpoint_path):
        os.remove(checkpoint_path)
        print("✓ Checkpoint removido (processamento completo)\n")
    
    return output_path

if __name__ == "__main__":
    try:
        result = process_csv_parallel(INPUT_PATH, OUTPUT_PATH, API_KEY, CHECKPOINT_PATH)
        print(f"🎉 PROCESSO CONCLUÍDO COM SUCESSO!\n")
    except KeyboardInterrupt:
        print(f"\n\n⚠️  Processamento interrompido pelo usuário!")
        print(f"✓ Checkpoint salvo em: {CHECKPOINT_PATH}")
        print(f"✓ Execute novamente para continuar de onde parou.\n")
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        traceback.print_exc()