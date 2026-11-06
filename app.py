import base64
import re
import unicodedata
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Investigación UNVM - IAPCH",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def local_css(file_name):
    base = Path(__file__).parent
    for ruta in (base / file_name, base / ".streamlit" / file_name):
        if ruta.exists():
            st.markdown(f"<style>{ruta.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)
            return
    st.warning(f"No se encontró {file_name} en {base} ni en {base / '.streamlit'}")


def logo_base64(ruta):
    try:
        return base64.b64encode(Path(ruta).read_bytes()).decode()
    except Exception:
        return None


local_css("styles.css")

SHEET_ID = "1J6Sjjrty8verBOAZLYrqxkicoB12PkM6f4ykvPKNDCo"
GID = "1761185783"
url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&gid={GID}"

MAPA_PEIDI_URL = "https://mapa-adoptantes-peidi.vercel.app/"

PROGRAMAS_BASE = {
    "GF": r"(?<![A-Za-z-])GF(?![A-Za-z])",
    "PIC": r"(?<![A-Za-z-])PIC(?![A-Za-z])",
    "PEIDI": r"(?<![A-Za-z-])PEIDI(?![A-Za-z])",
    "PICTOS": r"PICTOS",
    "Cs. Productiva": r"Cs\.?\s*Productiva",
}
LINEAS = {
    "Salud": ("🟢", r"Salud"),
    "Arte": ("🟣", r"Arte"),
    "Educación": ("🟡", r"Educaci[oó]n"),
    "Ciencia de Datos": ("🔵", r"Ciencia\s*de\s*Datos|Datos"),
}

SERVICIOS_LABS = {
    "LAB SALUD": {
        "LABORATORIO EN INTELIGENCIA SANITARIA: VIGILANCIA EPIDEMIOLÓGICA Y SALUD COMUNITARIA": [
            "Consultoría científico-técnica para el diseño, monitoreo y evaluación de políticas, programas y servicios de salud y salud mental con enfoque de derechos.",
            "Análisis espacio-temporal y georreferenciación de eventos de salud.",
            "Sistemas de alerta temprana y seguimiento de trayectorias de cuidados.",
            "Elaboración de informes y boletines epidemiológicos.",
            "Diseño de indicadores y evaluación de procesos de adecuación de servicios y desinstitucionalización en el campo de la salud mental.",
            "Diagnósticos comunitarios e investigación con metodologías participativas.",
            "Capacitación y asesoramiento técnico a equipos de salud."
        ],
        "TECNOLOGÍA FARMACÉUTICA Y MEDICINAL": [
            "Diseño y caracterización de sistemas terapéuticos.",
            "Estudios de estabilidad, degradación, cuantificación de principios activos.",
            "Análisis computacional de interacciones proteína-ligando.",
            "Asesoramiento en procesos farmacotécnicos.",
            "Apoyo en estudios de compuestos naturales y reposicionados."
        ],
        "SALUD, AMBIENTE Y SUSTENTABILIDAD": [
            "Capacitación y asesoramiento técnico en Salud y toxicología ambiental",
            "Caracterización geopedológica (STAN)",
            "Planificación forestal geoambiental (STAN)",
            "Seminario sobre Tecnologías constructivas y modalidades productivas para vivienda (STAN)",
            "Curso sobre Diseño y materiales sustentables (STAN)",
            "Capacitación y transferencia para la elaboración de paneles de cáscaras de maní (STAN)",
            "Asesoramiento en el uso y aplicaciones de placas de cáscaras de maní (STAN)",
            "Asesoramiento, capacitación y monitoreo para el diseño sustentable de viviendas (STAN)",
            "Curso sobre metodología de la investigación-experimentación y aplicación de tecnologías para arquitectura sustentable (STAN)",
            "Curso sobre Marco Lógico de Programación de la Acción en Investigación Científica y Tecnológica (para arquitectos) (STAN)",
            "Estudio para determinar la viabilidad técnica para la elaboración de placas aglomeradas a partir de semillas de algodón subproducto de la industria algodonera (STAN)",
            "Asesoramiento para el diseño y organización de programas de especialización en Tecnología de la Arquitectura (STAN)"
        ],
        "DEPORTE Y SALUD": [
            "Laboratorio de pruebas funcionales",
            "Estudios médicos deportivos (en la comunidad universitaria y en la población en general)",
            "Estudios de medicina del deporte",
            "Asistencia sanitaria en eventos deportivos",
            "Asistencia sanitaria a clubes deportivos",
            "Consultoría y/o capacitación científica – técnica"
        ]
    },
    "LAB CIENCIA DE DATOS": {
        "ÁREA DE CIENCIA DE DATOS Y ANALÍTICA": [
            "Metodológico: diagnóstico de necesidades, diseño del plan de análisis y lineamientos de validez, trazabilidad y reproducibilidad.",
            "Analítica y modelado: asesoramiento en la selección y aplicación de herramientas de análisis estadístico, y en el desarrollo e implementación de modelos estadísticos e IA.",
            "Gestión e integración de datos: asesoramiento en relevamiento, estandarización, control de calidad y resguardo de la información."
        ]
    },
    "LAB ARTE": {
        "LITERATURA, LENGUAS Y PATRIMONIO": [
            "Curaduría textual",
            "Catalogación y análisis de colecciones y archivos",
            "Digitalización y sistematización de colecciones y archivos"
        ],
        "TECNOLOGÍAS Y FORMATOS AUDIOVISUALES EMERGENTES": [
            "Curaduría de producciones para catálogos especializados",
            "Mapeos de producción artística en escenarios específicos",
            "Producciones audiovisuales en escenarios emergentes con tecnologías multiplataformas",
            "Asesoramiento especializado a polos emergentes"
        ]
    },
    "LAB EDUCACIÓN": {
        "INNOVACIÓN EDUCATIVA. SIMULACIÓN EN EDUCACIÓN EN SALUD": [
            "Asesoramiento en diseño de experiencias basadas en simulación: Incluye escenarios simulados y/o talleres de habilidades.",
            "Disponibilidad de múltiples simuladores: Diseñados para el desarrollo de enseñanza basada en simulación clínica.",
            "Salas de simulación con cámara Gesell: También cuenta con salas de taller de habilidades y salas de debriefing, brindando un entorno integral para la formación basada en experiencias inmersivas para el aprendizaje."
        ],
        "TECNOLOGÍA EDUCATIVA": [
            "Asesoramiento en implementación de entornos virtuales en educación formal y no formal.",
            "Asesoramiento, planificación y desarrollo de estrategias de internacionalización pedagógica (Cursos y clases espejo).",
            "Análisis de contenido y evaluación de puesta en acto de dispositivos de innovación tecnológica en educación.",
            "Producción de materiales específicos para incorporación de TIC en actividades disciplinares.",
            "Formación pedagógica especializada en experiencias educativas a distancia.",
            "Desarrollo de experiencias de escritura colaborativa mediadas por tecnologías digitales."
        ]
    }
}

VINCULOS_INSTITUCIONALES = {
    "Académicos e Institucionales": [
        "Centros CONICET", "Universidades Nacionales", "Laboratorios privados con interés científico",
        "Grupos de investigación en tecnología farmacéutica", "Vinculación tecnológica y transferencia digital",
        "UNRC", "Università degli Studi di Milano Statale", "Washington University in St. Louis",
        "Universidad de la República", "Universidad Nacional Autónoma de México", "Universidad Federal de Minas Gerais",
        "Red Universitaria de Prof. de Educación Física", "RAILEES", "PEUAM – UNVM", "UNLP", "UNC", "UNER",
        "UFRGS (Brasil)", "Red Argentina de Instituciones Lectoras y Escritores en Ed. Superior"
    ],
    "Gubernamentales y Municipios": [
        "Organizaciones de usuarios, usuarias y familiares", "Cooperativas y emprendimientos de la economía social",
        "Organizaciones territoriales", "Colectivos de arte y salud mental", "Centros deportivos y de recreación",
        "Municipalidad de Villa María", "Municipalidad de Villa Nueva", "Municipalidad de Idiazábal",
        "Municipalidad de Villa Ascasubi", "Municipalidad de Hernando", "Comunidad Regional San Martín"
    ],
    "Instituciones del sistema de salud": [
        "Municipios", "Hospitales regionales", "Dependencias gubernamentales", "Clínicas privadas",
        "Laboratorios de análisis clínicos públicos y privados", "Obras sociales",
        "Centros públicos y/o privados de productos farmacéuticos", "Laboratorios de Especialidades Medicinales"
    ],
    "Organismos nacionales e internacionales": [
        "OPS", "OMS", "Ministerios de Salud", "SENASA", "INTA", "SIBSA", "RETOXLAC", "ATA"
    ],
    "Culturales, Tecnológicos, Sociales y Museos": [
        "Fundación San José", "Fundación Vía Libre", "Pilgrims Games Studio",
        "Empresas de Idiazábal: Bionutrir, Menzio, Ortega, Olivero", "Museo del Cuarteto (Agencia Córdoba Cultura)",
        "Museo Bonfiglioli", "Biblioteca Margarita Liendo", "Orquesta Filarmónica del Centro del País",
        "Arde, Asociación Qumanta Huasi, Sensoteca S.A.S."
    ],
    "Educación (Primaria, Secundaria y Terciario)": [
        "Instituciones Educativas de Nivel Primario, Secundario y Terciario de Villa María y Villa Nueva",
        "Instituto José María Paz de Idiazábal", "Inst. Sec. Bernardino Rivadavia", "IPEM 147 Manuel Anselmo Ocampo"
    ]
}

EQUIPAMIENTO_LABS = {
    "LAB EDUCACIÓN Y SALUD": [
        {"nombre": "Anatomage Table", "desc": "Disección virtual y visualización de anatomía 3D.", "foto": "assets/EQUIPOS/anatomage_table.jpg"},
        {"nombre": "CAE ARES", "desc": "Maniquí de atención de emergencia.", "foto": "assets/EQUIPOS/cae_ares.jpg"},
        {"nombre": "Simulador Pediátrico", "desc": "Simulador avanzado multipropósito Mike/Michelle.", "foto": "assets/EQUIPOS/simulador_pediatrico.jpg"},
        {"nombre": "Simulador Clinical Chloe", "desc": "Simulador de paciente para enfermería.", "foto": "assets/EQUIPOS/simulador_clinical_chloe.jpg"},
        {"nombre": "Noelle® Simulador de Parto", "desc": "Maniquí con bebé articulado en parto y placenta.", "foto": "assets/EQUIPOS/noelle_simulador_de_parto.jpg"},
        {"nombre": "Simulador Geriátrico Teri", "desc": "Cuidado de pacientes ancianos.", "foto": "assets/EQUIPOS/simulador_geriatrico_teri.jpg"},
        {"nombre": "4 Torsos de RCP BasicBilly", "desc": "Kit de actualización de CPR directa.", "foto": "assets/EQUIPOS/4_torsos_de_rcp_basicbilly.jpg"},
        {"nombre": "3 Entrenadores de Sutura", "desc": "Práctica de sutura en extremidades.", "foto": "assets/EQUIPOS/3_entrenadores_de_sutura.jpg"},
        {"nombre": "3 Brazos de Entrenamiento Venoso", "desc": "Venopunción y administración IV.", "foto": "assets/EQUIPOS/3_brazos_de_entrenamiento_venoso.jpg"}
    ],
    "LAB SALUD Y CIENCIA DE DATOS": [
        {"nombre": "Instrumentos de Evaluación Diagnóstica", "desc": "Perfiles diagnósticos.", "foto": "assets/EQUIPOS/instrumentos_de_evaluacion_diagnostica.jpg"},
        {"nombre": "Servidores y Sistemas de Datos", "desc": "Reuniones virtuales y bases de datos.", "foto": "assets/EQUIPOS/computadoras_para_reuniones_virtuales.jpg"},
        {"nombre": "Equipamiento de Laboratorio Químico", "desc": "Balanza, HPLC, campanas de flujo.", "foto": "assets/EQUIPOS/balanza_medidor_de_ph_campanas.jpg"},
        {"nombre": "Aparatología Ambiental", "desc": "Material particulado y EPP.", "foto": "assets/EQUIPOS/aparatologia_para_material_particulado.jpg"},
        {"nombre": "Workstations y Software", "desc": "PC y software Stata/InfoStat.", "foto": "assets/EQUIPOS/pc_box_docente_impresora.jpg"},
        {"nombre": "Notebook GIGABYTE AERO 16", "desc": "Intel Core i7, 32GB RAM, RTX 3060P.", "foto": "assets/EQUIPOS/notebook_gigabyte_aero_16.jpg"},
        {"nombre": "Monitor Samsung F350 Flat 27\"", "desc": "Modelo 271350fhl - CIT-VM.", "foto": "assets/EQUIPOS/monitor_samsung_f350_flat_27.jpg"},
        {"nombre": "CPU Intel Core i5 / RX580", "desc": "CPU i5-12400, RX580 8GB.", "foto": "assets/EQUIPOS/cpu_intel_core_i5_12400.jpg"}
    ],
    "LAB ARTE": [
        {"nombre": "Cámaras y Lentes UNVM", "desc": "Lic. en Diseño y Producción Audiovisual.", "foto": "assets/EQUIPOS/camaras_y_lentes_de_la_lic_en_diseno.jpg"},
        {"nombre": "Micrófonos Corbateros y Boom UNVM", "desc": "Captura de audio profesional.", "foto": "assets/EQUIPOS/microfonos_corbateros_y_boom.jpg"},
        {"nombre": "Miniproyector Videomapping PEIDI", "desc": "Videomapping equipo PEIDI.", "foto": "assets/EQUIPOS/miniproyector_para_videomapping.jpg"},
        {"nombre": "Equipamiento de Post-producción", "desc": "Software y edición propia.", "foto": "assets/EQUIPOS/equipamiento_de_post_produccion.jpg"},
        {"nombre": "Cámara 360º y Lentes Meta Quest", "desc": "Subsecretaría de Cultura Villa María.", "foto": "assets/EQUIPOS/camara_360.jpg"},
        {"nombre": "Lentes Metaquest 360º", "desc": "Realidad inmersiva.", "foto": "assets/EQUIPOS/lentes_metaquest_360.jpg"},
        {"nombre": "Tablets y Auriculares de Cultura", "desc": "Préstamo de Cultura.", "foto": "assets/EQUIPOS/tablets_y_auriculares.jpg"},
        {"nombre": "Proyector IAPCH UNVM", "desc": "Proyector institucional.", "foto": "assets/EQUIPOS/proyector_iapch_unvm.jpg"},
        {"nombre": "Grabador Zoom H6", "desc": "Audio digital profesional.", "foto": "assets/EQUIPOS/zoom_h6.jpg"},
        {"nombre": "Micrófono ME64", "desc": "Micrófono con cable canon.", "foto": "assets/EQUIPOS/microfono_me64.jpg"},
        {"nombre": "Pistola Sennheiser MZS 20-1", "desc": "Soporte de suspensión.", "foto": "assets/EQUIPOS/pistola_sennheiser_mzs_20_1.jpg"},
        {"nombre": "Kit Zeppelin", "desc": "Antiviento para exteriores.", "foto": "assets/EQUIPOS/kit_zeppelin.jpg"},
        {"nombre": "Corbatero Inalámbrico Sennheiser", "desc": "EW100 G3 y caña.", "foto": "assets/EQUIPOS/corbatero_inalambrico_sennheiser_ew100_g3.jpg"}
    ]
}


@st.cache_data(ttl=600)
def load_data():
    try:
        df = pd.read_csv(url)
        df.columns = df.columns.str.strip()
        return df
    except Exception:
        return None


def buscar_columna(df, claves):
    for c in df.columns:
        if any(k in c.upper() for k in claves):
            return c
    return None


def contiene(serie, patron):
    return serie.astype(str).str.contains(patron, case=False, regex=True, na=False)


def texto_por_fila(df):
    return df.fillna("").astype(str).agg(" ".join, axis=1)


def sin_tildes(texto):
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()


def sin_tildes_serie(serie):
    return serie.astype(str).str.normalize("NFKD").str.encode("ascii", "ignore").str.decode("utf-8")


def reset_filtros():
    st.session_state.f_prog = None
    st.session_state.f_linea = None
    st.session_state.f_texto = ""


def stat(num, label):
    return f"<div class='stat'><div class='num'>{num}</div><div class='lbl'>{label}</div></div>"


@st.dialog("Detalle completo del proyecto", width="large")
def mostrar_modal_detalle(row_dict):
    st.markdown("### 📋 Información institucional y técnica")
    st.write("A continuación se detallan todos los campos registrados para este proyecto:")
    st.markdown("---")
    
    cols = st.columns(2)
    items = list(row_dict.items())
    mitad = (len(items) + 1) // 2
    
    for i, (k, v) in enumerate(items):
        col_idx = 0 if i < mitad else 1
        with cols[col_idx]:
            val_str = str(v) if pd.notna(v) and str(v).strip() != "" else "-"
            st.markdown(f"**{k}:**")
            st.markdown(f"<p style='color: var(--muted); margin-top: -4px;'>{val_str}</p>", unsafe_allow_html=True)
            
    st.markdown("---")
    if st.button("Cerrar ventana", use_container_width=True):
        st.rerun()


df = load_data()
if "page" not in st.session_state:
    st.session_state.page = "inicio"

# ==========================================
# INICIO
# ==========================================
if st.session_state.page == "inicio":
    st.write("")
    izq, der = st.columns([3, 2], gap="large", vertical_alignment="center")

    with izq:
        try:
            st.image("assets/UNVMHum.png", width=230)
        except Exception:
            pass
        st.markdown(
            "<p class='instituto'>Instituto Académico Pedagógico de Ciencias Humanas</p>"
            "<h1 class='display'>Investigación<br>UNVM</h1>"
            "<div class='tri'></div>"
            "<p class='lead'>Todos los proyectos de investigación, servicios científicos tecnológicos, equipamiento y vínculos institucionales en un solo lugar.</p>",
            unsafe_allow_html=True,
        )
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("Ver proyectos", type="primary", use_container_width=True):
                st.session_state.page = "datos"
                st.rerun()
        with col_btn2:
            if st.button("Servicios, Equipamiento y Vínculos", type="primary", use_container_width=True):
                st.session_state.page = "servicios"
                st.rerun()

        if df is not None and not df.empty:
            col_origen = "ORIGEN" if "ORIGEN" in df.columns else df.columns[-1]
            total_sin_ipeidi = len(df) - int(contiene(df[col_origen], r"I-PEIDI").sum())
            
            st.write("")
            st.write("")
            a, b, _ = st.columns([1, 1, 1])
            a.markdown(stat(total_sin_ipeidi, "proyectos registrados"), unsafe_allow_html=True)
            b.markdown(stat(len(PROGRAMAS_BASE), "programas"), unsafe_allow_html=True)

    with der:
        try:
            st.image("assets/INVEST.png", width=460)
        except Exception:
            pass

# ==========================================
# DATOS (PROYECTOS)
# ==========================================
elif st.session_state.page == "datos":
    logo_inv = logo_base64(Path(__file__).parent / "assets" / "INVEST.png")
    if logo_inv:
        st.markdown(
            f'<img src="data:image/png;base64,{logo_inv}" class="invest-watermark" alt="Investigación UNVM">',
            unsafe_allow_html=True
        )

    top_izq, top_der = st.columns([2, 1], vertical_alignment="center")
    with top_izq:
        c_i1, c_i2 = st.columns(2)
        if c_i1.button("← Inicio"):
            st.session_state.page = "inicio"
            st.rerun()
        if c_i2.button("🛠️ Servicios y Equipamiento"):
            st.session_state.page = "servicios"
            st.rerun()
            
    with top_der:
        if st.session_state.get("f_prog") == "PEIDI":
            logo = logo_base64(Path(__file__).parent / "assets" / "LOGO-PEIDI.jpeg")
            img_logo = f'<img src="data:image/jpeg;base64,{logo}" alt="PEIDI">' if logo else ""
            
            st.markdown(
                f'''
                <div style="display: flex; flex-direction: column; align-items: flex-end; gap: 8px; width: 100%;">
                    <div class="btn-mapa-wrap" style="width: 100%;">
                        <a class="btn-mapa" href="{MAPA_PEIDI_URL}" target="_blank" rel="noopener" style="width: 100%; justify-content: center;">
                            {img_logo}<span>Mapa de adoptantes ↗</span>
                        </a>
                    </div>
                </div>
                ''',
                unsafe_allow_html=True,
            )
            
            if st.button("⚡ Ver proyectos I-PEIDI", type="secondary", use_container_width=True):
                st.session_state.f_prog = "I-PEIDI"
                st.rerun()

    st.markdown(
        "<h1 class='display' style='font-size:2.8rem; margin-top:14px;'>Proyectos de investigación</h1>"
        "<div class='tri' style='margin-bottom:6px;'></div>",
        unsafe_allow_html=True,
    )

    if df is not None and not df.empty:
        col_origen = "ORIGEN" if "ORIGEN" in df.columns else df.columns[-1]
        col_linea = buscar_columna(df, ("LINEA", "LÍNEA", "AREA", "ÁREA"))
        
        mask_ipeidi = contiene(df[col_origen], r"I-PEIDI")
        df_base = df[~mask_ipeidi]

        programas_disponibles = dict(PROGRAMAS_BASE)
        if st.session_state.get("f_prog") == "I-PEIDI":
            programas_disponibles["I-PEIDI"] = r"I-PEIDI"

        conteos = {p: int(contiene(df[col_origen], rx).sum()) for p, rx in programas_disponibles.items()}

        st.markdown("<p class='section-title'>Programa</p>", unsafe_allow_html=True)
        prog = st.pills(
            "Programa", options=list(programas_disponibles), selection_mode="single", key="f_prog",
            format_func=lambda p: f"{p}  :gray[{conteos[p]}]", label_visibility="collapsed",
        )

        st.markdown("<p class='section-title'>Línea prioritaria</p>", unsafe_allow_html=True)
        linea = st.pills(
            "Línea", options=list(LINEAS), selection_mode="single", key="f_linea",
            format_func=lambda l: f"{LINEAS[l][0]} {l}", label_visibility="collapsed",
        )

        st.write("")
        s1, s2 = st.columns([5, 1])
        texto = s1.text_input(
            "Buscar", key="f_texto", label_visibility="collapsed",
            placeholder="Buscar por título, investigador, palabra clave…",
        )
        s2.button("Limpiar filtros", on_click=reset_filtros, width="stretch")

        if prog == "I-PEIDI":
            df_f = df[mask_ipeidi]
        else:
            df_f = df_base
            if prog:
                df_f = df_f[contiene(df_f[col_origen], programas_disponibles[prog])]
        
        if linea:
            patron = LINEAS[linea][1]
            if col_linea:
                df_f = df_f[contiene(df_f[col_linea], patron) | contiene(texto_por_fila(df_f), patron)]
            else:
                df_f = df_f[contiene(texto_por_fila(df_f), patron)]
                
        if texto:
            df_f = df_f[contiene(sin_tildes_serie(texto_por_fila(df_f)), re.escape(sin_tildes(texto)))]

        st.write("")
        total_sin_ipeidi = len(df_base)

        k1, k2, k3, k4 = st.columns([1, 1, 1, 2])
        k1.markdown(stat(len(df_f), "en esta vista"), unsafe_allow_html=True)
        k2.markdown(stat(total_sin_ipeidi, "en total"), unsafe_allow_html=True)
        with k4:
            st.write("")
            st.write("")
            st.download_button(
                "Descargar CSV", df_f.to_csv(index=False).encode("utf-8-sig"),
                file_name="proyectos_unvm.csv", mime="text/csv", width="content",
            )

        st.write("")
        if df_f.empty:
            st.info("No hay proyectos con esos filtros. Probá limpiando alguno.")
        else:
            c_iap = buscar_columna(df_f, ("IAP",))
            c_inv = buscar_columna(df_f, ("INVESTIGADOR", "RESPONSABLE"))
            c_desc = buscar_columna(df_f, ("DESCRIPCION", "DESCRIPCIÓN", "RESUMEN", "TITULO", "TÍTULO"))
            c_area = buscar_columna(df_f, ("AREA ESTRATEGICA", "ÁREA ESTRATÉGICA", "LINEA", "LÍNEA", "AREA", "ÁREA"))
            c_anio = buscar_columna(df_f, ("AÑO", "ANIO", "PERIODO", "CONVOCATORIA"))
            c_orig = col_origen

            st.markdown(
                """
                <div style="font-weight: 600; font-size: 0.9rem; color: var(--muted); padding: 10px 14px; border-bottom: 2px solid var(--ink); display: grid; grid-template-columns: 1fr 2fr 3fr 1.5fr 0.8fr 1fr 1fr; gap: 10px; align-items: center;">
                    <div>IAP</div>
                    <div>Investigador</div>
                    <div>Descripción / Título</div>
                    <div>Área Estratégica</div>
                    <div>AÑO</div>
                    <div>Origen</div>
                    <div style="text-align: right;">Acción</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            for idx, row in df_f.iterrows():
                val_iap = str(row[c_iap]) if c_iap and pd.notna(row[c_iap]) else "-"
                val_inv = str(row[c_inv]) if c_inv and pd.notna(row[c_inv]) else "-"
                val_desc = str(row[c_desc]) if c_desc and pd.notna(row[c_desc]) else "-"
                val_area = str(row[c_area]) if c_area and pd.notna(row[c_area]) else "-"
                val_anio = str(row[c_anio]) if c_anio and pd.notna(row[c_anio]) else "-"
                val_orig = str(row[c_orig]) if c_orig and pd.notna(row[c_orig]) else "-"

                row_container = st.container()
                with row_container:
                    cols_fila = st.columns([1, 2, 3, 1.5, 0.8, 1, 1], vertical_alignment="center")
                    cols_fila[0].markdown(f"<span style='font-size: 0.85rem;'>{val_iap}</span>", unsafe_allow_html=True)
                    cols_fila[1].markdown(f"<span style='font-size: 0.85rem; font-weight: 500;'>{val_inv}</span>", unsafe_allow_html=True)
                    cols_fila[2].markdown(f"<span style='font-size: 0.85rem;'>{val_desc[:90]}...</span>" if len(val_desc) > 90 else f"<span style='font-size: 0.85rem;'>{val_desc}</span>", unsafe_allow_html=True)
                    cols_fila[3].markdown(f"<span style='font-size: 0.85rem;'>{val_area}</span>", unsafe_allow_html=True)
                    cols_fila[4].markdown(f"<span style='font-size: 0.85rem;'>{val_anio}</span>", unsafe_allow_html=True)
                    cols_fila[5].markdown(f"<span style='font-size: 0.85rem; font-weight: 600;'>{val_orig}</span>", unsafe_allow_html=True)
                    
                    with cols_fila[6]:
                        if st.button("Ver detalle +", key=f"btn_modal_{idx}", use_container_width=True):
                            mostrar_modal_detalle(row.to_dict())
                            
                    st.markdown("<div style='border-bottom: 1px solid var(--line); margin: 4px 0;'></div>", unsafe_allow_html=True)
    else:
        st.error("No se pudieron cargar los datos. Revisá la conexión o que la hoja de Google siga compartida.")

# ==========================================
# SERVICIOS, EQUIPAMIENTO Y VÍNCULOS
# ==========================================
elif st.session_state.page == "servicios":
    # Marca de agua fija e imperceptible en la esquina superior derecha también para esta vista
    logo_inv = logo_base64(Path(__file__).parent / "assets" / "INVEST.png")
    if logo_inv:
        st.markdown(
            f'<img src="data:image/png;base64,{logo_inv}" class="invest-watermark" alt="Investigación UNVM">',
            unsafe_allow_html=True
        )

    c_s1, c_s2 = st.columns([2, 5])
    if c_s1.button("← Inicio"):
        st.session_state.page = "inicio"
        st.rerun()
    if c_s2.button("📊 Ver Proyectos de Investigación"):
        st.session_state.page = "datos"
        st.rerun()

    st.markdown(
        "<h1 class='display' style='font-size:2.8rem; margin-top:14px;'>Servicios, Equipamiento y Vínculos</h1>"
        "<div class='tri' style='margin-bottom:6px;'></div>",
        unsafe_allow_html=True,
    )

    tab_servicios, tab_equipos, tab_vinculos = st.tabs([
        "🧪 Servicios Científicos Tecnológicos", 
        "🧰 Equipamiento Especializado", 
        "🤝 Vínculos Institucionales"
    ])

    with tab_servicios:
        st.write("")
        st.markdown("<p class='lead' style='font-size: 1.05rem;'>Catálogo de capacidades, asesoramientos y prestaciones científicas organizadas por laboratorio y área.</p>", unsafe_allow_html=True)
        
        for lab_nombre, areas in SERVICIOS_LABS.items():
            with st.expander(f"🔬 {lab_nombre}", expanded=False):
                for area_nombre, servicios in areas.items():
                    st.markdown(f"#### **{area_nombre}**")
                    for s in servicios:
                        st.markdown(f"- {s}")
                    st.write("")

    with tab_equipos:
        st.write("")
        st.markdown("<p class='lead' style='font-size: 1.05rem;'>Infraestructura, tecnología y simuladores de última generación disponibles en el IAPCH.</p>", unsafe_allow_html=True)
        
        for lab_eq_nombre, equipos in EQUIPAMIENTO_LABS.items():
            with st.expander(f"⚙️ {lab_eq_nombre}", expanded=True):
                grid_cols = st.columns(3)
                for idx_eq, eq in enumerate(equipos):
                    with grid_cols[idx_eq % 3]:
                        img_path = eq["foto"]
                        img_html = ""
                        
                        try:
                            full_path = Path(__file__).parent / img_path
                            if full_path.exists():
                                b64_data = logo_base64(full_path)
                                if b64_data:
                                    mime = "image/png" if full_path.suffix.lower() == ".png" else "image/jpeg"
                                    img_html = f'<img src="data:{mime};base64,{b64_data}" alt="{eq["nombre"]}">'
                                else:
                                    raise Exception()
                            else:
                                raise Exception()
                        except Exception:
                            img_html = '<div style="color: var(--muted); font-size: 0.85rem; font-weight: 500; text-align: center; padding: 40px 0;">📷 Imagen pendiente</div>'

                        st.markdown(
                            f"""
                            <div class="eq-card">
                                <div>
                                    <div class="eq-img-container">
                                        {img_html}
                                    </div>
                                    <p style="font-weight: 700; font-size: 0.95rem; color: var(--ink); margin-bottom: 6px; line-height: 1.3;">{eq['nombre']}</p>
                                    <p style="font-size: 0.83rem; color: var(--muted); margin: 0; line-height: 1.4;">{eq['desc']}</p>
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

    with tab_vinculos:
        st.write("")
        st.markdown("<p class='lead' style='font-size: 1.05rem;'>Red de cooperación interinstitucional, académica, gubernamental y social.</p>", unsafe_allow_html=True)
        
        for categoria, elementos in VINCULOS_INSTITUCIONALES.items():
            with st.expander(f"🌐 {categoria}", expanded=False):
                cols_v = st.columns(2)
                for i, elem in enumerate(elementos):
                    with cols_v[i % 2]:
                        st.markdown(f"• {elem}")
                st.write("")