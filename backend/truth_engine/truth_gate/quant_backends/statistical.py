import logging
import math
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class StatisticalBackend:
    """
    Handles numerical validation and anomaly detection.
    """
    
    def analyze_table(self, name: str, data: List[Dict[str, Any]]) -> List[str]:
        """
        Detects anomalies using Median Absolute Deviation (Robust Z-Score).
        Better for small sample sizes with extreme outliers.
        """
        if not data:
            return ["Empty Table"]
            
        anomalies = []
        try:
            keys = data[0].keys()
            for key in keys:
                # Extract numeric values
                values = []
                for row in data:
                    val = row.get(key)
                    # Simple heuristic to convert "1,000" or "100" to float
                    try:
                        f_val = float(str(val).replace(',', ''))
                        values.append(f_val)
                    except (ValueError, TypeError):
                        continue
                        
                if len(values) < 5:
                    continue # Too small for stats
                    
                median = self._calculate_median(values)
                # Calculate MAD (Median Absolute Deviation)
                deviations = [abs(x - median) for x in values]
                mad = self._calculate_median(deviations)
                
                if mad == 0:
                    continue # All values identical
                
                # Modified Z-Score: 0.6745 * (x - median) / MAD
                # Threshold of 3.5 is standard for "Potential Outlier"
                for i, val in enumerate(values):
                    mod_z = 0.6745 * abs(val - median) / mad
                    if mod_z > 3.5:
                        anomalies.append(f"Statistical Anomaly in '{name}' col '{key}' row {i}: Value {val} (Z={mod_z:.1f})")
                        
        except Exception as e:
            logger.error(f"Stat analysis failed for table {name}: {e}")
            
        return anomalies

    def _calculate_median(self, values: List[float]) -> float:
        sorted_v = sorted(values)
        n = len(sorted_v)
        if n == 0: return 0
        if n % 2 == 1:
            return sorted_v[n // 2]
        else:
            return (sorted_v[n // 2 - 1] + sorted_v[n // 2]) / 2.0
