"""Funciones auxiliares para el proyecto de valuación de futbolistas."""

import pandas as pd


def aplanar(cols):
    """Aplana el MultiIndex de columnas que devuelve FBref.

    Conserva el primer nivel cuando aporta información, para evitar
    nombres duplicados (por ejemplo 'Tkl' bajo 'Tackles' y bajo 'Challenges').

    Parameters
    ----------
    cols : pd.MultiIndex
        Columnas de un DataFrame leído de FBref.

    Returns
    -------
    list of str
    """
    out = []
    for c in cols:
        top, sub = str(c[0]), str(c[1])
        out.append(sub if top.startswith("Unnamed") else f"{top}_{sub}")
    return out


def quitar_encabezados_repetidos(df, col="Player"):
    """Elimina las filas de encabezado que FBref repite cada 25 registros."""
    return df[df[col] != col].copy()


def limpiar_nacion(df, col = "Nation"):
    """Limpia la columna de naciones, dejando solo el código de país."""
    df[col] = df[col].str.split(" ", n = 1).str[1]
    return df

def limpiar_competicion(serie):
    """Quita el prefijo de país de la columna Comp ('eng Premier League' -> 'Premier League')."""
    return serie.astype(str).str.replace(r"^[a-z]{2,3}\s+", "", regex=True).str.strip()

def limpiar_df(df):
    """Aplica todas las funciones de limpieza a un DataFrame."""
    df.columns = aplanar(df.columns)
    df = quitar_encabezados_repetidos(df)
    df = limpiar_nacion(df)
    df['Comp'] = limpiar_competicion(df['Comp'])
    df = df.drop(columns = 'Matches')
    return df
