import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
import json
import math
from pathlib import Path
from shapely.geometry import Polygon, MultiPolygon, box, shape
from shapely.ops import unary_union

# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================
st.set_page_config(
    page_title="Otimizador do Videomonitoramento – COP Recife",
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
ARQUIVO_VIAS_PRIORITARIAS = DATA_DIR / "Vias Prioritarias.xlsx"
ARQUIVO_CVP = DATA_DIR / "CVP.xlsx"

# ============================================================
# CSS CUSTOMIZADO - Layout compacto
# ============================================================
st.markdown("""
<style>
    .stApp { background-color: #0e1117 !important; color: #e6eef8 !important; }
    .stSidebar { background-color: #0b0e13 !important; }
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
    /* Remover overflow de TODOS os containers da sidebar */
    [data-testid="stSidebar"],
    [data-testid="stSidebar"] > div,
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
        overflow: visible !important;
    }
    
    /* Aplicar scroll APENAS no container principal da sidebar */
    section[data-testid="stSidebar"] {
        min-width: 400px;
        max-width: 400px;
        overflow-y: auto !important;
        overflow-x: hidden !important;
        height: 100vh !important;
        transform: none !important;
        visibility: visible !important;
        position: relative !important;
    }
    
    [data-testid="stSidebar"] > div:first-child {
        width: 400px;
        padding-bottom: 3rem;
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
if 'vias_prioritarias' not in st.session_state:
    st.session_state.vias_prioritarias = pd.DataFrame()
if 'cvp' not in st.session_state:  # ← ADICIONAR ESTAS LINHAS
    st.session_state.cvp = pd.DataFrame()
if 'arquivos_carregados' not in st.session_state:
    st.session_state.arquivos_carregados = False
if 'incluir_red_anterior' not in st.session_state:
    st.session_state.incluir_red_anterior = False


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

def verificar_vias_prioritarias_por_logradouro(df_cruzamentos_selecionados: pd.DataFrame, 
                                                 df_vias_prioritarias: pd.DataFrame) -> tuple:
    if df_cruzamentos_selecionados.empty or df_vias_prioritarias.empty:
        return 0, 0, []
    
    # Criar dicionário de vias prioritárias com suas prioridades
    vias_dict = {}
    for _, row in df_vias_prioritarias.iterrows():
        log_norm = str(row['logradouro']).strip().upper()
        prioridade = int(row.get('prioridade', 5))
        vias_dict[log_norm] = prioridade
    
    # Verificar quais vias prioritárias estão cobertas
    vias_cobertas = {}
    
    for _, cruz in df_cruzamentos_selecionados.iterrows():
        log1 = str(cruz.get('log1', '')).strip().upper()
        log2 = str(cruz.get('log2', '')).strip().upper()
        
        if log1 in vias_dict and log1 not in vias_cobertas:
            vias_cobertas[log1] = vias_dict[log1]
        
        if log2 in vias_dict and log2 not in vias_cobertas:
            vias_cobertas[log2] = vias_dict[log2]
    
    qtd_vias_cobertas = len(vias_cobertas)
    total_vias = len(vias_dict)
    
    # Criar lista ordenada por prioridade (menor número = maior prioridade)
    lista_vias = sorted(
        [(via, prio) for via, prio in vias_cobertas.items()],
        key=lambda x: x[1]
    )
    
    return qtd_vias_cobertas, total_vias, lista_vias

def verificar_cvp_por_logradouro(df_cruzamentos_selecionados: pd.DataFrame, df_cvp: pd.DataFrame) -> tuple:
    """Verifica quais logradouros com CVP têm cobertura de câmeras"""
    if df_cruzamentos_selecionados.empty or df_cvp.empty:
        return 0, 0, []
    
    cvp_dict = {}
    for _, row in df_cvp.iterrows():
        log_norm = str(row['logradouro']).strip().upper()
        qtd = int(row.get('cvp', 0))
        cvp_dict[log_norm] = qtd
    
    logradouros_cobertos = {}
    
    for _, cruz in df_cruzamentos_selecionados.iterrows():
        log1 = str(cruz.get('log1', '')).strip().upper()
        log2 = str(cruz.get('log2', '')).strip().upper()
        
        if log1 in cvp_dict and log1 not in logradouros_cobertos:
            logradouros_cobertos[log1] = cvp_dict[log1]
        
        if log2 in cvp_dict and log2 not in logradouros_cobertos:
            logradouros_cobertos[log2] = cvp_dict[log2]
    
    qtd_cvp_cobertos = sum(logradouros_cobertos.values())
    total_cvp = sum(cvp_dict.values())
    lista_logradouros = list(logradouros_cobertos.keys())
    
    return qtd_cvp_cobertos, total_cvp, lista_logradouros

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


def carregar_pontos_minimos(filepath: Path, incluir_red: bool = False) -> tuple:
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
        
        # ===== NOVO: FILTRAR PONTOS RED =====
        if not incluir_red:
            # Remove pontos RED se não estiverem incluídos
            pontos = pontos[pontos['tipo'].str.strip().str.upper() != 'RED']
        else:
            # Adiciona coluna identificadora para pontos RED
            pontos['is_red'] = pontos['tipo'].str.strip().str.upper() == 'RED'
        # ===== FIM NOVO =====
        
        pontos = pontos.sort_values('prioridade', ascending=True).reset_index(drop=True)
        
        msg = f"✓ {len(pontos)} pontos mínimos carregados"
        if incluir_red:
            qtd_red = (pontos['tipo'].str.strip().str.upper() == 'RED').sum()
            msg += f" ({qtd_red} RED)"
        
        return pontos, msg
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

def carregar_vias_prioritarias(filepath: Path) -> tuple:
    """Carrega o Excel de vias prioritárias"""
    try:
        if not filepath.exists():
            return None, f"Arquivo não encontrado: {filepath}"
        
        df = pd.read_excel(filepath, header=0)
        
        col_map = {}
        for col in df.columns:
            col_lower = col.lower().strip()
            if 'logradouro' in col_lower or 'log' in col_lower or 'rua' in col_lower or 'via' in col_lower:
                col_map['logradouro'] = col
            elif 'prioridade' in col_lower or 'peso' in col_lower or 'nota' in col_lower:
                col_map['prioridade'] = col
            elif 'id' in col_lower:
                col_map['id'] = col
        
        if 'logradouro' not in col_map:
            return None, "Coluna 'LOGRADOURO' é obrigatória."
        
        vias = pd.DataFrame({
            'id': df[col_map['id']].astype(str) if 'id' in col_map else df[col_map['logradouro']].astype(str),
            'logradouro': df[col_map['logradouro']].astype(str),
            'prioridade': pd.to_numeric(df[col_map.get('prioridade', df.columns[0])], errors='coerce').fillna(5).astype(int) if 'prioridade' in col_map else 5
        })
        
        vias['logradouro'] = vias['logradouro'].str.strip().str.upper()
        
        return vias, f"✓ {len(vias)} vias prioritárias carregadas"
    except Exception as e:
        return None, f"Erro: {str(e)}"

def carregar_cvp(filepath: Path) -> tuple:
    """Carrega o Excel de CVP (Crimes Contra o Patrimônio) por logradouro"""
    try:
        if not filepath.exists():
            return None, f"Arquivo não encontrado: {filepath}"
        
        df = pd.read_excel(filepath, header=0)
        
        col_map = {}
        for col in df.columns:
            col_lower = col.lower().strip()
            if 'logradouro' in col_lower or 'log' in col_lower or 'rua' in col_lower:
                col_map['logradouro'] = col
            elif 'cvp' in col_lower or 'crime' in col_lower or 'patrimonio' in col_lower or 'patrimônio' in col_lower:
                col_map['cvp'] = col
            elif 'id' in col_lower:
                col_map['id'] = col
        
        if 'logradouro' not in col_map:
            return None, "Coluna 'LOGRADOURO' é obrigatória."
        
        if 'cvp' not in col_map:
            return None, "Coluna 'CVP' é obrigatória."
        
        cvp_data = pd.DataFrame({
            'id': df[col_map['id']].astype(str) if 'id' in col_map else df[col_map['logradouro']].astype(str),
            'logradouro': df[col_map['logradouro']].astype(str),
            'cvp': pd.to_numeric(df[col_map['cvp']], errors='coerce').fillna(0).astype(int)
        })
        
        cvp_data['logradouro'] = cvp_data['logradouro'].str.strip().str.upper()
        
        # Remover registros com CVP = 0
        cvp_data = cvp_data[cvp_data['cvp'] > 0]
        
        return cvp_data, f"✓ {len(cvp_data)} logradouros com CVP carregados"
    except Exception as e:
        return None, f"Erro: {str(e)}"

def carregar_arquivos_locais(incluir_red: bool = False):
    """Carrega todos os arquivos locais na inicialização"""
    logs, cruzamentos, msg = carregar_excel_cruzamentos(ARQUIVO_CRUZAMENTOS)
    if logs is not None:
        st.session_state.logs = logs
        st.session_state.cruzamentos = cruzamentos
    
    # ===== MODIFICADO: PASSAR PARÂMETRO incluir_red =====
    pontos_min, msg = carregar_pontos_minimos(ARQUIVO_PRIORIDADES, incluir_red)
    if pontos_min is not None:
        st.session_state.pontos_minimos = pontos_min
    # ===== FIM MODIFICADO =====
    
    equip, msg = carregar_excel_equipamentos(ARQUIVO_EQUIPAMENTOS)
    if equip is not None:
        st.session_state.equipamentos = equip
    
    alag, msg = carregar_alagamentos(ARQUIVO_ALAGAMENTOS)
    if alag is not None:
        st.session_state.alagamentos = alag
    
    sinist, msg = carregar_sinistros(ARQUIVO_SINISTROS)
    if sinist is not None:
        st.session_state.sinistros = sinist
    
    vias_prior, msg = carregar_vias_prioritarias(ARQUIVO_VIAS_PRIORITARIAS)
    if vias_prior is not None:
        st.session_state.vias_prioritarias = vias_prior

    cvp_data, msg = carregar_cvp(ARQUIVO_CVP)
    if cvp_data is not None:
        st.session_state.cvp = cvp_data

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
                                       max_cameras: int = None,
                                       logs: pd.DataFrame = None) -> tuple:  # ← ADICIONAR logs como parâmetro
    
    df_pontos_minimos_usados = pd.DataFrame()
    
    if df.empty:
        return pd.DataFrame(), 0.0, True, None, set(), df_pontos_minimos_usados, 0
    
    ipe_total = df['ipe_cruz'].sum()
    if ipe_total <= 0:
        return pd.DataFrame(), 0.0, True, None, set(), df_pontos_minimos_usados, 0
    
    # ===== NOVO: Preparar dicionário de IPE total por logradouro =====
    if logs is None or logs.empty:
        # Fallback para comportamento antigo se logs não fornecido
        usar_cobertura_ajustada = False
    else:
        usar_cobertura_ajustada = True
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
        
        # Calcular IPE total por logradouro
        ipe_total_por_log = {}
        for _, cruz in df.iterrows():
            cod1, cod2 = cruz['cod_log1'], cruz['cod_log2']
            ipe = cruz['ipe_cruz']
            
            if cod1 not in ipe_total_por_log:
                ipe_total_por_log[cod1] = 0
            if cod2 not in ipe_total_por_log:
                ipe_total_por_log[cod2] = 0
            
            ipe_total_por_log[cod1] += ipe
            ipe_total_por_log[cod2] += ipe
        
        # IPE total global (soma do IPE de todos os logradouros)
        ipe_total_geral = sum(ipe_total_por_log.values())
    # ===== FIM NOVO =====
    
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
    
    # ===== CORRIGIDO: Função com regra de 15% =====
    def calcular_cobertura_ajustada_atual(ids_cobertos_atual):
        if not usar_cobertura_ajustada:
            # Fallback: cobertura simples
            ipe_coberto = sum(cruz_por_id[cid]['ipe'] for cid in ids_cobertos_atual if cid in cruz_por_id)
            return ipe_coberto / ipe_total
        
        # Calcular IPE coberto por logradouro
        ipe_coberto_por_log = {}
        for cruz_id in ids_cobertos_atual:
            if cruz_id not in cruz_por_id:
                continue
            info = cruz_por_id[cruz_id]
            ipe = info['ipe']
            cod_log1, cod_log2 = info['cod_log1'], info['cod_log2']
            
            if cod_log1 not in ipe_coberto_por_log:
                ipe_coberto_por_log[cod_log1] = 0
            if cod_log2 not in ipe_coberto_por_log:
                ipe_coberto_por_log[cod_log2] = 0
            
            ipe_coberto_por_log[cod_log1] += ipe
            ipe_coberto_por_log[cod_log2] += ipe
        
        # Aplicar regra dos 15%
        ipe_ajustado_total = 0
        for cod_log, ipe_total_log in ipe_total_por_log.items():
            if ipe_total_log <= 0:
                continue
            
            ipe_coberto = ipe_coberto_por_log.get(cod_log, 0)
            cobertura_efetiva = ipe_coberto / ipe_total_log
            
            if cobertura_efetiva >= 0.15:  # ← CORRIGIDO: 15% ao invés de 50%
                # Logradouro com ≥15% → conta como 100%
                ipe_ajustado_total += ipe_total_log
            else:
                # Logradouro com <15% → mantém cobertura atual
                ipe_ajustado_total += ipe_coberto
        
        return ipe_ajustado_total / ipe_total_geral if ipe_total_geral > 0 else 0
    # ===== FIM CORRIGIDO =====
    
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
            
            # ===== NOVO: PRESERVAR FLAG is_red =====
            is_red = ponto.get('is_red', False)
            # ===== FIM NOVO =====
            
            pontos_minimos_usados.append({
                'id_minimo': ponto.get('id_minimo', len(pontos_minimos_usados) + 1),
                'tipo': ponto.get('tipo', 'PONTO_MINIMO'),
                'logradouro': ponto.get('logradouro', ''),
                'lat': lat,
                'lon': lon,
                'prioridade': ponto.get('prioridade', 5),
                'cameras': cameras_deste_ponto,
                'is_ponto_minimo': True,
                'is_red': is_red  # ← ADICIONAR ESTA LINHA
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
        
        # Usar cobertura ajustada (regra de 15%)
        cobertura_atual = calcular_cobertura_ajustada_atual(ids_cobertos)
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
    
    # Calcular cobertura real ajustada (regra de 15%)
    cobertura_real = calcular_cobertura_ajustada_atual(ids_cobertos)
    
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
    
    # Calcular bounds do GeoJSON se disponível
    if bairros_geojson is not None:
        all_coords = []
        for feature in bairros_geojson.get('features', []):
            geom = feature.get('geometry', {})
            geom_type = geom.get('type', '')
            coords = geom.get('coordinates', [])
            
            if geom_type == 'Polygon':
                for ring in coords:
                    all_coords.extend(ring)
            elif geom_type == 'MultiPolygon':
                for polygon in coords:
                    for ring in polygon:
                        all_coords.extend(ring)
        
        if all_coords:
            lons = [c[0] for c in all_coords]
            lats = [c[1] for c in all_coords]
            
            center_lat = (min(lats) + max(lats)) / 2
            center_lon = (min(lons) + max(lons)) / 2
            
            m = folium.Map(
                location=[center_lat, center_lon],
                zoom_start=12,
                tiles='CartoDB positron',
                min_zoom=11,
                max_zoom=18,
                max_bounds=True
            )
            
            m.fit_bounds([[min(lats), min(lons)], [max(lats), max(lons)]])
        else:
            m = folium.Map(
                location=[-8.05, -34.95],
                zoom_start=12,
                tiles='CartoDB positron',
                min_zoom=11,
                max_zoom=18
            )
    else:
        m = folium.Map(
            location=[-8.05, -34.95],
            zoom_start=12,
            tiles='CartoDB positron',
            min_zoom=11,
            max_zoom=18
        )
    
    # Adicionar máscara escura FORA do Recife
    if bairros_geojson is not None:
        # Criar geometria invertida usando shapely
        from shapely.geometry import Polygon, MultiPolygon, box, shape
        from shapely.ops import unary_union
        
        # Criar um retângulo grande que cobre toda a área visível
        outer_box = box(-36.5, -9.0, -33.0, -7.5)
        
        # Extrair as geometrias dos bairros do Recife
        recife_polygons = []
        for feature in bairros_geojson.get('features', []):
            geom = shape(feature['geometry'])
            recife_polygons.append(geom)
        
        # Unir todos os polígonos do Recife em uma única geometria
        recife_union = unary_union(recife_polygons)
        
        # Subtrair Recife do retângulo grande (área fora do Recife)
        mask_geometry = outer_box.difference(recife_union)
        
        # Converter de volta para GeoJSON
        mask_geojson = {
            "type": "Feature",
            "geometry": mask_geometry.__geo_interface__
        }
        
        # Adicionar máscara ao mapa
        folium.GeoJson(
            mask_geojson,
            style_function=lambda x: {
                'fillColor': '#000000',
                'color': 'transparent',
                'weight': 0,
                'fillOpacity': 0.7
            },
            name='Máscara Externa'
        ).add_to(m)
    
    # Adicionar borda dos bairros do Recife
    if bairros_geojson is not None:
        folium.GeoJson(
            bairros_geojson,
            style_function=lambda x: {
                'fillColor': 'transparent',
                'color': '#6b7280',
                'weight': 2,
                'fillOpacity': 0
            },
            name='Limites do Recife'
        ).add_to(m)
    
    # Pontos Mínimos
    if mostrar_pontos_minimos and pontos_minimos_usados is not None and not pontos_minimos_usados.empty:
        for _, p in pontos_minimos_usados.iterrows():
            is_red = p.get('is_red', False) or (str(p.get('tipo', '')).strip().upper() == 'RED')
            
            if is_red:
                cor = "#10b981"
                titulo = "📍 PONTO RED (Concessão)"
            else:
                cor = "#f6443b"
                titulo = "📍 PONTO OBRIGATÓRIO"
            
            popup_html = f"""<div style="font-size:0.8rem; min-width:180px;">
                <strong>{titulo}</strong><br/>
                <b>Motivo:</b> {p.get('tipo', 'N/A')}<br/>
                <b>Logradouro:</b> {p.get('logradouro', 'N/A')}<br/>
                <b>Prioridade:</b> {p.get('prioridade', 'N/A')}<br/>
                <b>Câmeras:</b> {p.get('cameras', 1)}
            </div>"""
            folium.CircleMarker(
                location=[p['lat'], p['lon']], radius=3, color=cor,
                fill=True, fillColor=cor, fillOpacity=0.8, weight=2,
                popup=folium.Popup(popup_html, max_width=250)
            ).add_to(m)
    
    # Pontos via IPE
    if mostrar_pontos_ipe and not cruzamentos_selecionados.empty:
        for _, c in cruzamentos_selecionados.iterrows():
            popup_html = f"""<div style="font-size:0.8rem; min-width:180px;">
                <strong>Cruzamento {int(c['id'])}</strong><br/>
                <b>Ruas:</b> {c['log1']} x {c['log2']}<br/>
                <b>IPE:</b> {c['ipe_cruz']:.4f}<br/>
            </div>"""
            folium.CircleMarker(
                location=[c['lat'], c['lon']], radius=3, color="#3b82f6",
                fill=True, fillColor="#3b82f6", fillOpacity=0.8, weight=1,
                popup=folium.Popup(popup_html, max_width=250)
            ).add_to(m)
    
    return m


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
    carregar_arquivos_locais(incluir_red=False)

# ============================================================
# SIDEBAR - CONTROLES COM AJUSTES 1 E 2
# ============================================================
with st.sidebar:
    st.markdown("## 🎛️ Controles")
    
    nota_min_equip = 4
    
    # ===== PRIMEIRO: VERIFICAR ESTADO DO RED PARA CALCULAR MÍNIMO =====
    # Precisamos ler o estado anterior do checkbox antes de renderizar
    if 'incluir_red_anterior' not in st.session_state:
        st.session_state.incluir_red_anterior = False
    
    # ===== 1. LIMITE DE OTIMIZAÇÃO =====
    st.markdown('<div class="section-title">1. Limite de Otimização</div>', unsafe_allow_html=True)
    
    modo_limite = st.radio(
        "Escolha o modo de limite:",
        ["Quantidade de Câmeras","Cobertura Alvo (%)"],
        key='modo_limite',
        help="Cobertura Alvo: otimiza até atingir % de cobertura desejada, restrito às condições de filtros. Quantidade: limita o número total de câmeras."
    )
    
    if modo_limite == "Cobertura Alvo (%)":
        cobertura_pct = st.slider(
            "Cobertura alvo de risco otimizada (via 15%)", 
            0, 100, 80, step=10, 
            key='cobertura_alvo',
            help="Percentual de cobertura otimizada do IPE a ser atingido"
        )
        max_cameras = None
        st.markdown(f'''<div class="info-box">
            ℹ️ O otimizador buscará atingir <b>{cobertura_pct}%</b> de cobertura efetiva, restrito à distância mínima entre câmeras.
        </div>''', unsafe_allow_html=True)
    else:
        cobertura_pct = 100
        
        # ===== NOVO: DEFINIR CÂMERAS RED =====
        cameras_red = 107
        # ===== FIM NOVO =====
        
        # Usar estado anterior do RED para definir mínimo e máximo
        if st.session_state.incluir_red_anterior:
            minimo_cameras = 250  # Mínimo sem RED
            maximo_cameras = 4032 - cameras_red  # Máximo descontando RED
            valor_padrao = 500  # Padrão sem RED
            help_text = f"Limite de câmeras ALÉM das {cameras_red} RED (50% dos pontos = 3 câm, 30% = 2 câm, 20% = 1 câm). Mínimo: {minimo_cameras} câmeras"
        else:
            minimo_cameras = 250
            maximo_cameras = 4032
            valor_padrao = 500
            help_text = f"Limite total de câmeras no sistema (50% dos pontos = 3 câm, 30% = 2 câm, 20% = 1 câm). Mínimo: {minimo_cameras} câmeras"
        
        # ===== MODIFICADO: Input agora pergunta câmeras SEM contar RED =====
        max_cameras_input = st.number_input(
            "Máximo de câmeras",
            min_value=minimo_cameras,
            max_value=maximo_cameras,
            value=valor_padrao,
            step=10, 
            key='max_cameras_input',
            help=help_text
        )
        
        # ===== NOVO: CALCULAR max_cameras REAL =====
        if st.session_state.incluir_red_anterior:
            max_cameras = max_cameras_input + cameras_red  # Adiciona as 107 RED
            total_display = max_cameras
            cameras_otimizadas = max_cameras_input
        else:
            max_cameras = max_cameras_input  # Usa o valor direto
            total_display = max_cameras
            cameras_otimizadas = max_cameras
        # ===== FIM NOVO =====
        
        # Mensagem dinâmica baseada em RED
        if st.session_state.incluir_red_anterior:
            st.markdown(f'''<div class="info-box">
                ℹ️ <b>Total: {total_display} câmeras</b><br/>
                • {cameras_red} câmeras de Relógios</span><br/>
                • {cameras_otimizadas} câmeras otimizadas<br/>
                <small>Distribuição das otimizadas: 50% dos pontos com 3 câm, 30% com 2 câm, 20% com 1 câm</small>
            </div>''', unsafe_allow_html=True)
        else:
            st.markdown(f'''<div class="info-box">
                ℹ️ Limite fixo de <b>{total_display} câmeras</b><br/>
                <small>Distribuição: 50% dos pontos com 3 câm, 30% com 2 câm, 20% com 1 câm</small>
            </div>''', unsafe_allow_html=True)
    
    max_cruzamentos = None
    
    # ===== 2. DISTÂNCIA MÍNIMA =====
    st.markdown('<div class="section-title">2. Distância mínima entre câmeras</div>', unsafe_allow_html=True)
    dist_min = st.slider("Distância (m)", 200, 500, 300, step=100, key='dist_min', help="Distância mínima entre câmeras que compartilham o mesmo logradouro")
    
    raio_cobertura = 50
    raio_equipamento = 100
    limite_cob_log = None
    
    # ===== 3. CÂMERAS DE RELÓGIOS DIGITAIS =====
    st.markdown('<div class="section-title">3. Câmeras de Relógios Digitais</div>', unsafe_allow_html=True)
    incluir_red = st.checkbox(
        "Incluir câmeras de relógios digitais",
        value=st.session_state.incluir_red_anterior,  # Mantém o estado anterior
        key='incluir_red',
        help="Pontos de relógios digitais (concessão) com 1 câmera sem custo por ponto"
    )
    
    if incluir_red:
        st.markdown(f"""<div class="info-box">
            ℹ️ <b>{cameras_red} câmeras de relógios digitais</b> serão incluídas como pontos mínimos prioritários (sem custo)
        </div>""", unsafe_allow_html=True)

    # Recarregar pontos mínimos se checkbox mudou
    if incluir_red != st.session_state.incluir_red_anterior:
        st.session_state.incluir_red_anterior = incluir_red
        pontos_min, msg = carregar_pontos_minimos(ARQUIVO_PRIORIDADES, incluir_red)
        if pontos_min is not None:
            st.session_state.pontos_minimos = pontos_min
        # Forçar rerun para atualizar o mínimo de câmeras na seção 1
        st.rerun()
    
    # ===== 4. PESOS DOS EIXOS IPE =====
    st.markdown('<div class="section-title">4. Pesos dos eixos IPE</div>', unsafe_allow_html=True)
    peso_seg = st.slider("Segurança", 0, 100, 15, key='peso_seg')
    peso_lct = st.slider("Lazer, Cultura e Turismo", 0, 100, 30, key='peso_lct')
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
        pontos_min_para_usar, max_cameras,
        st.session_state.logs
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
st.markdown('<h1 class="main-header">Otimizador do Videomonitoramento - COP Recife</h1>', unsafe_allow_html=True)

if not st.session_state.cruzamentos_calculados.empty and not alvo_atingido and modo_limite == "Cobertura Alvo (%)":
    st.markdown(f"""
    <div style="background: rgba(234, 179, 8, 0.1); border-left: 4px solid #fbbf24; padding: 0.6rem 0.8rem; margin-bottom: 0.8rem; border-radius: 4px;">
        <div style="display: flex; align-items: center; gap: 0.5rem;">
            <span style="font-size: 1.2rem;">⚠️</span>
            <div style="flex: 1; font-size: 0.8rem; color: #fef3c7; line-height: 1.4;">
                <strong>Cobertura alvo de {cobertura_pct}% não atingida.</strong> 
                Cenário com máximo de {total_cameras_usado:,} câmeras possíveis, considerando a restrição de distância mínima: {dist_min}m. 
                <em>O cenário apresentado simula o número máximo de câmeras necessárias para atingir a cobertura desejada dentro da restrição de distância mínima definida. É possível que existam soluções com menos câmeras que alcancem a mesma cobertura, devido ao incremento marginal decrescente (cada nova câmera adiciona menos ganho de cobertura).</em>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

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
        
        # ===== NOVO: SEPARAR ESTATÍSTICAS RED =====
        qtd_pontos_minimos = len(df_pontos_minimos_usados) if not df_pontos_minimos_usados.empty else 0
        cameras_pontos_minimos = df_pontos_minimos_usados['cameras'].sum() if not df_pontos_minimos_usados.empty and 'cameras' in df_pontos_minimos_usados.columns else 0
        
        # Separar RED dos outros
        qtd_red = 0
        cameras_red = 0
        qtd_outros_minimos = 0
        cameras_outros_minimos = 0
        
        if not df_pontos_minimos_usados.empty and 'is_red' in df_pontos_minimos_usados.columns:
            df_red = df_pontos_minimos_usados[df_pontos_minimos_usados['is_red'] == True]
            df_outros = df_pontos_minimos_usados[df_pontos_minimos_usados['is_red'] == False]
            
            qtd_red = len(df_red)
            cameras_red = df_red['cameras'].sum() if not df_red.empty else 0
            
            qtd_outros_minimos = len(df_outros)
            cameras_outros_minimos = df_outros['cameras'].sum() if not df_outros.empty else 0
        else:
            qtd_outros_minimos = qtd_pontos_minimos
            cameras_outros_minimos = cameras_pontos_minimos
        # ===== FIM NOVO =====
        
        qtd_pontos_ipe = total_sel
        cameras_pontos_ipe = df_sel['cameras'].sum() if not df_sel.empty and 'cameras' in df_sel.columns else 0
        
        total_pontos = qtd_pontos_minimos + qtd_pontos_ipe
        total_cameras = total_cameras_usado

        custo_unitario = 1610
        # ===== NOVO: DESCONTAR CUSTO DOS PONTOS RED =====
        cameras_com_custo = total_cameras - cameras_red
        custo_total_geral = cameras_com_custo * custo_unitario
        # ===== FIM NOVO =====
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

        df_cobertos = df_calc[df_calc['id'].isin(ids_cobertos)]
        qtd_cvp_cobertos, total_cvp, logradouros_cvp_cobertos = verificar_cvp_por_logradouro(
            df_cobertos,
            st.session_state.cvp
        )
        pct_cvp = (qtd_cvp_cobertos / total_cvp * 100) if total_cvp > 0 else 0

        df_cobertos = df_calc[df_calc['id'].isin(ids_cobertos)]
        qtd_vias_cobertas, total_vias, vias_prioritarias_cobertas = verificar_vias_prioritarias_por_logradouro(
            df_cobertos,
            st.session_state.vias_prioritarias
        )
        pct_vias_prioritarias = (qtd_vias_cobertas / total_vias * 100) if total_vias > 0 else 0        

        # EXIBIR ESTATÍSTICAS
        
        # EXIBIR ESTATÍSTICAS
        st.markdown("#### 📊 Pontos e Câmeras")
        
        stats_html = f"""<div class="stat-box">
            <div class="stat-row"><span>Total de pontos disponíveis:</span><span class="stat-value">{total_cruz:,}</span></div>"""
        
        # ===== NOVO: MOSTRAR RED SEPARADAMENTE =====
        if qtd_outros_minimos > 0:
            stats_html += f"""
            <div class="stat-row"><span>Pontos mínimos (COP):</span><span class="stat-value">{qtd_outros_minimos:,} pts ({int(cameras_outros_minimos)} câm)</span></div>"""
        
        if qtd_red > 0:
            stats_html += f"""
            <div class="stat-row"><span>Pontos Relógios Digitais:</span><span class="stat-value">{qtd_red:,} pts ({int(cameras_red)} câm)</span></div>"""
                
        # ===== FIM NOVO =====
        
        stats_html += f"""
            <div class="stat-row"><span>Pontos otimizados:</span><span class="stat-value">{qtd_pontos_ipe:,} pts ({int(cameras_pontos_ipe)} câm)</span></div>
            <div class="stat-row"><span><b>Total de pontos:</b></span><span class="stat-value" style="font-size: 1.1rem;">{total_pontos:,}</span></div>
            <div class="stat-row"><span><b>Total de câmeras:</b></span><span class="stat-value" style="font-size: 1.1rem;">{total_cameras:,}</span></div>"""
        
        # ===== NOVO: MOSTRAR CÂMERAS SEM CUSTO =====
        if qtd_red > 0:
            stats_html += f"""
            <div class="stat-row"><span>• Com custo:</span><span class="stat-value">{int(cameras_com_custo)} câm</span></div>
            <div class="stat-row"><span>• Sem custo (Relógios):</span><span class="stat-value">{int(cameras_red)} câm</span></div>"""
        # ===== FIM NOVO =====
        
        stats_html += f"""
            <div class="stat-row"><span><b>Câmeras por 10 mil hab.:</b></span><span class="stat-value" style="font-size: 1.1rem;">{total_cameras/158.8376:.0f}</span></div>
            <div class="stat-row" style="margin-top: 5px; font-size: 1rem;"><span><b>Custo Total:</b></span><span class="stat-value" style="color: #4ade80;">{custo_formatado}</span></div>"""
        
        st.markdown(stats_html, unsafe_allow_html=True)

        st.markdown("#### 🏙️ Cobertura Pontos Prioritários")
        st.markdown(f"""<div class="stat-box">
            <div class="stat-row"><span>Parques, Praças, Teatros, etc:</span><span class="stat-value">{pct_equipamentos:.1f}%</span></div>
            <div class="stat-row"><span>Mercados e Feiras:</span><span class="stat-value">{pct_comercial:.1f}%</span></div>
            <div class="stat-row"><span>Pontos de Alagamentos:</span><span class="stat-value">{pct_alagamentos:.1f}%</span></div>
            <div class="stat-row"><span>Pontos de Sinistros:</span><span class="stat-value">{pct_sinistros:.1f}%</span></div>
            <div class="stat-row"><span>Crimes Contra Patrimônio:</span><span class="stat-value">{pct_cvp:.1f}%</span></div>
            <div class="stat-row"><span>Vias Prioritárias:</span><span class="stat-value">{pct_vias_prioritarias:.1f}%</span></div>
        </div>""", unsafe_allow_html=True)

        st.markdown("#### 📈 Cobertura Risco IPE")

        st.markdown("""
        <style>
        .tooltip {
        position: relative;
        display: inline-block;
        cursor: help;
        }
        .tooltip .tooltiptext {
        visibility: hidden;
        width: 260px;
        background-color: #1f2937;
        color: #f9fafb;
        text-align: left;
        border-radius: 8px;
        padding: 10px;
        position: absolute;
        z-index: 1;
        bottom: 125%;
        left: 50%;
        transform: translateX(-50%);
        opacity: 0;
        transition: opacity 0.3s;
        font-size: 0.8rem;
        }
        .tooltip:hover .tooltiptext {
        visibility: visible;
        opacity: 1;
        }
        </style>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="stat-box">
        <div class="stat-row">
        <span>
        Cobertura de risco otimizada (via 50%)
        <span class="tooltip"> 🛈
        <span class="tooltiptext">
        A cobertura de risco otimizada adota o critério de que, uma vez que uma rua atinja 50% de cobertura do seu risco, ela passa a ser considerada como totalmente coberta (100%). Por conta dessa lógica, diferentes cenários com quantidades distintas de câmeras podem resultar em níveis idênticos de cobertura. Isso ocorre porque câmeras adicionais podem estar sendo alocadas justamente em ruas que já ultrapassaram o limiar de 50% de cobertura, não gerando aumento efetivo no indicador final.
        </span>
        </span>
        </span>
        <span class="stat-value" style="color: #4ade80;">{cobertura_ajustada_total:.1f}%</span>
        </div>
        <div class="stat-row"><span>Segurança:</span><span class="stat-value">{cobertura_ajustada_eixos['seg']:.1f}%</span></div>
        <div class="stat-row"><span>Lazer, Cultura e Turismo:</span><span class="stat-value">{cobertura_ajustada_eixos['lct']:.1f}%</span></div>
        <div class="stat-row"><span>Comercial:</span><span class="stat-value">{cobertura_ajustada_eixos['com']:.1f}%</span></div>
        <div class="stat-row"><span>Mobilidade:</span><span class="stat-value">{cobertura_ajustada_eixos['mob']:.1f}%</span></div>
        </div>
        """, unsafe_allow_html=True)




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

col_equip_lct, col_equip_com, col_alag = st.columns(3)

col_sinist, col_cvp, col_vias = st.columns(3)

# =============================================================================
# 🏢 EQUIPAMENTOS (linha ~1457)
# =============================================================================
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
            total_tipos = len(equipamentos_lct_seg)
            
            for nome, qtd in equipamentos_lct_seg:
                if nome and str(nome).strip() != "":
                    html_main += f'<div class="stat-row"><span>{nome}:</span><span class="stat-value">{qtd}</span></div>'
            
            st.markdown(f"#### 🏢 Equipamentos")
            st.markdown(f"""<div class="stat-box" style="margin-bottom: 1rem;">
                <div class="stat-row" style="border-bottom: 1px solid rgba(148, 163, 184, 0.3); padding-bottom: 5px; margin-bottom: 5px;">
                    <span><b>Cobertura:</b></span><span class="stat-value">{total_lct_seg} equipamentos ({pct_lct_seg:.1f}%)</span>
                </div>
                <div style="font-size: 0.7rem; color: #64748b; margin-bottom: 5px;">
                    {total_equipamentos_lct_seg} equipamentos totais mapeados • Mostrando {total_tipos} tipos
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
                    {total_equipamentos_lct_seg} equipamentos totais mapeados.
                </div>
                <div class="stat-row"><span>Nenhum equipamento LCT/SEG próximo.</span></div>
            </div>""", unsafe_allow_html=True)
    else:
        st.markdown("#### 🏢 Equipamentos")
        st.markdown("""<div class="stat-box"><div class="stat-row"><span>Carregue os dados.</span></div></div>""", unsafe_allow_html=True)

# =============================================================================
# 🏪 COMERCIAL (linha ~1500)
# =============================================================================
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
            total_tipos = len(equipamentos_com)
            
            for nome, qtd in equipamentos_com:
                if nome and str(nome).strip() != "":
                    html_com += f'<div class="stat-row"><span>{nome}:</span><span class="stat-value">{qtd}</span></div>'
            
            st.markdown(f"#### 🏪 Comercial")
            st.markdown(f"""<div class="stat-box" style="margin-bottom: 1rem;">
                <div class="stat-row" style="border-bottom: 1px solid rgba(148, 163, 184, 0.3); padding-bottom: 5px; margin-bottom: 5px;">
                    <span><b>Cobertura:</b></span><span class="stat-value">{total_com} equipamentos ({pct_com:.1f}%)</span>
                </div>
                <div style="font-size: 0.7rem; color: #64748b; margin-bottom: 5px;">
                    {total_equipamentos_com} equipamentos totais mapeados • Mostrando {total_tipos} tipos
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
                    {total_equipamentos_com} equipamentos totais mapeados.
                </div>
                <div class="stat-row"><span>Nenhum equipamento Comercial próximo.</span></div>
            </div>""", unsafe_allow_html=True)
    else:
        st.markdown("#### 🏪 Comercial")
        st.markdown("""<div class="stat-box"><div class="stat-row"><span>Carregue os dados.</span></div></div>""", unsafe_allow_html=True)

# =============================================================================
# 🌊 ALAGAMENTOS (linha ~1543)
# =============================================================================
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
            from collections import Counter
            alagamentos_agrupados = Counter(alagamentos_encontrados)
            
            alagamentos_ordenados = sorted(
                alagamentos_agrupados.items(), 
                key=lambda x: (-x[1], x[0])
            )
            
            for alag_nome, qtd in alagamentos_ordenados:
                alag_display = alag_nome if len(alag_nome) <= 50 else alag_nome[:47] + "..."
                html_alagamentos += f'<div class="stat-row" style="justify-content: space-between;"><span style="color:#fbbf24; font-size: 0.7rem;">⚠️ {alag_display}</span><span class="stat-value" style="font-size: 0.7rem;">{qtd}</span></div>'
        else:
            html_alagamentos = '<div class="stat-row"><span>Nenhum ponto de alagamento.</span></div>'
        
        st.markdown("#### 🌊 Alagamentos")
        st.markdown(f"""<div class="stat-box">
            <div class="stat-row" style="border-bottom: 1px solid rgba(148, 163, 184, 0.3); padding-bottom: 5px; margin-bottom: 5px;">
                <span><b>Cobertura:</b></span><span class="stat-value">{qtd_alag} pontos ({pct_alag:.1f}%)</span>
            </div>
            <div style="font-size: 0.7rem; color: #64748b; margin-bottom: 5px;">
                {total_alvos_alagamento} pontos totais mapeados
            </div>
            <div style="max-height: 150px; overflow-y: auto; padding-right: 5px; font-size: 0.75rem;">
                {html_alagamentos}
            </div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown("#### 🌊 Alagamentos")
        st.markdown("""<div class="stat-box"><div class="stat-row"><span>Carregue os dados.</span></div></div>""", unsafe_allow_html=True)

# =============================================================================
# 🚗 SINISTROS (linha ~1586)
# =============================================================================
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
            
            # Ordenar por quantidade de sinistros (decrescente)
            logradouros_ordenados = sorted(
                [(rua, sinistros_dict.get(rua, 0)) for rua in logradouros_encontrados],
                key=lambda x: -x[1]
            )
            
            for rua, qtd_nesta_rua in logradouros_ordenados:
                rua_display = rua if len(rua) <= 50 else rua[:47] + "..."
                html_sinistros += f'<div class="stat-row" style="justify-content: space-between;"><span style="color:#f87171; font-size: 0.7rem;">🚗 {rua_display}</span><span class="stat-value" style="font-size: 0.7rem;">{qtd_nesta_rua}</span></div>'
        else:
            html_sinistros = '<div class="stat-row"><span>Nenhuma rua com sinistros.</span></div>'
        
        st.markdown("#### 🚗 Sinistros")
        st.markdown(f"""<div class="stat-box">
            <div class="stat-row" style="border-bottom: 1px solid rgba(148, 163, 184, 0.3); padding-bottom: 5px; margin-bottom: 5px;">
                <span><b>Cobertura:</b></span><span class="stat-value">{qtd_sinistros_cobertos}/{total_sinistros} sinistros ({pct_sinist:.1f}%)</span>
            </div>
            <div style="font-size: 0.7rem; color: #64748b; margin-bottom: 5px;">
                {qtd_ruas} de {total_ruas} ruas cobertas
            </div>
            <div style="max-height: 150px; overflow-y: auto; padding-right: 5px; font-size: 0.75rem;">
                {html_sinistros}
            </div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown("#### 🚗 Sinistros")
        st.markdown("""<div class="stat-box"><div class="stat-row"><span>Carregue os dados.</span></div></div>""", unsafe_allow_html=True)

# =============================================================================
# 🚨 CVP
# =============================================================================
with col_cvp:
    if not st.session_state.cruzamentos_calculados.empty and not st.session_state.cvp.empty:
        df_todos_cobertos = st.session_state.cruzamentos_calculados[
            st.session_state.cruzamentos_calculados['id'].isin(ids_cobertos)
        ]
        
        qtd_cvp_cobertos, total_cvp, logradouros_cvp_encontrados = verificar_cvp_por_logradouro(
            df_todos_cobertos,
            st.session_state.cvp
        )
        
        qtd_ruas_cvp = len(logradouros_cvp_encontrados)
        total_ruas_cvp = len(st.session_state.cvp)
        pct_cvp = (qtd_cvp_cobertos / total_cvp * 100) if total_cvp > 0 else 0
        
        html_cvp = ""
        if logradouros_cvp_encontrados:
            cvp_dict = {}
            for _, row in st.session_state.cvp.iterrows():
                log_norm = str(row['logradouro']).strip().upper()
                qtd = int(row.get('cvp', 0))
                cvp_dict[log_norm] = qtd
            
            # Ordenar por quantidade de CVP (decrescente)
            logradouros_ordenados = sorted(
                [(rua, cvp_dict.get(rua, 0)) for rua in logradouros_cvp_encontrados],
                key=lambda x: -x[1]
            )
            
            for rua, qtd_cvp_nesta_rua in logradouros_ordenados:
                rua_display = rua if len(rua) <= 50 else rua[:47] + "..."
                html_cvp += f'<div class="stat-row" style="justify-content: space-between;"><span style="color:#fca5a5; font-size: 0.7rem;">🚨 {rua_display}</span><span class="stat-value" style="font-size: 0.7rem;">{qtd_cvp_nesta_rua}</span></div>'
        else:
            html_cvp = '<div class="stat-row"><span>Nenhuma rua com CVP.</span></div>'
        
        st.markdown("#### 🚨 CVP")
        st.markdown(f"""<div class="stat-box">
            <div class="stat-row" style="border-bottom: 1px solid rgba(148, 163, 184, 0.3); padding-bottom: 5px; margin-bottom: 5px;">
                <span><b>Cobertura:</b></span><span class="stat-value">{qtd_cvp_cobertos}/{total_cvp} crimes ({pct_cvp:.1f}%)</span>
            </div>
            <div style="font-size: 0.7rem; color: #64748b; margin-bottom: 5px;">
                {qtd_ruas_cvp} de {total_ruas_cvp} ruas cobertas
            </div>
            <div style="max-height: 150px; overflow-y: auto; padding-right: 5px; font-size: 0.75rem;">
                {html_cvp}
            </div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown("#### 🚨 CVP")
        st.markdown("""<div class="stat-box"><div class="stat-row"><span>Carregue os dados.</span></div></div>""", unsafe_allow_html=True)

# =============================================================================
# 🛣️ VIAS PRIORITÁRIAS
# =============================================================================
with col_vias:
    if not st.session_state.cruzamentos_calculados.empty and not st.session_state.vias_prioritarias.empty:
        df_todos_cobertos = st.session_state.cruzamentos_calculados[
            st.session_state.cruzamentos_calculados['id'].isin(ids_cobertos)
        ]
        
        qtd_vias_cobertas, total_vias, vias_encontradas = verificar_vias_prioritarias_por_logradouro(
            df_todos_cobertos,
            st.session_state.vias_prioritarias
        )
        
        pct_vias = (qtd_vias_cobertas / total_vias * 100) if total_vias > 0 else 0
        
        html_vias = ""
        if vias_encontradas:
            for via, prioridade in vias_encontradas:
                via_display = via if len(via) <= 50 else via[:47] + "..."
                html_vias += f'<div class="stat-row" style="justify-content: space-between;"><span style="color:#93c5fd; font-size: 0.7rem;">🛣️ {via_display}</span></div>'
        else:
            html_vias = '<div class="stat-row"><span>Nenhuma via prioritária coberta.</span></div>'
        
        st.markdown("#### 🛣️ Vias Prioritárias")
        st.markdown(f"""<div class="stat-box">
            <div class="stat-row" style="border-bottom: 1px solid rgba(148, 163, 184, 0.3); padding-bottom: 5px; margin-bottom: 5px;">
                <span><b>Cobertura:</b></span><span class="stat-value">{qtd_vias_cobertas}/{total_vias} vias ({pct_vias:.1f}%)</span>
            </div>
            <div style="font-size: 0.7rem; color: #64748b; margin-bottom: 5px;">
                Vias prioritárias cobertas
            </div>
            <div style="max-height: 150px; overflow-y: auto; padding-right: 5px; font-size: 0.75rem;">
                {html_vias}
            </div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown("#### 🛣️ Vias Prioritárias")
        st.markdown("""<div class="stat-box"><div class="stat-row"><span>Carregue os dados.</span></div></div>""", unsafe_allow_html=True)