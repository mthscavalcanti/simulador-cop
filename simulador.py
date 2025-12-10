import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
import json
import math
from pathlib import Path

# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================
st.set_page_config(
    page_title="Otimizador do Videomonitoramento – Recife",
    page_icon="📍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# CAMINHOS DOS ARQUIVOS LOCAIS
# ============================================================
DATA_DIR = Path("data")
ARQUIVO_CRUZAMENTOS = DATA_DIR / "Cruzamentos.xlsx"
ARQUIVO_PRIORIDADES = DATA_DIR / "Prioridades.xlsx"
ARQUIVO_EQUIPAMENTOS = DATA_DIR / "Equipamentos.xlsx"
ARQUIVO_BAIRROS = DATA_DIR / "bairros.geojson"
ARQUIVO_ALAGAMENTOS = DATA_DIR / "Alagamentos.xlsx"
ARQUIVO_SINISTROS = DATA_DIR / "Sinistros.xlsx"

# ============================================================
# CSS CUSTOMIZADO - Layout compacto
# ============================================================
st.markdown("""
<style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
        max-width: 100%;
    }
    .main-header {
        font-size: 1.4rem;
        font-weight: 700;
        margin-bottom: 0.3rem;
    }
    [data-testid="stSidebar"] {
        min-width: 400px;
        width: 400px;
        overflow-y: auto;
    }
    [data-testid="stSidebar"] > div:first-child {
        width: 400px;
        overflow-y: auto;
        height: 100vh;
    }
    .section-title {
        font-size: 0.85rem;
        font-weight: 600;
        margin: 0.8rem 0 0.3rem 0;
        padding-bottom: 0.2rem;
        border-bottom: 1px solid rgba(148, 163, 184, 0.3);
    }
    .stat-box {
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(148, 163, 184, 0.25);
        border-radius: 8px;
        padding: 0.5rem 0.8rem;
        margin: 0.2rem 0;
        font-size: 0.8rem;
    }
    .stat-row {
        display: flex;
        justify-content: space-between;
        padding: 0.15rem 0;
    }
    .stat-value {
        color: #a5b4fc;
        font-weight: 600;
    }
    .chip {
        display: inline-block;
        background: rgba(79, 70, 229, 0.3);
        border: 1px solid rgba(129, 140, 248, 0.5);
        border-radius: 999px;
        padding: 0.1rem 0.5rem;
        font-size: 0.75rem;
        margin: 0.1rem;
    }
    .stSlider {
        padding-top: 0.2rem;
        padding-bottom: 0.2rem;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="collapsedControl"] {display: none !important;}
    [data-testid="stSidebarCollapseButton"] {display: none !important;}
    section[data-testid="stSidebar"] {
        transform: none !important;
        visibility: visible !important;
        position: relative !important;
    }
    iframe {
        border-radius: 8px;
    }
    .coverage-warning {
        background: rgba(234, 179, 8, 0.2);
        border: 1px solid rgba(234, 179, 8, 0.5);
        border-radius: 8px;
        padding: 0.5rem 0.8rem;
        margin: 0.5rem 0;
        font-size: 0.8rem;
        color: #fbbf24;
    }
    .info-box {
        background: rgba(59, 130, 246, 0.15);
        border: 1px solid rgba(59, 130, 246, 0.4);
        border-radius: 8px;
        padding: 0.5rem 0.8rem;
        margin: 0.5rem 0;
        font-size: 0.8rem;
        color: #93c5fd;
    }
    .highlight-box {
        background: rgba(34, 197, 94, 0.15);
        border: 1px solid rgba(34, 197, 94, 0.4);
        border-radius: 8px;
        padding: 0.5rem 0.8rem;
        margin: 0.5rem 0;
        font-size: 0.8rem;
        color: #86efac;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# INICIALIZAÇÃO DO SESSION STATE - AJUSTE 3 APLICADO
# ============================================================
if 'logs' not in st.session_state:
    st.session_state.logs = pd.DataFrame()
if 'cruzamentos' not in st.session_state:
    st.session_state.cruzamentos = pd.DataFrame()
if 'cruzamentos_calculados' not in st.session_state:
    st.session_state.cruzamentos_calculados = pd.DataFrame()
if 'equipamentos' not in st.session_state:
    st.session_state.equipamentos = pd.DataFrame()
# ===== AJUSTE 3: ESTADOS PARA CHECKBOXES (SIMPLIFICADO) =====
if 'mostrar_pontos_minimos' not in st.session_state:
    st.session_state.mostrar_pontos_minimos = True
if 'mostrar_pontos_ipe' not in st.session_state:
    st.session_state.mostrar_pontos_ipe = True
# ===== FIM AJUSTE 3 =====
if 'bairros_geojson' not in st.session_state:
    st.session_state.bairros_geojson = None
if 'ultimo_selecionados' not in st.session_state:
    st.session_state.ultimo_selecionados = pd.DataFrame()
if 'pontos_minimos' not in st.session_state:
    st.session_state.pontos_minimos = pd.DataFrame()
if 'alagamentos' not in st.session_state:
    st.session_state.alagamentos = pd.DataFrame()
if 'sinistros' not in st.session_state:
    st.session_state.sinistros = pd.DataFrame()
if 'arquivos_carregados' not in st.session_state:
    st.session_state.arquivos_carregados = False


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def distancia_metros(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calcula distância geodésica em metros usando fórmula de Haversine"""
    R = 6371000
    to_rad = math.pi / 180
    d_lat = (lat2 - lat1) * to_rad
    d_lon = (lon2 - lon1) * to_rad
    a = (math.sin(d_lat / 2) ** 2 +
         math.cos(lat1 * to_rad) * math.cos(lat2 * to_rad) *
         math.sin(d_lon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def verificar_alagamentos_por_raio(df_cameras: pd.DataFrame, df_alagamentos: pd.DataFrame, 
                                    raio_camera: float = 50, raio_ponto: float = 100) -> list:

    if df_cameras.empty or df_alagamentos.empty:
        return []
    
    alagamentos_cobertos = []
    raio_total = raio_camera + raio_ponto  # 150m no caso padrão
    
    for _, alag in df_alagamentos.iterrows():
        alag_lat = alag['lat']
        alag_lon = alag['lon']
        alag_nome = alag.get('nome', f"Alagamento {alag.get('id', '')}")
        
        coberto = False
        for _, cam in df_cameras.iterrows():
            cam_lat = cam['lat']
            cam_lon = cam['lon']
            
            if distancia_metros(alag_lat, alag_lon, cam_lat, cam_lon) <= raio_total:
                coberto = True
                break
        
        if coberto:
            alagamentos_cobertos.append(alag_nome)
    
    return alagamentos_cobertos


def verificar_sinistros_por_logradouro(df_cruzamentos_selecionados: pd.DataFrame, df_sinistros: pd.DataFrame) -> tuple:
    """Verifica quais logradouros com sinistros têm cobertura de câmeras"""
    if df_cruzamentos_selecionados.empty or df_sinistros.empty:
        return 0, 0, []
    
    sinistros_dict = {}
    for _, row in df_sinistros.iterrows():
        log_norm = str(row['logradouro']).strip().upper()
        qtd = int(row.get('qtd', 1))
        sinistros_dict[log_norm] = qtd
    
    logradouros_cobertos = {}
    
    for _, cruz in df_cruzamentos_selecionados.iterrows():
        log1 = str(cruz.get('log1', '')).strip().upper()
        log2 = str(cruz.get('log2', '')).strip().upper()
        
        if log1 in sinistros_dict and log1 not in logradouros_cobertos:
            logradouros_cobertos[log1] = sinistros_dict[log1]
        
        if log2 in sinistros_dict and log2 not in logradouros_cobertos:
            logradouros_cobertos[log2] = sinistros_dict[log2]
    
    qtd_sinistros_cobertos = sum(logradouros_cobertos.values())
    total_sinistros = sum(sinistros_dict.values())
    lista_logradouros = list(logradouros_cobertos.keys())
    
    return qtd_sinistros_cobertos, total_sinistros, lista_logradouros

def calcular_cobertura_por_logradouro_ajustada(df_calculados: pd.DataFrame, ids_cobertos: set, logs: pd.DataFrame) -> tuple:
    """
    Calcula cobertura por logradouro com regra de 50%:
    - Se logradouro tem >= 50% de cobertura efetiva, considera 100%
    - Se < 50%, mantém a cobertura atual
    
    Retorna: (cobertura_ajustada_total, dict_por_eixo, detalhes_logradouros)
    """
    if df_calculados.empty or logs.empty:
        return 0.0, {'seg': 0.0, 'lct': 0.0, 'com': 0.0, 'mob': 0.0, 'qtd_100': 0, 'total_logs': 0}, []
    
    logs_dict = {}
    for _, log in logs.iterrows():
        cod_log = int(log['cod_log'])
        logs_dict[cod_log] = {
            'nome': log['nome'],
            'seg': log['seg'],
            'lct': log['lct'],
            'com': log['com'],
            'mob': log['mob']
        }
    
    ipe_total_por_log = {}
    for _, cruz in df_calculados.iterrows():
        cod1, cod2 = cruz['cod_log1'], cruz['cod_log2']
        ipe = cruz['ipe_cruz']
        
        if cod1 not in ipe_total_por_log:
            ipe_total_por_log[cod1] = {'total': 0, 'seg': 0, 'lct': 0, 'com': 0, 'mob': 0}
        if cod2 not in ipe_total_por_log:
            ipe_total_por_log[cod2] = {'total': 0, 'seg': 0, 'lct': 0, 'com': 0, 'mob': 0}
        
        ipe_total_por_log[cod1]['total'] += ipe
        ipe_total_por_log[cod2]['total'] += ipe
        
        ipe_total_por_log[cod1]['seg'] += cruz['ipe_cruz_seg']
        ipe_total_por_log[cod1]['lct'] += cruz['ipe_cruz_lct']
        ipe_total_por_log[cod1]['com'] += cruz['ipe_cruz_com']
        ipe_total_por_log[cod1]['mob'] += cruz['ipe_cruz_mob']
        
        ipe_total_por_log[cod2]['seg'] += cruz['ipe_cruz_seg']
        ipe_total_por_log[cod2]['lct'] += cruz['ipe_cruz_lct']
        ipe_total_por_log[cod2]['com'] += cruz['ipe_cruz_com']
        ipe_total_por_log[cod2]['mob'] += cruz['ipe_cruz_mob']
    
    ipe_coberto_por_log = {}
    df_cobertos = df_calculados[df_calculados['id'].isin(ids_cobertos)]
    
    for _, cruz in df_cobertos.iterrows():
        cod1, cod2 = cruz['cod_log1'], cruz['cod_log2']
        ipe = cruz['ipe_cruz']
        
        if cod1 not in ipe_coberto_por_log:
            ipe_coberto_por_log[cod1] = {'total': 0, 'seg': 0, 'lct': 0, 'com': 0, 'mob': 0}
        if cod2 not in ipe_coberto_por_log:
            ipe_coberto_por_log[cod2] = {'total': 0, 'seg': 0, 'lct': 0, 'com': 0, 'mob': 0}
        
        ipe_coberto_por_log[cod1]['total'] += ipe
        ipe_coberto_por_log[cod2]['total'] += ipe
        
        ipe_coberto_por_log[cod1]['seg'] += cruz['ipe_cruz_seg']
        ipe_coberto_por_log[cod1]['lct'] += cruz['ipe_cruz_lct']
        ipe_coberto_por_log[cod1]['com'] += cruz['ipe_cruz_com']
        ipe_coberto_por_log[cod1]['mob'] += cruz['ipe_cruz_mob']
        
        ipe_coberto_por_log[cod2]['seg'] += cruz['ipe_cruz_seg']
        ipe_coberto_por_log[cod2]['lct'] += cruz['ipe_cruz_lct']
        ipe_coberto_por_log[cod2]['com'] += cruz['ipe_cruz_com']
        ipe_coberto_por_log[cod2]['mob'] += cruz['ipe_cruz_mob']
    
    ipe_ajustado_total = 0
    ipe_ajustado_seg = 0
    ipe_ajustado_lct = 0
    ipe_ajustado_com = 0
    ipe_ajustado_mob = 0
    
    ipe_total_geral = sum(v['total'] for v in ipe_total_por_log.values())
    ipe_total_seg = sum(v['seg'] for v in ipe_total_por_log.values())
    ipe_total_lct = sum(v['lct'] for v in ipe_total_por_log.values())
    ipe_total_com = sum(v['com'] for v in ipe_total_por_log.values())
    ipe_total_mob = sum(v['mob'] for v in ipe_total_por_log.values())
    
    detalhes = []
    logradouros_100 = 0
    
    for cod_log, ipe_total_dict in ipe_total_por_log.items():
        ipe_total = ipe_total_dict['total']
        ipe_coberto = ipe_coberto_por_log.get(cod_log, {'total': 0})['total']
        
        if ipe_total > 0:
            cobertura_efetiva = ipe_coberto / ipe_total
            
            if cobertura_efetiva >= 0.15:
                ipe_ajustado_total += ipe_total_dict['total']
                ipe_ajustado_seg += ipe_total_dict['seg']
                ipe_ajustado_lct += ipe_total_dict['lct']
                ipe_ajustado_com += ipe_total_dict['com']
                ipe_ajustado_mob += ipe_total_dict['mob']
                cobertura_final = 1.0
                logradouros_100 += 1
            else:
                ipe_ajustado_total += ipe_coberto
                ipe_ajustado_seg += ipe_coberto_por_log.get(cod_log, {}).get('seg', 0)
                ipe_ajustado_lct += ipe_coberto_por_log.get(cod_log, {}).get('lct', 0)
                ipe_ajustado_com += ipe_coberto_por_log.get(cod_log, {}).get('com', 0)
                ipe_ajustado_mob += ipe_coberto_por_log.get(cod_log, {}).get('mob', 0)
                cobertura_final = cobertura_efetiva
            
            nome_log = logs_dict.get(cod_log, {}).get('nome', f'Log {cod_log}')
            detalhes.append({
                'cod_log': cod_log,
                'nome': nome_log,
                'cobertura_efetiva': cobertura_efetiva,
                'cobertura_ajustada': cobertura_final,
                'ipe_total': ipe_total
            })
    
    cobertura_ajustada_total = (ipe_ajustado_total / ipe_total_geral * 100) if ipe_total_geral > 0 else 0
    cobertura_ajustada_seg = (ipe_ajustado_seg / ipe_total_seg * 100) if ipe_total_seg > 0 else 0
    cobertura_ajustada_lct = (ipe_ajustado_lct / ipe_total_lct * 100) if ipe_total_lct > 0 else 0
    cobertura_ajustada_com = (ipe_ajustado_com / ipe_total_com * 100) if ipe_total_com > 0 else 0
    cobertura_ajustada_mob = (ipe_ajustado_mob / ipe_total_mob * 100) if ipe_total_mob > 0 else 0
    
    dict_por_eixo = {
        'seg': cobertura_ajustada_seg,
        'lct': cobertura_ajustada_lct,
        'com': cobertura_ajustada_com,
        'mob': cobertura_ajustada_mob,
        'qtd_100': logradouros_100,
        'total_logs': len(ipe_total_por_log)
    }
    
    detalhes.sort(key=lambda x: x['cobertura_efetiva'], reverse=True)
    
    return cobertura_ajustada_total, dict_por_eixo, detalhes


def verificar_equipamentos_proximos(df_selecionados: pd.DataFrame, df_equipamentos: pd.DataFrame, 
                                     raio_camera: float = 50, nota_min: int = 4, eixos: list = None,
                                     raio_equipamento: float = 100) -> list:
    
    if df_selecionados.empty or df_equipamentos.empty:
        return []
    
    df_full = df_equipamentos.copy()
    df_full['eixo_norm'] = df_full['eixo'].astype(str).str.strip().str.upper()
    
    if eixos:
        df_equip = df_full[
            (df_full['eixo_norm'].isin(eixos)) & 
            (df_full['peso'] >= nota_min)
        ].copy()
    else:
        df_equip = df_full[df_full['peso'] >= nota_min].copy()
    
    if df_equip.empty:
        return []
    
    pontos_selecionados = []
    for _, cruz in df_selecionados.iterrows():
        pontos_selecionados.append((cruz['lat'], cruz['lon']))
    
    if len(pontos_selecionados) == 0:
        return []
    
    equipamentos_encontrados = {}
    raio_total = raio_camera + raio_equipamento  # 150m no caso padrão
    
    for _, equip in df_equip.iterrows():
        equip_lat, equip_lon = equip['lat'], equip['lon']
        equip_tipo = str(equip['tipo']).strip()
        
        if not equip_tipo or equip_tipo == '' or equip_tipo.lower() == 'nan':
            equip_tipo = 'Equipamento Não Identificado'
        
        esta_proximo = False
        for ponto_lat, ponto_lon in pontos_selecionados:
            dist = distancia_metros(equip_lat, equip_lon, ponto_lat, ponto_lon)
            if dist <= raio_total:
                esta_proximo = True
                break
        
        if esta_proximo:
            if equip_tipo not in equipamentos_encontrados:
                equipamentos_encontrados[equip_tipo] = 0
            equipamentos_encontrados[equip_tipo] += 1
    
    equipamentos_proximos = sorted(
        equipamentos_encontrados.items(), 
        key=lambda x: (-x[1], x[0])
    )
    
    return equipamentos_proximos



def carregar_excel_cruzamentos(filepath: Path) -> tuple:
    """Carrega e processa o Excel de cruzamentos"""
    try:
        if not filepath.exists():
            return None, None, f"Arquivo não encontrado: {filepath}"
        
        xls = pd.ExcelFile(filepath)
        
        if "MODELO" not in xls.sheet_names or "cruzamentos_100%" not in xls.sheet_names:
            return None, None, "Abas 'MODELO' e 'cruzamentos_100%' não encontradas."
        
        df_modelo = pd.read_excel(filepath, sheet_name="MODELO", header=None)
        
        idx_header = None
        for i, row in df_modelo.iterrows():
            if row.iloc[0] == "RANKING_IPE":
                idx_header = i
                break
        
        if idx_header is None:
            return None, None, "Cabeçalho da aba MODELO não identificado."
        
        df_logs = df_modelo.iloc[idx_header + 1:].copy()
        df_logs.columns = df_modelo.iloc[idx_header].values
        df_logs = df_logs.dropna(subset=[df_logs.columns[1]])
        
        logs = pd.DataFrame({
            'cod_log': pd.to_numeric(df_logs.iloc[:, 1], errors='coerce'),
            'nome': df_logs.iloc[:, 2].astype(str),
            'seg': pd.to_numeric(df_logs.iloc[:, 3], errors='coerce').fillna(0),
            'lct': pd.to_numeric(df_logs.iloc[:, 4], errors='coerce').fillna(0),
            'com': pd.to_numeric(df_logs.iloc[:, 5], errors='coerce').fillna(0),
            'mob': pd.to_numeric(df_logs.iloc[:, 6], errors='coerce').fillna(0)
        }).dropna(subset=['cod_log'])
        
        df_cruz = pd.read_excel(filepath, sheet_name="cruzamentos_100%", header=0)
        
        cruz_dict = {}
        id_counter = 1
        
        for _, row in df_cruz.iterrows():
            cod1, cod2 = row.iloc[0], row.iloc[4]
            if pd.isna(cod1) or pd.isna(cod2):
                continue
            
            cod1, cod2 = int(cod1), int(cod2)
            log1 = str(row.iloc[2]) if not pd.isna(row.iloc[2]) else ""
            log2 = str(row.iloc[6]) if not pd.isna(row.iloc[6]) else ""
            lat = float(row.iloc[11]) if not pd.isna(row.iloc[11]) else 0
            lon = float(row.iloc[12]) if not pd.isna(row.iloc[12]) else 0
            
            if cod1 < cod2:
                cod_min, cod_max, log_min, log_max = cod1, cod2, log1, log2
            else:
                cod_min, cod_max, log_min, log_max = cod2, cod1, log2, log1
            
            chave = f"{cod_min}|{cod_max}"
            
            if chave not in cruz_dict:
                cruz_dict[chave] = {
                    'id': id_counter, 'cod_log1': cod_min, 'log1': log_min,
                    'cod_log2': cod_max, 'log2': log_max, 'lat': lat, 'lon': lon
                }
                id_counter += 1
            elif lat != 0 and lon != 0:
                cruz_dict[chave]['lat'] = (cruz_dict[chave]['lat'] + lat) / 2
                cruz_dict[chave]['lon'] = (cruz_dict[chave]['lon'] + lon) / 2
        
        cruzamentos = pd.DataFrame(list(cruz_dict.values()))
        return logs, cruzamentos, f"✓ {len(logs)} logradouros, {len(cruzamentos)} cruzamentos"
    
    except Exception as e:
        return None, None, f"Erro: {str(e)}"


def carregar_excel_equipamentos(filepath: Path) -> tuple:
    """Carrega o Excel de equipamentos"""
    try:
        if not filepath.exists():
            return None, f"Arquivo não encontrado: {filepath}"
        
        df = pd.read_excel(filepath, header=0)
        cols_necessarias = ["LATITUDE COM PONTO", "LONGITUDE COM PONTO", "PESO"]
        for col in cols_necessarias:
            if col not in df.columns:
                return None, f"Coluna '{col}' não encontrada."
        
        equip = pd.DataFrame({
            'eixo': df.get("EIXO", pd.Series([""] * len(df))).astype(str),
            'tipo': df.get("TIPO DE EQUIPAMENTO", pd.Series([""] * len(df))).astype(str),
            'log': df.get("LOG_CORRIGIDO", pd.Series([""] * len(df))).astype(str),
            'lat': pd.to_numeric(df["LATITUDE COM PONTO"], errors='coerce'),
            'lon': pd.to_numeric(df["LONGITUDE COM PONTO"], errors='coerce'),
            'peso': pd.to_numeric(df["PESO"], errors='coerce').fillna(0)
        }).dropna(subset=['lat', 'lon'])
        
        return equip, f"✓ {len(equip)} equipamentos"
    except Exception as e:
        return None, f"Erro: {str(e)}"


def carregar_pontos_minimos(filepath: Path) -> tuple:
    """Carrega o Excel de pontos mínimos obrigatórios"""
    try:
        if not filepath.exists():
            return None, f"Arquivo não encontrado: {filepath}"
        
        df = pd.read_excel(filepath, header=0)
        
        col_map = {}
        for col in df.columns:
            col_lower = col.lower().strip()
            if 'tipo' in col_lower:
                col_map['tipo'] = col
            elif 'logradouro' in col_lower or 'log' in col_lower:
                col_map['logradouro'] = col
            elif 'lat' in col_lower:
                col_map['lat'] = col
            elif 'lon' in col_lower or 'lng' in col_lower:
                col_map['lon'] = col
            elif 'prioridade' in col_lower or 'peso' in col_lower:
                col_map['prioridade'] = col
            elif 'camera' in col_lower or 'câmera' in col_lower:
                col_map['cameras'] = col
        
        if 'lat' not in col_map or 'lon' not in col_map:
            return None, "Colunas 'latitude' e 'longitude' são obrigatórias."
        
        pontos = pd.DataFrame({
            'id_minimo': range(1, len(df) + 1),
            'tipo': df[col_map.get('tipo', df.columns[0])].astype(str) if 'tipo' in col_map else 'PONTO_MINIMO',
            'logradouro': df[col_map.get('logradouro', df.columns[0])].astype(str) if 'logradouro' in col_map else '',
            'lat': pd.to_numeric(df[col_map['lat']], errors='coerce'),
            'lon': pd.to_numeric(df[col_map['lon']], errors='coerce'),
            'prioridade': pd.to_numeric(df[col_map.get('prioridade', df.columns[0])], errors='coerce').fillna(5) if 'prioridade' in col_map else 5,
            'cameras': pd.to_numeric(df[col_map.get('cameras', df.columns[0])], errors='coerce').fillna(1).astype(int) if 'cameras' in col_map else 1
        }).dropna(subset=['lat', 'lon'])
        
        pontos = pontos.sort_values('prioridade', ascending=True).reset_index(drop=True)
        
        return pontos, f"✓ {len(pontos)} pontos mínimos carregados"
    except Exception as e:
        return None, f"Erro: {str(e)}"


def carregar_alagamentos(filepath: Path) -> tuple:
    """Carrega o Excel de pontos de alagamento"""
    try:
        if not filepath.exists():
            return None, f"Arquivo não encontrado: {filepath}"
        
        df = pd.read_excel(filepath, header=0)
        
        col_map = {}
        for col in df.columns:
            col_lower = col.lower().strip()
            if 'nome' in col_lower or 'descricao' in col_lower or 'descrição' in col_lower:
                col_map['nome'] = col
            elif 'lat' in col_lower:
                col_map['lat'] = col
            elif 'lon' in col_lower or 'lng' in col_lower:
                col_map['lon'] = col
            elif 'id' in col_lower:
                col_map['id'] = col
        
        if 'lat' not in col_map or 'lon' not in col_map:
            return None, "Colunas 'latitude' e 'longitude' são obrigatórias."
        
        alagamentos = pd.DataFrame({
            'id': df[col_map['id']].astype(str) if 'id' in col_map else range(1, len(df) + 1),
            'nome': df[col_map.get('nome', df.columns[0])].astype(str) if 'nome' in col_map else [f"Alagamento {i+1}" for i in range(len(df))],
            'lat': pd.to_numeric(df[col_map['lat']], errors='coerce'),
            'lon': pd.to_numeric(df[col_map['lon']], errors='coerce')
        }).dropna(subset=['lat', 'lon'])
        
        return alagamentos, f"✓ {len(alagamentos)} pontos de alagamento carregados"
    except Exception as e:
        return None, f"Erro: {str(e)}"


def carregar_sinistros(filepath: Path) -> tuple:
    """Carrega o Excel de sinistros por logradouro"""
    try:
        if not filepath.exists():
            return None, f"Arquivo não encontrado: {filepath}"
        
        df = pd.read_excel(filepath, header=0)
        
        col_map = {}
        for col in df.columns:
            col_lower = col.lower().strip()
            if 'logradouro' in col_lower or 'log' in col_lower or 'rua' in col_lower:
                col_map['logradouro'] = col
            elif 'qtd' in col_lower or 'quantidade' in col_lower or 'total' in col_lower:
                col_map['qtd'] = col
            elif 'id' in col_lower:
                col_map['id'] = col
        
        if 'logradouro' not in col_map:
            return None, "Coluna 'LOGRADOURO' é obrigatória."
        
        sinistros = pd.DataFrame({
            'id': df[col_map['id']].astype(str) if 'id' in col_map else df[col_map['logradouro']].astype(str),
            'logradouro': df[col_map['logradouro']].astype(str),
            'qtd': pd.to_numeric(df[col_map.get('qtd', df.columns[0])], errors='coerce').fillna(1).astype(int) if 'qtd' in col_map else 1
        })
        
        sinistros['logradouro'] = sinistros['logradouro'].str.strip().str.upper()
        
        return sinistros, f"✓ {len(sinistros)} logradouros com sinistros carregados"
    except Exception as e:
        return None, f"Erro: {str(e)}"


def carregar_bairros_geojson(filepath: Path) -> tuple:
    """Carrega o arquivo GeoJSON de bairros"""
    try:
        if not filepath.exists():
            return None, f"Arquivo não encontrado: {filepath}"
        
        with open(filepath, 'r', encoding='utf-8') as f:
            geojson_data = json.load(f)
        
        return geojson_data, "✓ Fronteira carregada"
    except Exception as e:
        return None, f"Erro: {str(e)}"


def carregar_arquivos_locais():
    """Carrega todos os arquivos locais na inicialização"""
    logs, cruzamentos, msg = carregar_excel_cruzamentos(ARQUIVO_CRUZAMENTOS)
    if logs is not None:
        st.session_state.logs = logs
        st.session_state.cruzamentos = cruzamentos
    
    pontos_min, msg = carregar_pontos_minimos(ARQUIVO_PRIORIDADES)
    if pontos_min is not None:
        st.session_state.pontos_minimos = pontos_min
    
    equip, msg = carregar_excel_equipamentos(ARQUIVO_EQUIPAMENTOS)
    if equip is not None:
        st.session_state.equipamentos = equip
    
    alag, msg = carregar_alagamentos(ARQUIVO_ALAGAMENTOS)
    if alag is not None:
        st.session_state.alagamentos = alag
    
    sinist, msg = carregar_sinistros(ARQUIVO_SINISTROS)
    if sinist is not None:
        st.session_state.sinistros = sinist
    
    if ARQUIVO_BAIRROS.exists():
        geojson_data, msg = carregar_bairros_geojson(ARQUIVO_BAIRROS)
        if geojson_data is not None:
            st.session_state.bairros_geojson = geojson_data
    
    st.session_state.arquivos_carregados = True



def calcular_ipe_cruzamentos(logs: pd.DataFrame, cruzamentos: pd.DataFrame, 
                              w_seg: float, w_lct: float, w_com: float, w_mob: float) -> pd.DataFrame:
    """Calcula IPE para todos os cruzamentos"""
    if logs.empty or cruzamentos.empty:
        return pd.DataFrame()
    
    logs_dict = logs.set_index('cod_log').to_dict('index')
    resultados = []
    
    for _, c in cruzamentos.iterrows():
        cod1, cod2 = c['cod_log1'], c['cod_log2']
        if cod1 not in logs_dict or cod2 not in logs_dict:
            continue
        
        l1, l2 = logs_dict[cod1], logs_dict[cod2]
        
        ipe1 = w_seg * l1['seg'] + w_lct * l1['lct'] + w_com * l1['com'] + w_mob * l1['mob']
        ipe2 = w_seg * l2['seg'] + w_lct * l2['lct'] + w_com * l2['com'] + w_mob * l2['mob']
        ipe_cruz = ipe1 + ipe2
        
        seg_tot = l1['seg'] + l2['seg']
        lct_tot = l1['lct'] + l2['lct']
        com_tot = l1['com'] + l2['com']
        mob_tot = l1['mob'] + l2['mob']
        
        resultados.append({
            'id': c['id'], 'cod_log1': cod1, 'log1': c['log1'],
            'cod_log2': cod2, 'log2': c['log2'], 'lat': c['lat'], 'lon': c['lon'],
            'ipe_log1': ipe1, 'ipe_log2': ipe2, 'ipe_cruz': ipe_cruz,
            'seg_tot': seg_tot, 'lct_tot': lct_tot, 'com_tot': com_tot, 'mob_tot': mob_tot,
            'ipe_cruz_seg': w_seg * seg_tot, 'ipe_cruz_lct': w_lct * lct_tot,
            'ipe_cruz_com': w_com * com_tot, 'ipe_cruz_mob': w_mob * mob_tot
        })
    
    if not resultados:
        return pd.DataFrame()
    
    df = pd.DataFrame(resultados).sort_values('ipe_cruz', ascending=False).reset_index(drop=True)
    
    total_ipe = df['ipe_cruz'].sum()
    if total_ipe > 0:
        df['perc_ipe'] = df['ipe_cruz'] / total_ipe
        df['cobertura_acum'] = df['ipe_cruz'].cumsum() / total_ipe
    else:
        df['perc_ipe'] = 0
        df['cobertura_acum'] = 0
    
    return df



def filtrar_por_cobertura_e_distancia(df: pd.DataFrame, cobertura_frac: float, min_dist: float, 
                                       max_cruzamentos: int = None, raio_cobertura: float = 50,
                                       limite_cobertura_logradouro: float = None,
                                       pontos_minimos: pd.DataFrame = None,
                                       max_cameras: int = None) -> tuple:
    
    df_pontos_minimos_usados = pd.DataFrame()
    
    if df.empty:
        return pd.DataFrame(), 0.0, True, None, set(), df_pontos_minimos_usados, 0
    
    ipe_total = df['ipe_cruz'].sum()
    if ipe_total <= 0:
        return pd.DataFrame(), 0.0, True, None, set(), df_pontos_minimos_usados, 0
    
    ipe_por_logradouro = {}
    if limite_cobertura_logradouro is not None:
        for _, c in df.iterrows():
            ipe = c['ipe_cruz']
            for cod_log in [c['cod_log1'], c['cod_log2']]:
                ipe_por_logradouro[cod_log] = ipe_por_logradouro.get(cod_log, 0) + ipe
    
    cobertura_por_logradouro = {}
    cruzamentos_por_logradouro = {}
    cruz_por_id = {}
    
    for _, c in df.iterrows():
        cruz_id = c['id']
        lat, lon = c['lat'], c['lon']
        ipe = c['ipe_cruz']
        cod_log1, cod_log2 = c['cod_log1'], c['cod_log2']
        
        cruz_por_id[cruz_id] = {
            'lat': lat, 'lon': lon, 'ipe': ipe,
            'cod_log1': cod_log1, 'cod_log2': cod_log2
        }
        
        for cod_log in [cod_log1, cod_log2]:
            if cod_log not in cruzamentos_por_logradouro:
                cruzamentos_por_logradouro[cod_log] = []
            cruzamentos_por_logradouro[cod_log].append((cruz_id, lat, lon, ipe))
    
    cameras_globais = []
    cameras_por_logradouro = {}
    
    def camera_muito_perto_global(lat, lon):
        if min_dist <= 0:
            return False
        for cam_lat, cam_lon in cameras_globais:
            if distancia_metros(lat, lon, cam_lat, cam_lon) < min_dist:
                return True
        return False
    
    def camera_muito_perto_no_logradouro(lat, lon, cod_log1, cod_log2):
        if min_dist <= 0:
            return False
        for cod_log in [cod_log1, cod_log2]:
            if cod_log in cameras_por_logradouro:
                for cam_lat, cam_lon in cameras_por_logradouro[cod_log]:
                    if distancia_metros(lat, lon, cam_lat, cam_lon) < min_dist:
                        return True
        return False
    
    def registrar_camera_global(lat, lon):
        cameras_globais.append((lat, lon))
    
    def registrar_camera_nos_logradouros(lat, lon, cod_log1, cod_log2):
        for cod_log in [cod_log1, cod_log2]:
            if cod_log not in cameras_por_logradouro:
                cameras_por_logradouro[cod_log] = []
            cameras_por_logradouro[cod_log].append((lat, lon))
    
    def calcular_cobertura_por_logradouro(cam_lat, cam_lon, cam_cod_log1, cam_cod_log2, ids_cobertos_atual):
        novos_cobertos = set()
        for cod_log in [cam_cod_log1, cam_cod_log2]:
            if cod_log in cruzamentos_por_logradouro:
                for cruz_id, lat, lon, ipe in cruzamentos_por_logradouro[cod_log]:
                    if cruz_id not in ids_cobertos_atual and cruz_id not in novos_cobertos:
                        if distancia_metros(cam_lat, cam_lon, lat, lon) <= raio_cobertura:
                            novos_cobertos.add(cruz_id)
        return novos_cobertos
    
    def violaria_limite_logradouro(cruz_id, novos_cobertos, cod_log1, cod_log2):
        if limite_cobertura_logradouro is None:
            return False
        
        ipe_adicional = {cod_log1: 0, cod_log2: 0}
        ipe_cruz = cruz_por_id[cruz_id]['ipe']
        ipe_adicional[cod_log1] += ipe_cruz
        ipe_adicional[cod_log2] += ipe_cruz
        
        for cob_id in novos_cobertos:
            if cob_id != cruz_id and cob_id in cruz_por_id:
                cob_info = cruz_por_id[cob_id]
                cob_ipe = cob_info['ipe']
                cob_log1, cob_log2 = cob_info['cod_log1'], cob_info['cod_log2']
                
                if cob_log1 not in ipe_adicional:
                    ipe_adicional[cob_log1] = 0
                if cob_log2 not in ipe_adicional:
                    ipe_adicional[cob_log2] = 0
                    
                ipe_adicional[cob_log1] += cob_ipe
                ipe_adicional[cob_log2] += cob_ipe
        
        for cod_log in [cod_log1, cod_log2]:
            ipe_total_log = ipe_por_logradouro.get(cod_log, 0)
            if ipe_total_log <= 0:
                continue
            
            ipe_atual = cobertura_por_logradouro.get(cod_log, 0)
            ipe_novo = ipe_atual + ipe_adicional.get(cod_log, 0)
            
            if ipe_novo / ipe_total_log > limite_cobertura_logradouro:
                return True
        
        return False
    
    def atualizar_cobertura_logradouros(cruz_id, novos_cobertos, cod_log1, cod_log2):
        if limite_cobertura_logradouro is None:
            return
        
        processados = set()
        ipe_cruz = cruz_por_id[cruz_id]['ipe']
        cobertura_por_logradouro[cod_log1] = cobertura_por_logradouro.get(cod_log1, 0) + ipe_cruz
        cobertura_por_logradouro[cod_log2] = cobertura_por_logradouro.get(cod_log2, 0) + ipe_cruz
        processados.add(cruz_id)
        
        for cob_id in novos_cobertos:
            if cob_id not in processados and cob_id in cruz_por_id:
                cob_info = cruz_por_id[cob_id]
                cob_ipe = cob_info['ipe']
                cob_log1, cob_log2 = cob_info['cod_log1'], cob_info['cod_log2']
                
                cobertura_por_logradouro[cob_log1] = cobertura_por_logradouro.get(cob_log1, 0) + cob_ipe
                cobertura_por_logradouro[cob_log2] = cobertura_por_logradouro.get(cob_log2, 0) + cob_ipe
                processados.add(cob_id)
    
    def calcular_cameras_por_ponto(indice_ponto: int) -> int:
        posicao_percent = (indice_ponto % 100)
        if posicao_percent < 50:
            return 3
        elif posicao_percent < 80:
            return 2
        else:
            return 1
    
    selecionados = []
    ids_cobertos = set()
    ipe_coberto = 0.0
    motivo_limite = None
    total_cameras = 0
    total_pontos = 0
    pontos_minimos_usados = []
    
    if pontos_minimos is not None and not pontos_minimos.empty:
        for _, ponto in pontos_minimos.iterrows():
            cameras_deste_ponto = int(ponto.get('cameras', 1))
            
            if max_cameras is not None and (total_cameras + cameras_deste_ponto) > max_cameras:
                motivo_limite = 'cameras'
                break
            
            lat, lon = ponto['lat'], ponto['lon']
            
            registrar_camera_global(lat, lon)
            total_cameras += cameras_deste_ponto
            total_pontos += 1
            
            pontos_minimos_usados.append({
                'id_minimo': ponto.get('id_minimo', len(pontos_minimos_usados) + 1),
                'tipo': ponto.get('tipo', 'PONTO_MINIMO'),
                'logradouro': ponto.get('logradouro', ''),
                'lat': lat,
                'lon': lon,
                'prioridade': ponto.get('prioridade', 5),
                'cameras': cameras_deste_ponto,
                'is_ponto_minimo': True
            })
            
            for cruz_id, info in cruz_por_id.items():
                if cruz_id not in ids_cobertos:
                    if distancia_metros(lat, lon, info['lat'], info['lon']) <= raio_cobertura:
                        ids_cobertos.add(cruz_id)
                        ipe_coberto += info['ipe']
        
        df_pontos_minimos_usados = pd.DataFrame(pontos_minimos_usados) if pontos_minimos_usados else pd.DataFrame()
    
    for _, c in df.iterrows():
        cameras_deste_ponto = calcular_cameras_por_ponto(total_pontos)
        
        if max_cameras is not None and (total_cameras + cameras_deste_ponto) > max_cameras:
            motivo_limite = 'cameras'
            break
        
        if max_cruzamentos is not None and len(selecionados) >= max_cruzamentos:
            motivo_limite = 'quantidade'
            break
        
        cobertura_atual = ipe_coberto / ipe_total
        if max_cruzamentos is None and max_cameras is None and cobertura_atual >= cobertura_frac:
            break
        
        lat, lon = c['lat'], c['lon']
        cruz_id = c['id']
        cod_log1, cod_log2 = c['cod_log1'], c['cod_log2']
        
        if camera_muito_perto_global(lat, lon):
            continue
        
        if camera_muito_perto_no_logradouro(lat, lon, cod_log1, cod_log2):
            continue
        
        novos_cobertos = calcular_cobertura_por_logradouro(lat, lon, cod_log1, cod_log2, ids_cobertos)
        if cruz_id not in ids_cobertos:
            novos_cobertos.add(cruz_id)
        
        if violaria_limite_logradouro(cruz_id, novos_cobertos, cod_log1, cod_log2):
            continue
        
        cruz_dict = c.to_dict()
        cruz_dict['cameras'] = cameras_deste_ponto
        selecionados.append(cruz_dict)
        
        registrar_camera_global(lat, lon)
        registrar_camera_nos_logradouros(lat, lon, cod_log1, cod_log2)
        atualizar_cobertura_logradouros(cruz_id, novos_cobertos, cod_log1, cod_log2)
        total_cameras += cameras_deste_ponto
        total_pontos += 1
        
        for cob_id in novos_cobertos:
            if cob_id in cruz_por_id and cob_id not in ids_cobertos:
                ipe_coberto += cruz_por_id[cob_id]['ipe']
        ids_cobertos.update(novos_cobertos)
    
    if not selecionados and df_pontos_minimos_usados.empty:
        return pd.DataFrame(), 0.0, False, None, set(), df_pontos_minimos_usados, 0
    
    df_result = pd.DataFrame(selecionados) if selecionados else pd.DataFrame()
    cobertura_real = ipe_coberto / ipe_total
    
    if not df_result.empty:
        df_result['cobertura_acum'] = df_result['ipe_cruz'].cumsum() / ipe_total
    
    alvo_atingido = cobertura_real >= cobertura_frac * 0.99
    if not alvo_atingido and motivo_limite is None:
        motivo_limite = 'restricoes'
    
    return df_result, cobertura_real, alvo_atingido, motivo_limite, ids_cobertos, df_pontos_minimos_usados, total_cameras



# ===== AJUSTE 3: FUNÇÃO criar_mapa SIMPLIFICADA =====
def criar_mapa(cruzamentos_selecionados: pd.DataFrame, equipamentos: pd.DataFrame, 
               nota_min_equip: int, bairros_geojson=None,
               pontos_minimos_usados: pd.DataFrame = None, mostrar_pontos_minimos: bool = True,
               mostrar_pontos_ipe: bool = True) -> folium.Map:
    """Cria o mapa com os cruzamentos, equipamentos e pontos mínimos"""
    m = folium.Map(location=[-8.07, -34.91], zoom_start=12, tiles='OpenStreetMap')
    
    if bairros_geojson is not None:
        folium.GeoJson(bairros_geojson, style_function=lambda x: {
            'fillColor': 'transparent', 'color': '#6b7280', 'weight': 2, 'fillOpacity': 0
        }).add_to(m)
    
    # Pontos Mínimos
    if mostrar_pontos_minimos and pontos_minimos_usados is not None and not pontos_minimos_usados.empty:
        for _, p in pontos_minimos_usados.iterrows():
            popup_html = f"""<div style="font-size:0.8rem; min-width:180px;">
                <strong>📍 PONTO OBRIGATÓRIO</strong><br/>
                <b>Tipo:</b> {p.get('tipo', 'N/A')}<br/>
                <b>Logradouro:</b> {p.get('logradouro', 'N/A')}<br/>
                <b>Prioridade:</b> {p.get('prioridade', 'N/A')}
            </div>"""
            folium.CircleMarker(
                location=[p['lat'], p['lon']], radius=5, color="#f6443b",
                fill=True, fillColor="#f6443b", fillOpacity=0.8, weight=2,
                popup=folium.Popup(popup_html, max_width=250)
            ).add_to(m)
    
    # Pontos via IPE
    if mostrar_pontos_ipe and not cruzamentos_selecionados.empty:
        for _, c in cruzamentos_selecionados.iterrows():
            popup_html = f"""<div style="font-size:0.8rem; min-width:180px;">
                <strong>Cruzamento {int(c['id'])}</strong><br/>
                <b>Ruas:</b> {c['log1']} x {c['log2']}<br/>
                <b>IPE:</b> {c['ipe_cruz']:.4f}<br/>
                <b>Cobertura:</b> {c['cobertura_acum']*100:.2f}%
            </div>"""
            folium.CircleMarker(
                location=[c['lat'], c['lon']], radius=5, color="#3b82f6",
                fill=True, fillColor="#3b82f6", fillOpacity=0.8, weight=1,
                popup=folium.Popup(popup_html, max_width=250)
            ).add_to(m)
    
    return m
# ===== FIM AJUSTE 3 =====


def gerar_csv_download(df_calculados: pd.DataFrame, df_selecionados: pd.DataFrame) -> bytes:
    """Gera CSV para download"""
    if df_calculados.empty:
        return b""
    
    ids_sel = set(df_selecionados['id'].values) if not df_selecionados.empty else set()
    df_export = df_calculados.copy()
    df_export['selecionado_no_mapa'] = df_export['id'].apply(lambda x: 1 if x in ids_sel else 0)
    
    cols = ['id', 'cod_log1', 'log1', 'cod_log2', 'log2', 'lat', 'lon',
            'ipe_log1', 'ipe_log2', 'ipe_cruz', 'perc_ipe', 'cobertura_acum', 'selecionado_no_mapa']
    
    df_export = df_export[cols]
    for col in ['ipe_log1', 'ipe_log2', 'ipe_cruz', 'perc_ipe', 'cobertura_acum']:
        df_export[col] = df_export[col].apply(lambda x: f"{x:.6f}")
    
    return df_export.to_csv(index=False, sep=';').encode('utf-8')


# ============================================================
# CARREGAMENTO INICIAL DOS ARQUIVOS
# ============================================================
if not st.session_state.arquivos_carregados:
    carregar_arquivos_locais()



# ============================================================
# SIDEBAR - CONTROLES COM AJUSTES 1 E 2
# ============================================================
with st.sidebar:
    st.markdown("## 🎛️ Controles")
    
    st.markdown('<div class="section-title">📁 Estatísticas gerais</div>', unsafe_allow_html=True)
    
    status_html = '<div class="stat-box">'
    if not st.session_state.logs.empty:
        status_html += f'<div class="stat-row"><span>✓ Cruzamentos:</span><span class="stat-value">{len(st.session_state.cruzamentos)}</span></div>'
    else:
        status_html += '<div class="stat-row"><span>✗ Cruzamentos:</span><span style="color:#ef4444;">Não carregado</span></div>'
    
    if not st.session_state.pontos_minimos.empty:
        status_html += f'<div class="stat-row"><span>✓ Prioridades:</span><span class="stat-value">{len(st.session_state.pontos_minimos)}</span></div>'
    else:
        status_html += '<div class="stat-row"><span>✗ Prioridades:</span><span style="color:#ef4444;">Não carregado</span></div>'
    
    if not st.session_state.equipamentos.empty:
        status_html += f'<div class="stat-row"><span>✓ Equipamentos:</span><span class="stat-value">{len(st.session_state.equipamentos)}</span></div>'
    else:
        status_html += '<div class="stat-row"><span>✗ Equipamentos:</span><span style="color:#ef4444;">Não carregado</span></div>'
    
    if not st.session_state.alagamentos.empty:
        status_html += f'<div class="stat-row"><span>✓ Alagamentos:</span><span class="stat-value">{len(st.session_state.alagamentos)}</span></div>'
    else:
        status_html += '<div class="stat-row"><span>✗ Alagamentos:</span><span style="color:#ef4444;">Não carregado</span></div>'
    
    if not st.session_state.sinistros.empty:
        total_sinistros_carregados = st.session_state.sinistros['qtd'].sum()
        status_html += f'<div class="stat-row"><span>✓ Sinistros:</span><span class="stat-value">{total_sinistros_carregados} em {len(st.session_state.sinistros)} ruas</span></div>'
    else:
        status_html += '<div class="stat-row"><span>✗ Sinistros:</span><span style="color:#ef4444;">Não carregado</span></div>'
    
    if st.session_state.bairros_geojson is not None:
        status_html += '<div class="stat-row"><span>✓ Bairros:</span><span class="stat-value">Carregado</span></div>'
    
    status_html += '</div>'
    st.markdown(status_html, unsafe_allow_html=True)
    
    # if st.button("🔄 Recarregar Arquivos", use_container_width=True):
    #     st.session_state.arquivos_carregados = False
    #     st.rerun()

    # nota_min_equip = st.slider("Nota minima equipamentos", 1, 5, 4, key='nota_equip')
    nota_min_equip = 4
    
    # ===== AJUSTE 1 E 2: FILTROS DE COBERTURA E LIMITE DE CÂMERAS =====
    st.markdown('<div class="section-title">1. Limite de Otimização</div>', unsafe_allow_html=True)
    
    modo_limite = st.radio(
        "Escolha o modo de limite:",
        ["Quantidade de Câmeras","Cobertura Alvo (%)"],
        key='modo_limite',
        help="Cobertura Alvo: otimiza até atingir % de cobertura desejada, restrito às condições de filtros. Quantidade: limita o número total de câmeras."
    )
    
    if modo_limite == "Cobertura Alvo (%)":
        # AJUSTE 1: Filtro de Cobertura Alvo Efetiva IPE
        cobertura_pct = st.slider(
            "Cobertura alvo efetiva IPE (%)", 
            0, 100, 80, step=5, 
            key='cobertura_alvo',
            help="Percentual de cobertura efetiva do IPE a ser atingido"
        )
        max_cameras = None
        st.markdown(f'''<div class="info-box">
            ℹ️ O otimizador buscará atingir <b>{cobertura_pct}%</b> de cobertura efetiva, restrito à distância mínima entre câmeras.
        </div>''', unsafe_allow_html=True)
    else:
        # AJUSTE 2: Limite Mínimo de 250 Câmeras
        cobertura_pct = 100
        max_cameras = st.number_input(
            "Máximo de câmeras", 
            min_value=250,  # ← AJUSTE 2: LIMITE MÍNIMO
            max_value=10000, 
            value=500, 
            step=10, 
            key='max_cameras',
            help="Limite total de câmeras no sistema (50% dos pontos = 3 câm, 30% = 2 câm, 20% = 1 câm). Mínimo: 250 câmeras"
        )
        st.markdown(f'''<div class="info-box">
            ℹ️ Limite fixo de <b>{max_cameras}</b> câmeras (distribuição: 50% dos pontos com 3 câm, 30% com 2 câm, 20% com 1 câm)
        </div>''', unsafe_allow_html=True)
    
    max_cruzamentos = None
    # ===== FIM AJUSTE 1 E 2 =====
    
    st.markdown('<div class="section-title">2. Distancia minima entre câmeras</div>', unsafe_allow_html=True)
    dist_min = st.slider("Distancia (m)", 50, 500, 300, step=50, key='dist_min', help="Distancia minima entre câmeras que compartilham o mesmo logradouro")
    
    # st.markdown('<div class="section-title">3b. Raio de cobertura das cameras</div>', unsafe_allow_html=True)
    # raio_cobertura = st.slider("Raio (m)",50, 250, 50, step=50, key='raio_cobertura')
    raio_cobertura=50
    
    # st.markdown('<div class="section-title">4. Limite de cobertura por logradouro</div>', unsafe_allow_html=True)
    # usar_limite_log = st.checkbox("Limitar cobertura por rua", value=False, key='usar_limite_log',
    #                                help="Evita concentracao de cameras em uma unica rua")
    # if usar_limite_log:
    #     limite_cob_log = st.slider("Maximo por logradouro (%)", 10, 100, 50, step=5, key='limite_log',
    #                                 help="Limita quanto do IPE de cada rua pode ser coberto") / 100
    #     st.markdown(f"""<div class="info-box">
    #         ℹ️ Cada rua tera no maximo <b>{limite_cob_log*100:.0f}%</b> do seu IPE coberto
    #     </div>""", unsafe_allow_html=True)
    # else:
    #     limite_cob_log = None
    limite_cob_log = None
    
    st.markdown('<div class="section-title">3. Pesos dos eixos IPE</div>', unsafe_allow_html=True)
    peso_seg = st.slider("Seguranca", 0, 100, 15, key='peso_seg')
    peso_lct = st.slider("LCT", 0, 100, 30, key='peso_lct')
    peso_com = st.slider("Comercial", 0, 100, 15, key='peso_com')
    peso_mob = st.slider("Mobilidade", 0, 100, 40, key='peso_mob')
    
    soma_pesos = peso_seg + peso_lct + peso_com + peso_mob or 1
    w_seg, w_lct = peso_seg / soma_pesos, peso_lct / soma_pesos
    w_com, w_mob = peso_com / soma_pesos, peso_mob / soma_pesos
    
    st.markdown(f"""<div class="stat-box">
        <span class="chip">Seg {w_seg*100:.0f}%</span>
        <span class="chip">LCT {w_lct*100:.0f}%</span>
        <span class="chip">Com {w_com*100:.0f}%</span>
        <span class="chip">Mob {w_mob*100:.0f}%</span>
    </div>""", unsafe_allow_html=True)



# ============================================================
# PROCESSAMENTO
# ============================================================
cobertura_real = 0.0
alvo_atingido = True
motivo_limite = None
ids_cobertos = set()

if not st.session_state.logs.empty and not st.session_state.cruzamentos.empty:
    st.session_state.cruzamentos_calculados = calcular_ipe_cruzamentos(
        st.session_state.logs, st.session_state.cruzamentos, w_seg, w_lct, w_com, w_mob
    )

df_pontos_minimos_usados = pd.DataFrame()
total_cameras_usado = 0

if not st.session_state.cruzamentos_calculados.empty:
    pontos_min_para_usar = st.session_state.pontos_minimos if not st.session_state.pontos_minimos.empty else None
    
    st.session_state.ultimo_selecionados, cobertura_real, alvo_atingido, motivo_limite, ids_cobertos, df_pontos_minimos_usados, total_cameras_usado = filtrar_por_cobertura_e_distancia(
        st.session_state.cruzamentos_calculados, cobertura_pct / 100, dist_min, 
        max_cruzamentos, raio_cobertura, limite_cob_log,
        pontos_min_para_usar, max_cameras
    )

# ✅ ADICIONAR AQUI (após ids_cobertos ser calculado):
# Calcular cobertura por logradouro ajustada
cobertura_ajustada_total = 0.0
cobertura_ajustada_eixos = {'seg': 0.0, 'lct': 0.0, 'com': 0.0, 'mob': 0.0, 'qtd_100': 0, 'total_logs': 0}
detalhes_logradouros = []

if not st.session_state.cruzamentos_calculados.empty and ids_cobertos:
    cobertura_ajustada_total, cobertura_ajustada_eixos, detalhes_logradouros = calcular_cobertura_por_logradouro_ajustada(
        st.session_state.cruzamentos_calculados,
        ids_cobertos,
        st.session_state.logs
    )

# ============================================================
# AREA PRINCIPAL - MAPA E RESUMOS
# ============================================================
st.markdown('<h1 class="main-header">Otimizador do Videomonitoramento - Recife</h1>', unsafe_allow_html=True)

if not st.session_state.cruzamentos_calculados.empty and not alvo_atingido and max_cruzamentos is None and max_cameras is None:
    restricoes_ativas = []
    if dist_min > 0:
        restricoes_ativas.append(f"distancia minima de {dist_min}m")
    if limite_cob_log is not None:
        restricoes_ativas.append(f"limite de {limite_cob_log*100:.0f}% por logradouro")
    
    restricoes_texto = " e ".join(restricoes_ativas) if restricoes_ativas else "as restricoes configuradas"

col_mapa, col_stats = st.columns([2, 1])

with col_mapa:
    # Preparar dados para o mapa com AJUSTE 3
    mapa = criar_mapa(
        st.session_state.ultimo_selecionados,
        st.session_state.equipamentos,
        nota_min_equip,
        st.session_state.bairros_geojson,
        df_pontos_minimos_usados,
        st.session_state.mostrar_pontos_minimos,
        st.session_state.mostrar_pontos_ipe
    )
    st_folium(mapa, width=None, height=650, returned_objects=[])
    
    # ===== AJUSTE 3: CHECKBOXES SIMPLIFICADOS ABAIXO DO MAPA =====
    # st.markdown("---")
    # col_check1, col_check2 = st.columns(2)
    
    # with col_check1:
    #     st.session_state.mostrar_pontos_minimos = st.checkbox(
    #         "📍 Mostrar Pontos Mínimos", 
    #         value=st.session_state.mostrar_pontos_minimos, 
    #         key='check_pontos_min'
    #     )
    
    # with col_check2:
    #     st.session_state.mostrar_pontos_ipe = st.checkbox(
    #         "📊 Mostrar Pontos via IPE", 
    #         value=st.session_state.mostrar_pontos_ipe, 
    #         key='check_pontos_ipe'
    #     )
    # ===== FIM AJUSTE 3 =====


with col_stats:
    if not st.session_state.cruzamentos_calculados.empty:
        df_calc = st.session_state.cruzamentos_calculados
        df_sel = st.session_state.ultimo_selecionados
        
        total_cruz = len(df_calc)
        total_sel = len(df_sel)
        total_cobertos = len(ids_cobertos)
        
        qtd_pontos_minimos = len(df_pontos_minimos_usados) if not df_pontos_minimos_usados.empty else 0
        cameras_pontos_minimos = df_pontos_minimos_usados['cameras'].sum() if not df_pontos_minimos_usados.empty and 'cameras' in df_pontos_minimos_usados.columns else 0
        
        qtd_pontos_ipe = total_sel
        cameras_pontos_ipe = df_sel['cameras'].sum() if not df_sel.empty and 'cameras' in df_sel.columns else 0
        
        total_pontos = qtd_pontos_minimos + qtd_pontos_ipe
        total_cameras = total_cameras_usado

        custo_unitario = 1610
        custo_total_geral = total_cameras * custo_unitario
        custo_formatado = f"R$ {custo_total_geral:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        
        # COBERTURA EFETIVA: cruzamentos cobertos pelo raio das câmeras
        df_cobertos = df_calc[df_calc['id'].isin(ids_cobertos)]
        
        # Calcular cobertura efetiva: somar IPE de todos os cruzamentos cobertos
        # (cruzamentos dentro do raio de pelo menos uma câmera)
        ipe_total_coberto_ajustado = 0
        ipe_seg_coberto_ajustado = 0
        ipe_lct_coberto_ajustado = 0
        ipe_com_coberto_ajustado = 0
        ipe_mob_coberto_ajustado = 0
        
        for _, cruz in df_cobertos.iterrows():
            ipe_total_coberto_ajustado += cruz['ipe_cruz']
            ipe_seg_coberto_ajustado += cruz['ipe_cruz_seg']
            ipe_lct_coberto_ajustado += cruz['ipe_cruz_lct']
            ipe_com_coberto_ajustado += cruz['ipe_cruz_com']
            ipe_mob_coberto_ajustado += cruz['ipe_cruz_mob']
        
        t_total = df_calc['ipe_cruz'].sum() or 1
        t_seg = df_calc['ipe_cruz_seg'].sum() or 1
        t_lct = df_calc['ipe_cruz_lct'].sum() or 1
        t_com = df_calc['ipe_cruz_com'].sum() or 1
        t_mob = df_calc['ipe_cruz_mob'].sum() or 1
        
        cobertura_real_ajustada = ipe_total_coberto_ajustado / t_total
        cov_seg = (ipe_seg_coberto_ajustado / t_seg * 100) if t_seg > 0 else 0
        cov_lct = (ipe_lct_coberto_ajustado / t_lct * 100) if t_lct > 0 else 0
        cov_com = (ipe_com_coberto_ajustado / t_com * 100) if t_com > 0 else 0
        cov_mob = (ipe_mob_coberto_ajustado / t_mob * 100) if t_mob > 0 else 0
        
        # CALCULAR COBERTURAS ADICIONAIS
        df_todos_pontos = st.session_state.ultimo_selecionados.copy()
        if not df_pontos_minimos_usados.empty:
            df_pontos_min_adaptado = df_pontos_minimos_usados[['lat', 'lon']].copy()
            for col in df_todos_pontos.columns:
                if col not in df_pontos_min_adaptado.columns:
                    df_pontos_min_adaptado[col] = ''
            df_todos_pontos = pd.concat([df_todos_pontos, df_pontos_min_adaptado], ignore_index=True)
        
        df_full = st.session_state.equipamentos.copy()
        df_full['eixo_norm'] = df_full['eixo'].astype(str).str.strip().str.upper()
        total_equipamentos_lct_seg = len(df_full[
            (df_full['eixo_norm'].isin(['LCT', 'SEG'])) & 
            (df_full['peso'] >= nota_min_equip)
        ])
        equipamentos_lct_seg = verificar_equipamentos_proximos(
            df_todos_pontos, 
            st.session_state.equipamentos, 
            raio_camera=raio_cobertura,  # 50m
            nota_min=nota_min_equip,
            eixos=['LCT', 'SEG'],
            raio_equipamento=100  # 100m
        )
        total_lct_seg = sum(qtd for _, qtd in equipamentos_lct_seg)
        pct_equipamentos = (total_lct_seg / total_equipamentos_lct_seg * 100) if total_equipamentos_lct_seg > 0 else 0
        
        total_equipamentos_com = len(df_full[
            (df_full['eixo_norm'] == 'COM') & 
            (df_full['peso'] >= nota_min_equip)
        ])
        equipamentos_com = verificar_equipamentos_proximos(
            df_todos_pontos, 
            st.session_state.equipamentos, 
            raio_camera=raio_cobertura,  # 50m
            nota_min=nota_min_equip,
            eixos=['COM'],
            raio_equipamento=100  # 100m
        )
        total_com_equip = sum(qtd for _, qtd in equipamentos_com)
        pct_comercial = (total_com_equip / total_equipamentos_com * 100) if total_equipamentos_com > 0 else 0
        
        alagamentos_cobertos = verificar_alagamentos_por_raio(
            df_todos_pontos, 
            st.session_state.alagamentos, 
            raio_camera=raio_cobertura,  # 50m
            raio_ponto=100  # 100m
        )
        total_alvos_alagamento = len(st.session_state.alagamentos)
        qtd_alag = len(alagamentos_cobertos)
        pct_alagamentos = (qtd_alag / total_alvos_alagamento * 100) if total_alvos_alagamento > 0 else 0
        
        df_cobertos = df_calc[df_calc['id'].isin(ids_cobertos)]
        qtd_sinistros_cobertos, total_sinistros, logradouros_sinistros_cobertos = verificar_sinistros_por_logradouro(
            df_cobertos,
            st.session_state.sinistros
        )
        pct_sinistros = (qtd_sinistros_cobertos / total_sinistros * 100) if total_sinistros > 0 else 0

        
        # EXIBIR ESTATÍSTICAS
        st.markdown("#### 📊 Pontos e Câmeras")
        
        stats_html = f"""<div class="stat-box">
            <div class="stat-row"><span>Total de pontos disponíveis:</span><span class="stat-value">{total_cruz:,}</span></div>"""
        
        if qtd_pontos_minimos > 0:
            stats_html += f"""
            <div class="stat-row"><span>Pontos mínimos:</span><span class="stat-value">{qtd_pontos_minimos:,} pts ({int(cameras_pontos_minimos)} câm)</span></div>"""
        
        stats_html += f"""
            <div class="stat-row"><span>Pontos otimizados:</span><span class="stat-value">{qtd_pontos_ipe:,} pts ({int(cameras_pontos_ipe)} câm)</span></div>
            <div class="stat-row"><span><b>Total de pontos:</b></span><span class="stat-value" style="font-size: 1.1rem;">{total_pontos:,}</span></div>
            <div class="stat-row"><span><b>Total de câmeras:</b></span><span class="stat-value" style="font-size: 1.1rem;">{total_cameras:,}</span></div>
            <div class="stat-row" style="margin-top: 5px; font-size: 1rem;"><span><b>Custo Total:</b></span><span class="stat-value" style="color: #4ade80;">{custo_formatado}</span></div>"""
        
        # stats_html += f"""</div>
        # <div class="stat-box">
        #     <div class="stat-row"><span><b>Total de pontos:</b></span><span class="stat-value" style="font-size: 1.1rem;">{total_pontos:,}</span></div>
        #     <div class="stat-row"><span><b>Total de câmeras:</b></span><span class="stat-value" style="font-size: 1.1rem;">{total_cameras:,}</span></div>
        #     <div class="stat-row" style="margin-top: 5px; font-size: 1rem;"><span><b>Custo Total:</b></span><span class="stat-value" style="color: #4ade80;">{custo_formatado}</span></div>"""        

        # stats_html += f"""
        #     <div class="stat-row"><span>Equipamentos:</span><span class="stat-value">{pct_equipamentos:.1f}%</span></div>
        #     <div class="stat-row"><span>Comercial:</span><span class="stat-value">{pct_comercial:.1f}%</span></div>
        #     <div class="stat-row"><span>Alagamentos:</span><span class="stat-value">{pct_alagamentos:.1f}%</span></div>
        #     <div class="stat-row"><span>Sinistros:</span><span class="stat-value">{pct_sinistros:.1f}% ({qtd_sinistros_cobertos}/{total_sinistros})</span></div>
        # </div>"""
        
        st.markdown(stats_html, unsafe_allow_html=True)

        st.markdown("#### 🏙️ Cobertura da Cidade")
        st.markdown(f"""<div class="stat-box">
            <div class="stat-row"><span>Equipamentos:</span><span class="stat-value">{pct_equipamentos:.1f}%</span></div>
            <div class="stat-row"><span>Comercial:</span><span class="stat-value">{pct_comercial:.1f}%</span></div>
            <div class="stat-row"><span>Alagamentos:</span><span class="stat-value">{pct_alagamentos:.1f}%</span></div>
            <div class="stat-row"><span>Sinistros:</span><span class="stat-value">{pct_sinistros:.1f}% ({qtd_sinistros_cobertos}/{total_sinistros})</span></div>
        </div>""", unsafe_allow_html=True)

        st.markdown("#### 📈 Cobertura de Risco IPE")
        st.markdown(f"""<div class="stat-box">
            <div class="stat-row"<span>Cobertura de risco IPE:</span><span class="stat-value" style="color: #4ade80;">{cobertura_ajustada_total:.1f}%</span></div>
            <div class="stat-row"><span>Seguranca:</span><span class="stat-value">{cobertura_ajustada_eixos['seg']:.1f}%</span></div>
            <div class="stat-row"><span>Lazer, Cultura e Turismo:</span><span class="stat-value">{cobertura_ajustada_eixos['lct']:.1f}%</span></div>
            <div class="stat-row"><span>Comercial:</span><span class="stat-value">{cobertura_ajustada_eixos['com']:.1f}%</span></div>
            <div class="stat-row"><span>Mobilidade:</span><span class="stat-value">{cobertura_ajustada_eixos['mob']:.1f}%</span></div>
        </div>""", unsafe_allow_html=True)

        # st.markdown("#### 🎯 Cobertura por Logradouro (Ajustada)")
        # qtd_100 = cobertura_ajustada_eixos.get('qtd_100', 0)
        # total_logs = cobertura_ajustada_eixos.get('total_logs', 0)
        # st.markdown(f"""<div class="highlight-box">
        #     <div class="stat-row" style="border-bottom: 1px solid rgba(34, 197, 94, 0.4); padding-bottom: 5px; margin-bottom: 5px;">
        #         <span><b>Cobertura Total Ajustada:</b></span><span style="color: #86efac; font-weight: 700; font-size: 1.1rem;">{cobertura_ajustada_total:.1f}%</span>
        #     </div>
        #     <div style="font-size: 0.75rem; color: #86efac; margin-bottom: 3px;">
        #         Logradouros com ≥50% → 100% | Logradouros com &lt;50% → mantém atual
        #     </div>
        #     <div style="font-size: 0.7rem; color: #64748b;">
        #         {qtd_100} de {total_logs} logradouros atingiram 100% de cobertura
        #     </div>
        # </div>""", unsafe_allow_html=True)
        
        # st.markdown(f"""<div class="stat-box">
        #     <div class="stat-row"><span>Seguranca:</span><span class="stat-value">{cobertura_ajustada_eixos['seg']:.1f}%</span></div>
        #     <div class="stat-row"><span>Lazer, Cultura e Turismo:</span><span class="stat-value">{cobertura_ajustada_eixos['lct']:.1f}%</span></div>
        #     <div class="stat-row"><span>Comercial:</span><span class="stat-value">{cobertura_ajustada_eixos['com']:.1f}%</span></div>
        #     <div class="stat-row"><span>Mobilidade:</span><span class="stat-value">{cobertura_ajustada_eixos['mob']:.1f}%</span></div>
        # </div>""", unsafe_allow_html=True)
        
        csv_data = gerar_csv_download(df_calc, df_sel)
        st.download_button("📥 Baixar CSV", csv_data, "ipe_cruzamentos.csv", "text/csv", use_container_width=True)
    else:
        st.info("⚠️ Nenhum arquivo foi carregado. Verifique o diretório 'data/'.")

# ============================================================
# SEÇÃO ABAIXO DO MAPA - CARDS DETALHADOS
# ============================================================
st.markdown("---")

col_equip_lct, col_equip_com, col_alag, col_sinist = st.columns(4)

with col_equip_lct:
    if not st.session_state.equipamentos.empty and not st.session_state.cruzamentos_calculados.empty:
        df_todos_pontos = st.session_state.ultimo_selecionados.copy()
        
        if not df_pontos_minimos_usados.empty:
            df_pontos_min_adaptado = df_pontos_minimos_usados[['lat', 'lon']].copy()
            for col in df_todos_pontos.columns:
                if col not in df_pontos_min_adaptado.columns:
                    df_pontos_min_adaptado[col] = ''
            
            df_todos_pontos = pd.concat([df_todos_pontos, df_pontos_min_adaptado], ignore_index=True)
        
        df_full = st.session_state.equipamentos.copy()
        df_full['eixo_norm'] = df_full['eixo'].astype(str).str.strip().str.upper()
        total_equipamentos_lct_seg = len(df_full[
            (df_full['eixo_norm'].isin(['LCT', 'SEG'])) & 
            (df_full['peso'] >= nota_min_equip)
        ])
        
        equipamentos_lct_seg = verificar_equipamentos_proximos(
            df_todos_pontos, 
            st.session_state.equipamentos, 
            raio_cobertura,
            nota_min_equip,
            ['LCT', 'SEG']
        )
        
        total_lct_seg = sum(qtd for _, qtd in equipamentos_lct_seg)
        pct_lct_seg = (total_lct_seg / total_equipamentos_lct_seg * 100) if total_equipamentos_lct_seg > 0 else 0
        
        if total_lct_seg > 0:
            html_main = ""
            for nome, qtd in equipamentos_lct_seg:
                if nome and str(nome).strip() != "":
                    html_main += f'<div class="stat-row"><span>{nome}:</span><span class="stat-value">{qtd}</span></div>'
            
            st.markdown(f"#### 🏢 Equipamentos")
            st.markdown(f"""<div class="stat-box" style="margin-bottom: 1rem;">
                <div class="stat-row" style="border-bottom: 1px solid rgba(148, 163, 184, 0.3); padding-bottom: 5px; margin-bottom: 5px;">
                    <span><b>Cobertura:</b></span><span class="stat-value">{total_lct_seg} ({pct_lct_seg:.1f}%)</span>
                </div>
                <div style="font-size: 0.7rem; color: #64748b; margin-bottom: 5px;">
                    Calculado sobre {total_equipamentos_lct_seg} equipamentos mapeados.
                </div>
                <div style="max-height: 150px; overflow-y: auto; padding-right: 5px; font-size: 0.75rem;">
                    {html_main}
                </div>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"#### 🏢 Equipamentos")
            st.markdown(f"""<div class="stat-box">
                <div class="stat-row" style="border-bottom: 1px solid rgba(148, 163, 184, 0.3); padding-bottom: 5px; margin-bottom: 5px;">
                    <span><b>Cobertura:</b></span><span class="stat-value">0 (0.0%)</span>
                </div>
                <div style="font-size: 0.7rem; color: #64748b; margin-bottom: 5px;">
                    Calculado sobre {total_equipamentos_lct_seg} equipamentos mapeados.
                </div>
                <div class="stat-row"><span>Nenhum equipamento LCT/SEG próximo.</span></div>
            </div>""", unsafe_allow_html=True)
    else:
        st.markdown("#### 🏢 Equipamentos")
        st.markdown("""<div class="stat-box"><div class="stat-row"><span>Carregue os dados.</span></div></div>""", unsafe_allow_html=True)

with col_equip_com:
    if not st.session_state.equipamentos.empty and not st.session_state.cruzamentos_calculados.empty:
        df_todos_pontos = st.session_state.ultimo_selecionados.copy()
        
        if not df_pontos_minimos_usados.empty:
            df_pontos_min_adaptado = df_pontos_minimos_usados[['lat', 'lon']].copy()
            for col in df_todos_pontos.columns:
                if col not in df_pontos_min_adaptado.columns:
                    df_pontos_min_adaptado[col] = ''
            
            df_todos_pontos = pd.concat([df_todos_pontos, df_pontos_min_adaptado], ignore_index=True)
        
        df_full = st.session_state.equipamentos.copy()
        df_full['eixo_norm'] = df_full['eixo'].astype(str).str.strip().str.upper()
        total_equipamentos_com = len(df_full[
            (df_full['eixo_norm'] == 'COM') & 
            (df_full['peso'] >= nota_min_equip)
        ])
        
        equipamentos_com = verificar_equipamentos_proximos(
            df_todos_pontos, 
            st.session_state.equipamentos, 
            raio_cobertura,
            nota_min_equip,
            ['COM']
        )
        
        total_com = sum(qtd for _, qtd in equipamentos_com)
        pct_com = (total_com / total_equipamentos_com * 100) if total_equipamentos_com > 0 else 0
        
        if total_com > 0:
            html_com = ""
            for nome, qtd in equipamentos_com:
                if nome and str(nome).strip() != "":
                    html_com += f'<div class="stat-row"><span>{nome}:</span><span class="stat-value">{qtd}</span></div>'
            
            st.markdown(f"#### 🏪 Comercial")
            st.markdown(f"""<div class="stat-box" style="margin-bottom: 1rem;">
                <div class="stat-row" style="border-bottom: 1px solid rgba(148, 163, 184, 0.3); padding-bottom: 5px; margin-bottom: 5px;">
                    <span><b>Cobertura:</b></span><span class="stat-value">{total_com} ({pct_com:.1f}%)</span>
                </div>
                <div style="font-size: 0.7rem; color: #64748b; margin-bottom: 5px;">
                    Calculado sobre {total_equipamentos_com} equipamentos mapeados.
                </div>
                <div style="max-height: 150px; overflow-y: auto; padding-right: 5px; font-size: 0.75rem;">
                    {html_com}
                </div>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"#### 🏪 Comercial")
            st.markdown(f"""<div class="stat-box">
                <div class="stat-row" style="border-bottom: 1px solid rgba(148, 163, 184, 0.3); padding-bottom: 5px; margin-bottom: 5px;">
                    <span><b>Cobertura:</b></span><span class="stat-value">0 (0.0%)</span>
                </div>
                <div style="font-size: 0.7rem; color: #64748b; margin-bottom: 5px;">
                    Calculado sobre {total_equipamentos_com} equipamentos mapeados.
                </div>
                <div class="stat-row"><span>Nenhum equipamento Comercial próximo.</span></div>
            </div>""", unsafe_allow_html=True)
    else:
        st.markdown("#### 🏪 Comercial")
        st.markdown("""<div class="stat-box"><div class="stat-row"><span>Carregue os dados.</span></div></div>""", unsafe_allow_html=True)

with col_alag:
    if not st.session_state.cruzamentos_calculados.empty and not st.session_state.alagamentos.empty:
        df_todos_pontos_alag = st.session_state.ultimo_selecionados.copy()
        
        if not df_pontos_minimos_usados.empty:
            df_pontos_min_adaptado = df_pontos_minimos_usados[['lat', 'lon']].copy()
            for col in df_todos_pontos_alag.columns:
                if col not in df_pontos_min_adaptado.columns:
                    df_pontos_min_adaptado[col] = ''
            df_todos_pontos_alag = pd.concat([df_todos_pontos_alag, df_pontos_min_adaptado], ignore_index=True)
        
        alagamentos_encontrados = verificar_alagamentos_por_raio(
            df_todos_pontos_alag, 
            st.session_state.alagamentos, 
            raio_cobertura
        )
        
        total_alvos_alagamento = len(st.session_state.alagamentos)
        qtd_alag = len(alagamentos_encontrados)
        pct_alag = (qtd_alag / total_alvos_alagamento * 100) if total_alvos_alagamento > 0 else 0
        
        html_alagamentos = ""
        if alagamentos_encontrados:
            for alag in alagamentos_encontrados:
                alag_display = alag if len(alag) <= 60 else alag[:57] + "..."
                html_alagamentos += f'<div class="stat-row" style="justify-content: flex-start;"><span style="color:#fbbf24; font-size: 0.7rem;">⚠️ {alag_display}</span></div>'
        else:
            html_alagamentos = '<div class="stat-row"><span>Nenhum ponto de alagamento.</span></div>'
        
        st.markdown("#### 🌊 Alagamentos")
        st.markdown(f"""<div class="stat-box">
            <div class="stat-row" style="border-bottom: 1px solid rgba(148, 163, 184, 0.3); padding-bottom: 5px; margin-bottom: 5px;">
                <span><b>Cobertura:</b></span><span class="stat-value">{qtd_alag} ({pct_alag:.1f}%)</span>
            </div>
            <div style="font-size: 0.7rem; color: #64748b; margin-bottom: 5px;">
                Calculado sobre {total_alvos_alagamento} pontos mapeados.
            </div>
            <div style="max-height: 150px; overflow-y: auto; padding-right: 5px; font-size: 0.75rem;">
                {html_alagamentos}
            </div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown("#### 🌊 Alagamentos")
        st.markdown("""<div class="stat-box"><div class="stat-row"><span>Carregue os dados.</span></div></div>""", unsafe_allow_html=True)

with col_sinist:
    if not st.session_state.cruzamentos_calculados.empty and not st.session_state.sinistros.empty:
        df_todos_cobertos = st.session_state.cruzamentos_calculados[
            st.session_state.cruzamentos_calculados['id'].isin(ids_cobertos)
        ]
        
        qtd_sinistros_cobertos, total_sinistros, logradouros_encontrados = verificar_sinistros_por_logradouro(
            df_todos_cobertos,
            st.session_state.sinistros
        )
        
        qtd_ruas = len(logradouros_encontrados)
        total_ruas = len(st.session_state.sinistros)
        pct_sinist = (qtd_sinistros_cobertos / total_sinistros * 100) if total_sinistros > 0 else 0
        
        html_sinistros = ""
        if logradouros_encontrados:
            sinistros_dict = {}
            for _, row in st.session_state.sinistros.iterrows():
                log_norm = str(row['logradouro']).strip().upper()
                qtd = int(row.get('qtd', 1))
                sinistros_dict[log_norm] = qtd
            
            for rua in logradouros_encontrados:
                qtd_nesta_rua = sinistros_dict.get(rua, 0)
                rua_display = rua if len(rua) <= 50 else rua[:47] + "..."
                html_sinistros += f'<div class="stat-row" style="justify-content: space-between;"><span style="color:#f87171; font-size: 0.7rem;">🚗 {rua_display}</span><span class="stat-value" style="font-size: 0.7rem;">{qtd_nesta_rua}</span></div>'
        else:
            html_sinistros = '<div class="stat-row"><span>Nenhuma rua com sinistros.</span></div>'
        
        st.markdown("#### 🚗 Sinistros")
        st.markdown(f"""<div class="stat-box">
            <div class="stat-row" style="border-bottom: 1px solid rgba(148, 163, 184, 0.3); padding-bottom: 5px; margin-bottom: 5px;">
                <span><b>Cobertura:</b></span><span class="stat-value">{qtd_sinistros_cobertos}/{total_sinistros} ({pct_sinist:.1f}%)</span>
            </div>
            <div style="font-size: 0.7rem; color: #64748b; margin-bottom: 5px;">
                {qtd_ruas} de {total_ruas} ruas cobertas.
            </div>
            <div style="max-height: 150px; overflow-y: auto; padding-right: 5px; font-size: 0.75rem;">
                {html_sinistros}
            </div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown("#### 🚗 Sinistros")
        st.markdown("""<div class="stat-box"><div class="stat-row"><span>Carregue os dados.</span></div></div>""", unsafe_allow_html=True)