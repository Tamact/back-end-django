import numpy as np
import pandas as pd
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class DataVisualizer:
    @staticmethod
    def prepare_similarity_data(df_results: pd.DataFrame) -> Dict[str, Any]:
        """
        Prépare les données de similarité pour la visualisation
        """
        try:
            # Nettoyage des données
            df = df_results.dropna(subset=['Similarité Cosinus', 'Nom du CV']).copy()
            df['Similarité Cosinus'] = pd.to_numeric(df['Similarité Cosinus'], errors='coerce')
            df = df.dropna(subset=['Similarité Cosinus'])

            return {
                "bar_chart": {
                    "x": df['Similarité Cosinus'].tolist(),
                    "y": df['Nom du CV'].tolist(),
                    "title": "Similarité des CVs par rapport à l'offre d'emploi"
                },
                "statistics": {
                    "mean": float(df['Similarité Cosinus'].mean()),
                    "median": float(df['Similarité Cosinus'].median()),
                    "std": float(df['Similarité Cosinus'].std()),
                    "min": float(df['Similarité Cosinus'].min()),
                    "max": float(df['Similarité Cosinus'].max())
                }
            }
        except Exception as e:
            logger.error(f"Erreur lors de la préparation des données de similarité : {e}")
            return {}

    @staticmethod
    def prepare_pie_chart_data(df_results: pd.DataFrame) -> Dict[str, Any]:
        """
        Prépare les données pour le diagramme circulaire
        """
        try:
            df = df_results.copy()
            df['Intervalle'] = pd.cut(
                df['Similarité Cosinus'],
                bins=[0, 0.4, 0.7, 1],
                labels=['0-0.4', '0.41-0.7', '0.71-1']
            )
            
            interval_counts = df['Intervalle'].value_counts()
            
            return {
                "labels": interval_counts.index.tolist(),
                "values": interval_counts.values.tolist(),
                "title": "Répartition des similarités des CVs"
            }
        except Exception as e:
            logger.error(f"Erreur lors de la préparation des données du diagramme circulaire : {e}")
            return {}

    @staticmethod
    def prepare_histogram_data(df_results: pd.DataFrame) -> Dict[str, Any]:
        """
        Prépare les données pour l'histogramme
        """
        try:
            hist, bins = np.histogram(df_results['Similarité Cosinus'], bins=10)
            return {
                "counts": hist.tolist(),
                "bins": bins.tolist(),
                "title": "Distribution des scores de similarité"
            }
        except Exception as e:
            logger.error(f"Erreur lors de la préparation des données de l'histogramme : {e}")
            return {}

    @staticmethod
    def prepare_cumulative_data(df_results: pd.DataFrame) -> Dict[str, Any]:
        """
        Prépare les données pour la similarité cumulative
        """
        try:
            df = df_results.sort_values(by='Similarité Cosinus', ascending=False).copy()
            cumulative = df['Similarité Cosinus'].cumsum()
            
            return {
                "x": list(range(len(cumulative))),
                "y": cumulative.tolist(),
                "title": "Similarité Cumulative des CVs"
            }
        except Exception as e:
            logger.error(f"Erreur lors de la préparation des données cumulatives : {e}")
            return {}

    @staticmethod
    def prepare_scatter_data(df_results: pd.DataFrame) -> Dict[str, Any]:
        """
        Prépare les données pour le nuage de points
        """
        try:
            return {
                "x": df_results['Nom du CV'].tolist(),
                "y": df_results['Similarité Cosinus'].tolist(),
                "title": "Similarité de chaque CV par rapport à l'offre"
            }
        except Exception as e:
            logger.error(f"Erreur lors de la préparation des données du nuage de points : {e}")
            return {}

    @staticmethod
    def prepare_boxplot_data(df_results: pd.DataFrame) -> Dict[str, Any]:
        """
        Prépare les données pour le box plot
        """
        try:
            q1 = float(df_results['Similarité Cosinus'].quantile(0.25))
            q3 = float(df_results['Similarité Cosinus'].quantile(0.75))
            median = float(df_results['Similarité Cosinus'].median())
            iqr = q3 - q1
            whisker_low = float(max(df_results['Similarité Cosinus'].min(), q1 - 1.5 * iqr))
            whisker_high = float(min(df_results['Similarité Cosinus'].max(), q3 + 1.5 * iqr))
            
            return {
                "q1": q1,
                "q3": q3,
                "median": median,
                "whisker_low": whisker_low,
                "whisker_high": whisker_high,
                "outliers": df_results['Similarité Cosinus'][
                    (df_results['Similarité Cosinus'] < whisker_low) | 
                    (df_results['Similarité Cosinus'] > whisker_high)
                ].tolist(),
                "title": "Répartition des scores de similarité entre les CVs"
            }
        except Exception as e:
            logger.error(f"Erreur lors de la préparation des données du box plot : {e}")
            return {}

    @staticmethod
    def prepare_competences_data(competences_data: Dict[str, List[float]]) -> Dict[str, Any]:
        """
        Prépare les données pour le graphique des compétences
        """
        try:
            return {
                "competences": list(competences_data.keys()),
                "scores": {
                    cv_name: [scores[i] for i in range(len(competences_data))]
                    for cv_name, scores in competences_data.items()
                },
                "title": "Similarité des CVs par Compétence"
            }
        except Exception as e:
            logger.error(f"Erreur lors de la préparation des données des compétences : {e}")
            return {}
