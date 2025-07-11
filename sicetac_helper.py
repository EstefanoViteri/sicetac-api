import pandas as pd
from difflib import get_close_matches
import logging
from rapidfuzz import fuzz, process

logging.basicConfig(level=logging.INFO)

class SICETACHelper:
    def __init__(self, archivo_municipios):
        self.df_municipios = pd.read_excel(archivo_municipios)
        self.columnas_municipios = ['nombre_oficial', 'variacion_1', 'variacion_2', 'variacion_3']
        self.codigo_municipio_col = 'codigo_dane'
        self.nombre_municipio_col = 'nombre_oficial'
        self.nombre_departamento_col = 'departamento'

    def buscar_municipio(self, nombre_input):
        '''
        resultado = self._buscar_codigo(
            self.df_municipios,
            nombre_input,
            self.columnas_municipios,
            self.codigo_municipio_col,
            ['departamento', 'nombre_oficial']
        )
        '''
        resultado = self.buscar_codigo_dane(
            nombre_input,
            self.df_municipios,
            col_codigo=self.codigo_municipio_col,
            col_nombre=self.nombre_municipio_col,
            col_departamento=self.nombre_departamento_col,
            umbral=80
        )
        
        reporte = f"Nombre oficial: {resultado['nombre_oficial']}, Código DANE: {resultado['codigo_dane']}, Departamento: {resultado['departamento']}"
        if resultado['score'] >= 80:
            logging.info(f"✔ Municipio encontrado ✔ \n{reporte}")
        else:
            logging.warning(f"✘ Municipio NO encontrado ✘ Se toma a {reporte} para el cálculo, pero la coincidencia es baja (score: {resultado['score']})")
        return resultado

    def _buscar_codigo(self, df, nombre_input, columnas_nombres, codigo_col, extra_cols=None):
        nombre_input = str(nombre_input).strip().upper()
        for col in columnas_nombres:
            if col in df.columns:
                match = df[df[col].astype(str).str.upper().fillna('') == nombre_input]
                if not match.empty:
                    row = match.iloc[0]
                    result = {codigo_col: row[codigo_col]}
                    if extra_cols:
                        for c in extra_cols:
                            if c in row:
                                result[c] = row[c]
                    return result

        for col in columnas_nombres:
            if col in df.columns:
                opciones = df[col].dropna().astype(str).str.upper().unique().tolist()
                cercanos = get_close_matches(nombre_input, opciones, n=1, cutoff=0.8)
                if cercanos:
                    match = df[df[col].astype(str).str.upper() == cercanos[0]]
                    if not match.empty:
                        row = match.iloc[0]
                        result = {codigo_col: row[codigo_col]}
                        if extra_cols:
                            for c in extra_cols:
                                if c in row:
                                    result[c] = row[c]
                        result['coincidencia_aproximada'] = cercanos[0]
                        return result
        return None

    def buscar_codigo_dane(
        self,
        nombre_input: str,
        df: pd.DataFrame,
        col_codigo: str = "codigo_dane",
        col_nombre: str = "nombre_oficial",
        col_departamento: str = "departamento",
        umbral: int = 90
        ) -> dict:
        # 1. Encuentra la mejor coincidencia
        #TODO Revisar la funcion process.extractOne y el scorer
        mejor_nombre, score, idx = process.extractOne(nombre_input,df[col_nombre],scorer=fuzz.partial_ratio)
        fila = df.iloc[idx]
        codigo = fila[col_codigo]
        departamento = fila[col_departamento]

        resultado = {
            'nombre_oficial': mejor_nombre,
            'departamento': departamento,
            'codigo_dane': codigo,
            'score': score
        }
        return resultado
        
    def ruta_existe(self, origen_input, destino_input, df_rutas):
        cod_origen = self.buscar_municipio(origen_input)
        cod_destino = self.buscar_municipio(destino_input)
        if cod_origen and cod_destino:
            existe = df_rutas[
                (df_rutas['codigo_dane_origen'] == cod_origen['codigo_dane']) &
                (df_rutas['codigo_dane_destino'] == cod_destino['codigo_dane'])
            ]
            return not existe.empty
        return False
